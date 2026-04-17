
import base64
import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from secrets import token_hex
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.crud.network import (
    create_reco_feedback,
    create_reco_impressions,
    get_bidirectional_blocked_user_pks,
    get_bidirectional_connected_user_pks,
    get_candidate_circle_names,
    get_circle_overlap_counts,
    get_connection_overlap_counts,
    get_feedback_counts_in_days,
    get_feedback_ext_rows_in_days,
    get_feedback_targets_in_days,
    get_global_feedback_counts_in_days,
    get_global_impression_counts_in_days,
    get_impression_counts_in_days,
    get_joined_circle_names,
    get_recent_impression_target_user_pks,
    get_shared_circle_names,
    get_shared_connection_names,
    get_user_circle_codes,
    list_candidate_users,
    list_filter_option_values,
    list_recent_feedback_target_profiles,
    map_business_user_ids_to_pks,
)
from app.crud.sys_config import get_sys_config_values
from app.models.user import User
from app.models.user_verification import UserVerification
from app.verification.constants import VerificationStatus, VerificationType

SUPPORTED_TABS = {"recommend", "nearby", "latest"}
SUPPORTED_EVENTS = {"click_card", "apply_friend", "chat_start", "dismiss", "block"}
POSITIVE_EVENTS = {"click_card", "apply_friend", "chat_start"}
DEFAULT_DOMAIN_TAGS = ["AI", "产品", "技术", "运营", "营销", "投资", "供应链", "企业服务"]
DEFAULT_INDUSTRY_OPTIONS = [
    "互联网 / AI",
    "电子 / 电器 / 通讯",
    "产品",
    "客服 / 运营",
    "销售",
    "人力 / 行政 / 法务",
    "财务 / 审计 / 税务",
    "市场 / 品牌 / 公关",
    "设计 / 传媒",
    "教育 / 培训",
    "医疗 / 健康",
    "金融",
    "制造 / 供应链",
    "建筑 / 房地产",
    "电商 / 零售",
    "物流 / 贸易",
    "咨询 / 专业服务",
    "能源 / 环保",
    "政府 / 公共服务",
    "其他",
]

DEFAULT_RECO_CONFIG: dict[str, float] = {
    "network.reco.impression_1d_hide_count": 5.0,
    "network.reco.pool.cold_impression_threshold": 24.0,
    "network.reco.pool.s_race_threshold": 0.17,
    "network.reco.pool.a_race_threshold": 0.10,
    "network.reco.penalty.dismiss_base_per_count": 0.20,
    "network.reco.penalty.dismiss_base_cap": 0.42,
    "network.reco.penalty.dismiss_repeat_per_count": 0.12,
    "network.reco.penalty.dismiss_repeat_cap": 0.24,
    "network.reco.penalty.dismiss_mismatch_per_count": 0.08,
    "network.reco.penalty.dismiss_mismatch_cap": 0.16,
    "network.reco.penalty.dismiss_not_local_per_count": 0.08,
    "network.reco.penalty.dismiss_not_local_cap": 0.16,
    "network.reco.penalty.exposure_per_count": 0.08,
    "network.reco.penalty.exposure_cap": 0.35,
    "network.reco.penalty.refresh_repeat": 0.25,
    "network.reco.boost.positive_per_count": 0.05,
    "network.reco.boost.positive_cap": 0.18,
}
RECO_CONFIG_CACHE_TTL_SECONDS = 30
_RECO_CONFIG_CACHE_TS: float = 0.0
_RECO_CONFIG_CACHE_VALUE: dict[str, float] = dict(DEFAULT_RECO_CONFIG)

FIRST_PAGE_RECENT_CACHE_TTL_SECONDS = 30 * 60
_FIRST_PAGE_RECENT_CACHE: dict[str, tuple[float, list[int]]] = {}
REQUEST_SCOPE_CACHE_TTL_SECONDS = 30 * 60
_REQUEST_SCOPE_REFRESH_CACHE: dict[str, tuple[float, list[int]]] = {}

POOL_PRIORITY = {"s": 5, "a": 4, "cold": 3, "b": 2, "downrank": 1}


@dataclass
class ViewerIntentProfile:
    industry_weights: dict[str, float]
    city_weights: dict[str, float]
    verified_interest: float
    is_cold_start: bool


@dataclass
class CandidateScore:
    user: User
    score: float
    reason_tags: list[str]
    reason_detail: dict[str, Any]
    is_same_city: bool
    last_active_ts: float
    active_text: str
    pool_tier: str
    is_explore: bool
    industry_key: str
    city_key: str


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))


def _to_float(value: str | None, default: float) -> float:
    try:
        return float(str(value).strip())
    except Exception:  # noqa: BLE001
        return float(default)


def _load_reco_config(db: Session) -> dict[str, float]:
    global _RECO_CONFIG_CACHE_TS, _RECO_CONFIG_CACHE_VALUE

    now_ts = datetime.now(UTC).timestamp()
    if now_ts - _RECO_CONFIG_CACHE_TS <= RECO_CONFIG_CACHE_TTL_SECONDS:
        return _RECO_CONFIG_CACHE_VALUE

    merged = dict(DEFAULT_RECO_CONFIG)
    try:
        raw_map = get_sys_config_values(db=db, config_keys=set(DEFAULT_RECO_CONFIG.keys()))
        for key, default in DEFAULT_RECO_CONFIG.items():
            merged[key] = _to_float(raw_map.get(key), default)
    except SQLAlchemyError:
        merged = dict(DEFAULT_RECO_CONFIG)

    _RECO_CONFIG_CACHE_VALUE = merged
    _RECO_CONFIG_CACHE_TS = now_ts
    return merged


def _encode_cursor(offset: int) -> str | None:
    if offset <= 0:
        return None
    payload = json.dumps({"offset": int(offset)}, ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8")


def _decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        payload = json.loads(decoded)
        return max(int(payload.get("offset", 0)), 0)
    except Exception:  # noqa: BLE001
        return 0


def _build_refresh_context_key(
    *,
    viewer_user_pk: int,
    tab: str,
    keyword: str | None,
    city_name: str | None,
    industry_label: str | None,
    domain: str | None,
) -> str:
    return "|".join(
        [
            str(int(viewer_user_pk)),
            str(tab or "").strip(),
            str(keyword or "").strip().lower(),
            str(city_name or "").strip(),
            str(industry_label or "").strip(),
            str(domain or "").strip(),
        ]
    )


def _clean_reason_text(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if "???" in text or "锟" in text:
        return ""
    if text.count("?") >= max(len(text) // 2, 2):
        return ""
    return text


def _parse_submit_payload(payload_json: str | None) -> dict[str, Any]:
    if not payload_json:
        return {}
    try:
        parsed = json.loads(payload_json)
    except Exception:  # noqa: BLE001
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _load_candidate_profile_lines(db: Session, candidate_user_pks: set[int]) -> dict[int, dict[str, str]]:
    if not candidate_user_pks:
        return {}

    candidate_map: dict[int, dict[str, str]] = {}

    for verify_type, company_key, title_key in (
        (VerificationType.ENTERPRISE.value, "company_name", "job_title"),
        (VerificationType.BUSINESS_CARD.value, "company_name", "card_title"),
    ):
        stmt = select(
            UserVerification.user_pk,
            UserVerification.submit_payload_json,
        ).where(
            UserVerification.user_pk.in_(candidate_user_pks),
            UserVerification.verify_type == verify_type,
            UserVerification.status == VerificationStatus.APPROVED.value,
        )
        for user_pk, payload_json in db.execute(stmt).all():
            normalized_user_pk = int(user_pk or 0)
            if not normalized_user_pk:
                continue

            payload = _parse_submit_payload(payload_json)
            company_name = _clean_reason_text(payload.get(company_key))
            job_title = _clean_reason_text(payload.get(title_key))
            if not company_name and not job_title:
                continue

            current = dict(candidate_map.get(normalized_user_pk, {}))
            if company_name and not current.get("company_name"):
                current["company_name"] = company_name
            if job_title and not current.get("job_title"):
                current["job_title"] = job_title
            candidate_map[normalized_user_pk] = current

    return candidate_map


def _active_score(user: User) -> tuple[float, str]:
    now = datetime.now(UTC).replace(tzinfo=None)
    reference = user.last_login_at or user.updated_at or user.created_at
    if not reference:
        return 0.25, "最近活跃"

    diff_hours = max((now - reference).total_seconds() / 3600, 0)
    if diff_hours <= 2:
        return 1.0, "活跃于 2 小时内"
    if diff_hours <= 24:
        return 0.88, "今天活跃"
    if diff_hours <= 72:
        return 0.70, "活跃于 3 天内"
    if diff_hours <= 24 * 7:
        return 0.48, "活跃于 7 天内"
    return 0.28, "最近活跃"


def _freshness_score(user: User) -> float:
    now = datetime.now(UTC).replace(tzinfo=None)
    created_at = user.created_at or user.updated_at
    if not created_at:
        return 0.2
    diff_days = max((now - created_at).total_seconds() / 86400, 0)
    if diff_days <= 3:
        return 1.0
    if diff_days <= 7:
        return 0.82
    if diff_days <= 14:
        return 0.62
    if diff_days <= 30:
        return 0.42
    return 0.18


def _quality_score(user: User) -> float:
    score = 0.0
    if bool(user.is_verified):
        score += 0.35
    if str(user.avatar_url or "").strip() and str(user.avatar_url or "").strip() != "/static/logo.png":
        score += 0.12
    if str(user.intro or "").strip():
        score += 0.16
    if str(user.industry_label or "").strip():
        score += 0.10
    if str(user.city_name or "").strip():
        score += 0.08
    if int(user.circle_count or 0) > 0:
        score += 0.10
    if int(user.network_count or 0) > 0:
        score += 0.09
    return _clamp_score(score)

def _content_match_score(viewer: User, candidate: User, keyword: str | None, domain: str | None) -> float:
    score = 0.0
    viewer_industry = str(viewer.industry_label or "").strip().lower()
    candidate_industry = str(candidate.industry_label or "").strip().lower()
    candidate_city = str(candidate.city_name or "").strip().lower()
    candidate_intro = str(candidate.intro or "").strip().lower()
    candidate_name = str(candidate.nickname or "").strip().lower()

    if viewer_industry and candidate_industry and viewer_industry == candidate_industry:
        score += 0.55

    normalized_keyword = str(keyword or "").strip().lower()
    if normalized_keyword and (
        normalized_keyword in candidate_name
        or normalized_keyword in candidate_industry
        or normalized_keyword in candidate_city
        or normalized_keyword in candidate_intro
    ):
        score += 0.25

    normalized_domain = str(domain or "").strip().lower()
    if normalized_domain and (normalized_domain in candidate_industry or normalized_domain in candidate_intro):
        score += 0.20

    return _clamp_score(score)


def _city_score(viewer: User, candidate: User, preferred_city_name: str | None) -> tuple[float, bool]:
    viewer_city = str(preferred_city_name or viewer.city_name or "").strip()
    candidate_city = str(candidate.city_name or "").strip()
    if viewer_city and candidate_city and viewer_city == candidate_city:
        return 1.0, True
    return 0.0, False


def _smoothed_rate(successes: int, impressions: int, *, prior_rate: float, prior_strength: float) -> float:
    safe_successes = max(int(successes or 0), 0)
    safe_impressions = max(int(impressions or 0), 0)
    return (safe_successes + (prior_rate * prior_strength)) / (safe_impressions + prior_strength)


def _build_viewer_intent_profile(recent_positive_rows: list[dict[str, Any]]) -> ViewerIntentProfile:
    industry_weights: dict[str, float] = {}
    city_weights: dict[str, float] = {}
    verified_interest = 0.0
    now = datetime.now(UTC).replace(tzinfo=None)
    event_weight_map = {"click_card": 1.0, "apply_friend": 1.5, "chat_start": 1.8}

    for row in recent_positive_rows:
        created_at = row.get("created_at")
        if not isinstance(created_at, datetime):
            continue
        age_hours = max((now - created_at.replace(tzinfo=None)).total_seconds() / 3600, 0)
        decay = math.exp(-age_hours / 72.0)
        weight = event_weight_map.get(str(row.get("event_type") or ""), 1.0) * decay

        industry_label = str(row.get("industry_label") or "").strip()
        city_name = str(row.get("city_name") or "").strip()
        if industry_label:
            industry_weights[industry_label] = float(industry_weights.get(industry_label, 0.0)) + weight
        if city_name:
            city_weights[city_name] = float(city_weights.get(city_name, 0.0)) + (weight * 0.8)
        if bool(row.get("is_verified")):
            verified_interest += weight

    return ViewerIntentProfile(
        industry_weights=industry_weights,
        city_weights=city_weights,
        verified_interest=verified_interest,
        is_cold_start=len(recent_positive_rows) < 3,
    )


def _weighted_lookup(score_map: dict[str, float], key: str | None) -> float:
    normalized_key = str(key or "").strip()
    if not normalized_key or not score_map:
        return 0.0
    peak = max(score_map.values()) if score_map else 0.0
    if peak <= 0:
        return 0.0
    return _clamp_score(float(score_map.get(normalized_key, 0.0)) / peak)


def _realtime_interest_score(*, candidate: User, intent_profile: ViewerIntentProfile) -> float:
    industry_score = _weighted_lookup(intent_profile.industry_weights, candidate.industry_label)
    city_score = _weighted_lookup(intent_profile.city_weights, candidate.city_name)
    verified_score = 1.0 if (intent_profile.verified_interest > 0 and bool(candidate.is_verified)) else 0.0
    return _clamp_score((0.55 * industry_score) + (0.25 * city_score) + (0.20 * verified_score))


def _time_slot_bonus(*, candidate_active_score: float, is_same_city: bool, candidate: User) -> float:
    hour = datetime.now(UTC).astimezone().hour
    bonus = 0.0

    if 11 <= hour <= 14 and candidate_active_score >= 0.85:
        bonus += 0.03
    if 19 <= hour <= 23 and candidate_active_score >= 0.70:
        bonus += 0.04
    if 7 <= hour <= 9 and is_same_city:
        bonus += 0.02
    if bool(candidate.is_verified) and candidate_active_score >= 0.85:
        bonus += 0.01

    return bonus


def _pool_boost(pool_tier: str) -> float:
    return {"s": 0.10, "a": 0.05, "cold": 0.02, "b": 0.0, "downrank": -0.12}.get(pool_tier, 0.0)


def _request_rotation_jitter(*, viewer_user_pk: int, candidate_user_pk: int, request_salt: str) -> float:
    digest = hashlib.sha1(f"{viewer_user_pk}:{candidate_user_pk}:{request_salt}".encode("utf-8")).hexdigest()
    raw_value = int(digest[:8], 16) / 0xFFFFFFFF
    return max(0.0, min(raw_value, 1.0))


def _assign_pool_tier(
    *,
    race_score: float,
    quality_score: float,
    freshness_score: float,
    global_impressions: int,
    global_negative_rate: float,
    reco_cfg: dict[str, float],
) -> tuple[str, bool]:
    cold_threshold = max(int(reco_cfg["network.reco.pool.cold_impression_threshold"]), 1)
    s_threshold = float(reco_cfg["network.reco.pool.s_race_threshold"])
    a_threshold = float(reco_cfg["network.reco.pool.a_race_threshold"])

    if global_impressions < cold_threshold:
        is_explore = freshness_score >= 0.60 or quality_score >= 0.65
        return "cold", bool(is_explore)
    if global_negative_rate >= 0.14:
        return "downrank", False
    if race_score >= s_threshold and quality_score >= 0.55:
        return "s", False
    if race_score >= a_threshold or quality_score >= 0.70:
        return "a", False
    is_explore = freshness_score >= 0.75 and quality_score >= 0.60
    return "b", bool(is_explore)


def _build_reason_info(
    *,
    overlap_circle_count: int,
    overlap_connection_count: int,
    shared_circle_names: list[str],
    shared_connection_names: list[str],
    is_same_city: bool,
    candidate: User,
    pool_tier: str,
    is_explore: bool,
) -> tuple[list[str], dict[str, Any]]:
    clean_shared_circle_names = [name for name in (_clean_reason_text(item) for item in shared_circle_names[:3]) if name]
    clean_shared_connection_names = [
        name for name in (_clean_reason_text(item) for item in shared_connection_names[:3]) if name
    ]
    clean_city_name = _clean_reason_text(candidate.city_name)
    clean_industry_label = _clean_reason_text(candidate.industry_label)

    detail: dict[str, Any] = {
        "is_same_city": bool(is_same_city),
        "shared_circle_count": int(overlap_circle_count),
        "shared_connection_count": int(overlap_connection_count),
        "shared_circle_names": clean_shared_circle_names,
        "shared_connection_names": clean_shared_connection_names,
        "shared_connection_source": "",
        "pool_tier": pool_tier,
        "is_explore": bool(is_explore),
    }

    if clean_shared_connection_names:
        if len(clean_shared_connection_names) == 1:
            detail["shared_connection_source"] = f"共同好友：{clean_shared_connection_names[0]}"
        else:
            detail["shared_connection_source"] = f"共同好友：{clean_shared_connection_names[0]} 等 {len(clean_shared_connection_names)} 人"

    tags: list[str] = []
    if clean_shared_connection_names:
        tags.append(f"共同好友·{clean_shared_connection_names[0]}")
    elif overlap_connection_count > 0:
        tags.append(f"共同好友 {overlap_connection_count} 人")

    if clean_shared_circle_names:
        tags.append(f"同圈·{clean_shared_circle_names[0]}")
    elif overlap_circle_count > 0:
        tags.append(f"同圈 {overlap_circle_count} 个")

    if is_same_city and clean_city_name:
        tags.append(f"同城·{clean_city_name}")

    if clean_industry_label:
        tags.append(clean_industry_label)

    if bool(candidate.is_verified):
        tags.append("已认证")

    if is_explore and clean_city_name and not is_same_city:
        tags.append(f"新候选·{clean_city_name}")

    deduped_tags: list[str] = []
    for tag in tags:
        normalized_tag = _clean_reason_text(tag)
        if normalized_tag and normalized_tag not in deduped_tags:
            deduped_tags.append(normalized_tag)

    return deduped_tags[:3], detail

def _sort_rows_for_tab(rows: list[CandidateScore], normalized_tab: str) -> list[CandidateScore]:
    if normalized_tab == "latest":
        return sorted(
            rows,
            key=lambda item: (item.last_active_ts, POOL_PRIORITY.get(item.pool_tier, 0), item.score),
            reverse=True,
        )
    if normalized_tab == "nearby":
        return sorted(
            rows,
            key=lambda item: (int(item.is_same_city), item.score, POOL_PRIORITY.get(item.pool_tier, 0), item.last_active_ts),
            reverse=True,
        )
    return sorted(
        rows,
        key=lambda item: (item.score, POOL_PRIORITY.get(item.pool_tier, 0), item.last_active_ts),
        reverse=True,
    )


def _apply_diversity_window(rows: list[CandidateScore], *, window_size: int) -> list[CandidateScore]:
    selected_ids: set[int] = set()
    industry_counter: Counter[str] = Counter()
    city_counter: Counter[str] = Counter()
    top_rows: list[CandidateScore] = []

    for row in rows:
        if len(top_rows) >= window_size:
            break
        industry_cap = 3 if window_size <= 20 else 4
        city_cap = 4 if window_size <= 20 else 5
        if row.industry_key and industry_counter[row.industry_key] >= industry_cap:
            continue
        if row.city_key and city_counter[row.city_key] >= city_cap:
            continue
        selected_ids.add(int(row.user.id))
        if row.industry_key:
            industry_counter[row.industry_key] += 1
        if row.city_key:
            city_counter[row.city_key] += 1
        top_rows.append(row)

    for row in rows:
        if len(top_rows) >= window_size:
            break
        if row.user.id in selected_ids:
            continue
        selected_ids.add(int(row.user.id))
        top_rows.append(row)

    remaining_rows = [row for row in rows if row.user.id not in selected_ids]
    return top_rows + remaining_rows


def _shuffle_recommend_rows(
    *,
    rows: list[CandidateScore],
    viewer_user_pk: int,
    request_salt: str,
    window_size: int,
    repeat_user_pks: set[int],
) -> list[CandidateScore]:
    def shuffle_key(row: CandidateScore) -> float:
        return _request_rotation_jitter(
            viewer_user_pk=int(viewer_user_pk),
            candidate_user_pk=int(row.user.id),
            request_salt=request_salt,
        )

    non_downrank_rows = [row for row in rows if row.pool_tier != "downrank"]
    downrank_rows = [row for row in rows if row.pool_tier == "downrank"]

    fresh_non_downrank_rows = [row for row in non_downrank_rows if int(row.user.id) not in repeat_user_pks]
    repeat_non_downrank_rows = [row for row in non_downrank_rows if int(row.user.id) in repeat_user_pks]

    if len(fresh_non_downrank_rows) >= window_size:
        head_rows = sorted(fresh_non_downrank_rows, key=shuffle_key, reverse=True)
        tail_rows = sorted(repeat_non_downrank_rows, key=shuffle_key, reverse=True)
    else:
        head_rows = sorted(non_downrank_rows, key=shuffle_key, reverse=True)
        tail_rows = []

    ordered_downrank_rows = sorted(downrank_rows, key=shuffle_key, reverse=True)
    return head_rows + tail_rows + ordered_downrank_rows


def _compose_ranked_rows(
    *,
    rows: list[CandidateScore],
    normalized_tab: str,
    safe_limit: int,
    is_cold_start: bool,
    first_page_repeat_user_pks: set[int] | None = None,
    viewer_user_pk: int | None = None,
    request_salt: str = "",
    shuffle_first_page: bool = False,
) -> list[CandidateScore]:
    base_sorted = _sort_rows_for_tab(rows, normalized_tab)
    if not base_sorted:
        return []

    window_size = min(max(safe_limit, 10), len(base_sorted))
    repeat_user_pks = {int(item) for item in (first_page_repeat_user_pks or set()) if item}
    if normalized_tab != "recommend":
        if repeat_user_pks:
            fresh_rows = [row for row in base_sorted if int(row.user.id) not in repeat_user_pks]
            repeat_rows = [row for row in base_sorted if int(row.user.id) in repeat_user_pks]
            if len(fresh_rows) >= window_size:
                return _apply_diversity_window(fresh_rows, window_size=window_size) + repeat_rows
        return _apply_diversity_window(base_sorted, window_size=window_size)

    if shuffle_first_page and viewer_user_pk:
        return _shuffle_recommend_rows(
            rows=base_sorted,
            viewer_user_pk=int(viewer_user_pk),
            request_salt=request_salt,
            window_size=window_size,
            repeat_user_pks=repeat_user_pks,
        )

    quotas = {
        "s": max(int(round(window_size * 0.45)), 1),
        "a": max(int(round(window_size * 0.20)), 1),
        "cold": max(int(round(window_size * (0.18 if is_cold_start else 0.12))), 1),
        "explore": max(int(round(window_size * (0.12 if is_cold_start else 0.08))), 1),
    }
    quotas["b"] = max(window_size - sum(quotas.values()), 0)

    groups: dict[str, list[CandidateScore]] = {
        "s": [row for row in base_sorted if row.pool_tier == "s"],
        "a": [row for row in base_sorted if row.pool_tier == "a"],
        "cold": [row for row in base_sorted if row.pool_tier == "cold"],
        "b": [row for row in base_sorted if row.pool_tier == "b"],
        "explore": [row for row in base_sorted if row.is_explore and row.pool_tier != "downrank"],
        "downrank": [row for row in base_sorted if row.pool_tier == "downrank"],
    }
    if repeat_user_pks:
        available_fresh_count = sum(
            1 for row in base_sorted if int(row.user.id) not in repeat_user_pks
        )
        if available_fresh_count >= window_size:
            groups = {
                group_name: [row for row in group_rows if int(row.user.id) not in repeat_user_pks]
                for group_name, group_rows in groups.items()
            }

    selected_ids: set[int] = set()
    industry_counter: Counter[str] = Counter()
    city_counter: Counter[str] = Counter()
    top_rows: list[CandidateScore] = []

    def can_accept(row: CandidateScore, *, strict: bool) -> bool:
        if row.user.id in selected_ids:
            return False
        if not strict:
            return True
        industry_cap = 3 if window_size <= 20 else 4
        city_cap = 4 if window_size <= 20 else 5
        if row.industry_key and industry_counter[row.industry_key] >= industry_cap:
            return False
        if row.city_key and city_counter[row.city_key] >= city_cap:
            return False
        return True

    def accept(row: CandidateScore) -> None:
        selected_ids.add(int(row.user.id))
        if row.industry_key:
            industry_counter[row.industry_key] += 1
        if row.city_key:
            city_counter[row.city_key] += 1
        top_rows.append(row)

    def take_from(source_rows: list[CandidateScore], quota: int, *, strict: bool) -> None:
        if quota <= 0:
            return
        for row in source_rows:
            if len(top_rows) >= window_size or quota <= 0:
                break
            if not can_accept(row, strict=strict):
                continue
            accept(row)
            quota -= 1

    for group_name in ("s", "a", "cold", "explore", "b"):
        take_from(groups[group_name], quotas.get(group_name, 0), strict=True)

    if len(top_rows) < window_size:
        for group_name in ("s", "a", "cold", "explore", "b", "downrank"):
            take_from(groups[group_name], window_size - len(top_rows), strict=False)
            if len(top_rows) >= window_size:
                break

    remaining_rows = [row for row in base_sorted if row.user.id not in selected_ids]
    if repeat_user_pks and len(top_rows) >= window_size:
        top_fresh_rows = [row for row in top_rows if int(row.user.id) not in repeat_user_pks]
        top_repeat_rows = [row for row in top_rows if int(row.user.id) in repeat_user_pks]
        if len(top_fresh_rows) >= window_size:
            top_rows = top_fresh_rows[:window_size]
            remaining_rows = top_repeat_rows + remaining_rows
    return top_rows + remaining_rows


def list_network_recommendations(
    db: Session,
    *,
    viewer: User,
    tab: str,
    request_id: str | None,
    cursor: str | None,
    limit: int,
    keyword: str | None,
    city_name: str | None,
    industry_label: str | None,
    domain: str | None,
    exclude_business_user_ids: list[str] | None = None,
) -> dict[str, Any]:
    normalized_tab = tab if tab in SUPPORTED_TABS else "recommend"
    safe_limit = min(max(int(limit or 20), 1), 50)
    offset = _decode_cursor(cursor)
    reco_cfg = _load_reco_config(db)
    stable_request_id = str(request_id or "").strip() or f"rec_{int(datetime.now(UTC).timestamp())}_{token_hex(4)}"
    request_salt = stable_request_id
    refresh_context_key = _build_refresh_context_key(
        viewer_user_pk=viewer.id,
        tab=normalized_tab,
        keyword=keyword,
        city_name=city_name,
        industry_label=industry_label,
        domain=domain,
    )

    blocked_set = get_bidirectional_blocked_user_pks(db=db, viewer_user_pk=viewer.id)
    connected_set = get_bidirectional_connected_user_pks(db=db, viewer_user_pk=viewer.id)
    feedback_block_set = get_feedback_targets_in_days(db=db, viewer_user_pk=viewer.id, days=90, event_types={"block"})
    negative_hide_set = get_feedback_targets_in_days(db=db, viewer_user_pk=viewer.id, days=30, event_types={"dismiss"})

    normalized_exclude_ids = {
        str(item or "").strip() for item in (exclude_business_user_ids or []) if str(item or "").strip()
    }
    refresh_excluded_user_pks: set[int] = set()
    request_scope_locked = False
    if normalized_exclude_ids:
        exclude_id_map = map_business_user_ids_to_pks(db=db, business_user_ids=normalized_exclude_ids)
        refresh_excluded_user_pks = {int(pk) for pk in exclude_id_map.values() if pk}

    if offset > 0:
        cached_request_scope = _REQUEST_SCOPE_REFRESH_CACHE.get(stable_request_id)
        if cached_request_scope:
            cached_ts, cached_user_pks = cached_request_scope
            if datetime.now(UTC).timestamp() - float(cached_ts) <= REQUEST_SCOPE_CACHE_TTL_SECONDS:
                refresh_excluded_user_pks.update(int(item) for item in (cached_user_pks or []) if item)
                request_scope_locked = True
            else:
                _REQUEST_SCOPE_REFRESH_CACHE.pop(stable_request_id, None)

    if offset <= 0:
        now_ts = datetime.now(UTC).timestamp()
        cached_value = _FIRST_PAGE_RECENT_CACHE.get(refresh_context_key)
        if cached_value:
            cached_ts, cached_user_pks = cached_value
            if now_ts - float(cached_ts) <= FIRST_PAGE_RECENT_CACHE_TTL_SECONDS:
                refresh_excluded_user_pks.update(int(item) for item in (cached_user_pks or []) if item)
            else:
                _FIRST_PAGE_RECENT_CACHE.pop(refresh_context_key, None)

        recent_impression_excluded = get_recent_impression_target_user_pks(
            db=db,
            viewer_user_pk=viewer.id,
            tab_key=normalized_tab,
            scene="discover",
            days=1,
            limit=max(min(safe_limit, 20), 10),
        )
        refresh_excluded_user_pks.update(recent_impression_excluded)
        _REQUEST_SCOPE_REFRESH_CACHE[stable_request_id] = (
            now_ts,
            [int(item) for item in refresh_excluded_user_pks if item],
        )
        request_scope_locked = True

    rank_with_request_scope = bool(offset <= 0 or request_scope_locked)

    soft_excluded_user_pks = {viewer.id, *blocked_set, *feedback_block_set}
    base_excluded_user_pks = {*soft_excluded_user_pks, *connected_set}
    strict_excluded_user_pks = {*base_excluded_user_pks, *negative_hide_set}

    if normalized_tab == "nearby":
        preferred_city = city_name
    else:
        preferred_city = city_name if city_name and city_name != "全国" else None

    raw_candidates = list_candidate_users(
        db=db,
        viewer_user_pk=viewer.id,
        limit_pool=600,
        keyword=keyword,
        city_name=preferred_city,
        industry_label=industry_label,
        domain=domain,
    )
    candidate_exclude_levels = [
        {*strict_excluded_user_pks, *refresh_excluded_user_pks},
        strict_excluded_user_pks,
        {*base_excluded_user_pks, *refresh_excluded_user_pks},
        base_excluded_user_pks,
        {*soft_excluded_user_pks, *refresh_excluded_user_pks},
        soft_excluded_user_pks,
    ]

    candidate_groups: list[list[User]] = []
    seen_candidate_ids: set[int] = set()
    for excluded_set in candidate_exclude_levels:
        current_group = [
            item
            for item in raw_candidates
            if item.id not in excluded_set and int(item.id) not in seen_candidate_ids
        ]
        if not current_group:
            continue
        candidate_groups.append(current_group)
        seen_candidate_ids.update(int(item.id) for item in current_group if item and item.id)

    candidate_ids = {int(item.id) for group in candidate_groups for item in group if item and item.id}
    if not candidate_ids:
        return {"request_id": stable_request_id, "items": [], "next_cursor": None, "has_more": False}

    viewer_circle_codes = get_user_circle_codes(db=db, user_pk=viewer.id)
    viewer_connected_ids = get_bidirectional_connected_user_pks(db=db, viewer_user_pk=viewer.id)
    candidate_circle_name_map = get_candidate_circle_names(db=db, candidate_user_pks=candidate_ids)
    overlap_circle_map = get_circle_overlap_counts(db=db, viewer_circle_codes=viewer_circle_codes, candidate_user_pks=candidate_ids)
    overlap_connection_map = get_connection_overlap_counts(db=db, viewer_connected_user_pks=viewer_connected_ids, candidate_user_pks=candidate_ids)
    shared_circle_name_map = get_shared_circle_names(db=db, viewer_circle_codes=viewer_circle_codes, candidate_user_pks=candidate_ids)
    shared_connection_name_map = get_shared_connection_names(
        db=db,
        viewer_connected_user_pks=viewer_connected_ids,
        candidate_user_pks=candidate_ids,
    )

    impression_7d_map = get_impression_counts_in_days(db=db, viewer_user_pk=viewer.id, candidate_user_pks=candidate_ids, days=7)
    impression_1d_map = get_impression_counts_in_days(db=db, viewer_user_pk=viewer.id, candidate_user_pks=candidate_ids, days=1)
    dismiss_30d_map = get_feedback_counts_in_days(
        db=db,
        viewer_user_pk=viewer.id,
        candidate_user_pks=candidate_ids,
        days=30,
        event_types={"dismiss"},
    )
    positive_30d_map = get_feedback_counts_in_days(
        db=db,
        viewer_user_pk=viewer.id,
        candidate_user_pks=candidate_ids,
        days=30,
        event_types=POSITIVE_EVENTS,
    )
    dismiss_reason_rows = get_feedback_ext_rows_in_days(
        db=db,
        viewer_user_pk=viewer.id,
        candidate_user_pks=candidate_ids,
        days=30,
        event_types={"dismiss"},
    )

    global_impression_14d_map = get_global_impression_counts_in_days(db=db, candidate_user_pks=candidate_ids, days=14)
    global_click_14d_map = get_global_feedback_counts_in_days(
        db=db,
        candidate_user_pks=candidate_ids,
        days=14,
        event_types={"click_card"},
    )
    global_apply_14d_map = get_global_feedback_counts_in_days(
        db=db,
        candidate_user_pks=candidate_ids,
        days=14,
        event_types={"apply_friend"},
    )
    global_chat_14d_map = get_global_feedback_counts_in_days(
        db=db,
        candidate_user_pks=candidate_ids,
        days=14,
        event_types={"chat_start"},
    )
    global_negative_14d_map = get_global_feedback_counts_in_days(
        db=db,
        candidate_user_pks=candidate_ids,
        days=14,
        event_types={"dismiss", "block"},
    )
    recent_positive_rows = list_recent_feedback_target_profiles(
        db=db,
        viewer_user_pk=viewer.id,
        days=30,
        event_types=POSITIVE_EVENTS,
        limit=80,
    )
    intent_profile = _build_viewer_intent_profile(recent_positive_rows)

    repeat_reason_map: dict[int, int] = {}
    mismatch_reason_map: dict[int, int] = {}
    not_local_reason_map: dict[int, int] = {}
    for target_user_pk, _, ext_json in dismiss_reason_rows:
        reason_code = ""
        try:
            payload = json.loads(ext_json) if ext_json else {}
            reason_code = str(payload.get("reason_code") or "").strip()
        except Exception:  # noqa: BLE001
            reason_code = ""
        if reason_code == "too_many_repeats":
            repeat_reason_map[target_user_pk] = int(repeat_reason_map.get(target_user_pk, 0)) + 1
        elif reason_code == "industry_mismatch":
            mismatch_reason_map[target_user_pk] = int(mismatch_reason_map.get(target_user_pk, 0)) + 1
        elif reason_code == "not_local":
            not_local_reason_map[target_user_pk] = int(not_local_reason_map.get(target_user_pk, 0)) + 1

    impression_hide_threshold = max(int(reco_cfg["network.reco.impression_1d_hide_count"]), 1)

    def _build_scored_rows(*, source_candidates: list[User], enforce_impression_hide: bool) -> list[CandidateScore]:
        rows: list[CandidateScore] = []
        for candidate in source_candidates:
            if enforce_impression_hide and impression_1d_map.get(candidate.id, 0) >= impression_hide_threshold:
                continue

            overlap_circle_count = int(overlap_circle_map.get(candidate.id, 0))
            overlap_connection_count = int(overlap_connection_map.get(candidate.id, 0))
            shared_circle_names = list(shared_circle_name_map.get(candidate.id, []))
            shared_connection_names = list(shared_connection_name_map.get(candidate.id, []))

            relation_score = _clamp_score((overlap_circle_count * 0.22) + (overlap_connection_count * 0.12))
            match_score = _content_match_score(viewer, candidate, keyword, domain)
            city_score, is_same_city = _city_score(viewer, candidate, city_name)
            profile_score = _clamp_score((0.68 * match_score) + (0.32 * city_score))
            quality_score = _quality_score(candidate)
            active_score, active_text = _active_score(candidate)
            freshness_score = _freshness_score(candidate)
            realtime_score = _realtime_interest_score(candidate=candidate, intent_profile=intent_profile)

            global_impressions = int(global_impression_14d_map.get(candidate.id, 0))
            global_clicks = int(global_click_14d_map.get(candidate.id, 0))
            global_applies = int(global_apply_14d_map.get(candidate.id, 0))
            global_chats = int(global_chat_14d_map.get(candidate.id, 0))
            global_negatives = int(global_negative_14d_map.get(candidate.id, 0))

            click_rate = _smoothed_rate(global_clicks, global_impressions, prior_rate=0.05, prior_strength=12)
            apply_rate = _smoothed_rate(global_applies, global_impressions, prior_rate=0.02, prior_strength=12)
            chat_rate = _smoothed_rate(global_chats, global_impressions, prior_rate=0.015, prior_strength=12)
            global_negative_rate = _smoothed_rate(global_negatives, global_impressions, prior_rate=0.025, prior_strength=12)
            race_score = _clamp_score(
                (0.24 * click_rate)
                + (0.36 * apply_rate)
                + (0.30 * chat_rate)
                + (0.10 * quality_score)
                - (0.20 * global_negative_rate)
            )

            pool_tier, is_explore = _assign_pool_tier(
                race_score=race_score,
                quality_score=quality_score,
                freshness_score=freshness_score,
                global_impressions=global_impressions,
                global_negative_rate=global_negative_rate,
                reco_cfg=reco_cfg,
            )

            dismiss_penalty = min(
                dismiss_30d_map.get(candidate.id, 0) * reco_cfg["network.reco.penalty.dismiss_base_per_count"],
                reco_cfg["network.reco.penalty.dismiss_base_cap"],
            )
            repeat_reason_penalty = min(
                repeat_reason_map.get(candidate.id, 0) * reco_cfg["network.reco.penalty.dismiss_repeat_per_count"],
                reco_cfg["network.reco.penalty.dismiss_repeat_cap"],
            )
            mismatch_reason_penalty = min(
                mismatch_reason_map.get(candidate.id, 0) * reco_cfg["network.reco.penalty.dismiss_mismatch_per_count"],
                reco_cfg["network.reco.penalty.dismiss_mismatch_cap"],
            )
            not_local_reason_penalty = min(
                not_local_reason_map.get(candidate.id, 0) * reco_cfg["network.reco.penalty.dismiss_not_local_per_count"],
                reco_cfg["network.reco.penalty.dismiss_not_local_cap"],
            )
            exposure_penalty = min(
                impression_7d_map.get(candidate.id, 0) * reco_cfg["network.reco.penalty.exposure_per_count"],
                reco_cfg["network.reco.penalty.exposure_cap"],
            )
            positive_boost = min(
                positive_30d_map.get(candidate.id, 0) * reco_cfg["network.reco.boost.positive_per_count"],
                reco_cfg["network.reco.boost.positive_cap"],
            )
            refresh_repeat_penalty = float(reco_cfg["network.reco.penalty.refresh_repeat"]) if (rank_with_request_scope and candidate.id in refresh_excluded_user_pks) else 0.0
            time_bonus = _time_slot_bonus(candidate_active_score=active_score, is_same_city=is_same_city, candidate=candidate)
            explore_bonus = 0.03 if is_explore else 0.0
            request_jitter_bonus = 0.0
            if rank_with_request_scope and candidate.id not in refresh_excluded_user_pks:
                request_jitter_bonus = 0.06 * _request_rotation_jitter(
                    viewer_user_pk=int(viewer.id),
                    candidate_user_pk=int(candidate.id),
                    request_salt=request_salt,
                )

            if intent_profile.is_cold_start:
                base_score = (
                    (0.22 * relation_score)
                    + (0.18 * profile_score)
                    + (0.08 * realtime_score)
                    + (0.18 * quality_score)
                    + (0.14 * active_score)
                    + (0.09 * freshness_score)
                    + (0.08 * race_score)
                    + _pool_boost(pool_tier)
                    + time_bonus
                    + explore_bonus
                    + request_jitter_bonus
                    + positive_boost
                    - dismiss_penalty
                    - repeat_reason_penalty
                    - mismatch_reason_penalty
                    - (not_local_reason_penalty if not is_same_city else 0.0)
                    - exposure_penalty
                    - refresh_repeat_penalty
                )
            else:
                base_score = (
                    (0.24 * relation_score)
                    + (0.20 * profile_score)
                    + (0.16 * realtime_score)
                    + (0.12 * quality_score)
                    + (0.10 * active_score)
                    + (0.08 * freshness_score)
                    + (0.10 * race_score)
                    + _pool_boost(pool_tier)
                    + time_bonus
                    + explore_bonus
                    + request_jitter_bonus
                    + positive_boost
                    - dismiss_penalty
                    - repeat_reason_penalty
                    - mismatch_reason_penalty
                    - (not_local_reason_penalty if not is_same_city else 0.0)
                    - exposure_penalty
                    - refresh_repeat_penalty
                )

            if normalized_tab == "nearby":
                base_score += 0.12 * city_score
            elif normalized_tab == "latest":
                base_score += 0.08 * active_score + 0.06 * freshness_score

            final_score = _clamp_score(base_score)
            reason_tags, reason_detail = _build_reason_info(
                overlap_circle_count=overlap_circle_count,
                overlap_connection_count=overlap_connection_count,
                shared_circle_names=shared_circle_names,
                shared_connection_names=shared_connection_names,
                is_same_city=is_same_city,
                candidate=candidate,
                pool_tier=pool_tier,
                is_explore=is_explore,
            )
            reason_detail.update(
                {
                    "relation_score": round(relation_score, 4),
                    "profile_score": round(profile_score, 4),
                    "realtime_score": round(realtime_score, 4),
                    "quality_score": round(quality_score, 4),
                    "active_score": round(active_score, 4),
                    "freshness_score": round(freshness_score, 4),
                    "race_score": round(race_score, 4),
                    "global_impressions_14d": global_impressions,
                    "viewer_impressions_7d": int(impression_7d_map.get(candidate.id, 0)),
                }
            )
            last_active_ts = float((candidate.last_login_at or candidate.updated_at or candidate.created_at).timestamp())
            rows.append(
                CandidateScore(
                    user=candidate,
                    score=final_score,
                    reason_tags=reason_tags,
                    reason_detail=reason_detail,
                    is_same_city=is_same_city,
                    last_active_ts=last_active_ts,
                    active_text=active_text,
                    pool_tier=pool_tier,
                    is_explore=is_explore,
                    industry_key=str(candidate.industry_label or "").strip(),
                    city_key=str(candidate.city_name or "").strip(),
                )
            )
        return rows

    ordered_rows: list[CandidateScore] = []
    for group_index, candidate_group in enumerate(candidate_groups):
        scored_rows = _build_scored_rows(
            source_candidates=candidate_group,
            enforce_impression_hide=True,
        )
        if not scored_rows:
            scored_rows = _build_scored_rows(
                source_candidates=candidate_group,
                enforce_impression_hide=False,
            )
        if not scored_rows:
            continue

        ordered_rows.extend(
            _compose_ranked_rows(
                rows=scored_rows,
                normalized_tab=normalized_tab,
                safe_limit=safe_limit,
                is_cold_start=intent_profile.is_cold_start,
                first_page_repeat_user_pks=refresh_excluded_user_pks if (rank_with_request_scope and group_index == 0) else set(),
                viewer_user_pk=int(viewer.id),
                request_salt=request_salt,
                shuffle_first_page=bool(rank_with_request_scope and normalized_tab == "recommend" and group_index == 0),
            )
        )

    total = len(ordered_rows)
    page_rows = ordered_rows[offset : offset + safe_limit]
    next_offset = offset + len(page_rows)
    has_more = next_offset < total
    candidate_user_pks = {int(row.user.id) for row in page_rows if row.user and row.user.id}
    candidate_profile_map = _load_candidate_profile_lines(db=db, candidate_user_pks=candidate_user_pks)

    if offset <= 0 and page_rows:
        _FIRST_PAGE_RECENT_CACHE[refresh_context_key] = (
            datetime.now(UTC).timestamp(),
            [int(row.user.id) for row in page_rows if row.user and row.user.id],
        )

    items: list[dict[str, Any]] = []
    for row in page_rows:
        safe_reason_tags = [tag for tag in (_clean_reason_text(item) for item in row.reason_tags) if tag][:3]
        safe_reason_detail = dict(row.reason_detail or {})
        safe_reason_detail["shared_circle_names"] = [
            name
            for name in (_clean_reason_text(item) for item in (safe_reason_detail.get("shared_circle_names") or []))
            if name
        ][:3]
        safe_reason_detail["circle_names"] = [
            name
            for name in (
                _clean_reason_text(item)
                for item in candidate_circle_name_map.get(int(row.user.id), [])
            )
            if name
        ][:3]
        safe_reason_detail["shared_connection_names"] = [
            name
            for name in (_clean_reason_text(item) for item in (safe_reason_detail.get("shared_connection_names") or []))
            if name
        ][:3]
        safe_reason_detail["shared_connection_source"] = _clean_reason_text(safe_reason_detail.get("shared_connection_source"))

        items.append(
            {
                "user_id": row.user.user_id,
                "nickname": row.user.nickname,
                "avatar_url": row.user.avatar_url,
                "intro": str(row.user.intro or "").strip(),
                "industry_label": row.user.industry_label,
                "city_name": row.user.city_name,
                "company_name": str(row.user.company_name or candidate_profile_map.get(int(row.user.id), {}).get("company_name", "")).strip(),
                "job_title": str(row.user.job_title or candidate_profile_map.get(int(row.user.id), {}).get("job_title", "")).strip(),
                "circle_names": list(safe_reason_detail["circle_names"]),
                "is_verified": bool(row.user.is_verified),
                "active_text": row.active_text,
                "reason_tags": safe_reason_tags,
                "reason_detail": safe_reason_detail,
                "score": round(row.score, 4),
            }
        )

    return {
        "request_id": stable_request_id,
        "items": items,
        "next_cursor": _encode_cursor(next_offset) if has_more else None,
        "has_more": has_more,
    }


def list_network_filter_options(db: Session) -> dict[str, list[str]]:
    dynamic_options = list_filter_option_values(db=db, limit=20)
    return {
        "cities": dynamic_options.get("cities", []),
        "industries": DEFAULT_INDUSTRY_OPTIONS,
        "domains": DEFAULT_DOMAIN_TAGS,
    }


def save_network_impressions(
    db: Session,
    *,
    viewer: User,
    target_business_user_ids: list[str],
    scene: str,
    tab: str,
    request_id: str | None,
) -> int:
    normalized_scene = scene if scene == "discover" else "discover"
    normalized_tab = tab if tab in SUPPORTED_TABS else "recommend"
    normalized_ids = {str(item or "").strip() for item in target_business_user_ids if str(item or "").strip()}
    if not normalized_ids:
        return 0

    business_to_pk = map_business_user_ids_to_pks(db=db, business_user_ids=normalized_ids)
    target_pks = {pk for _, pk in business_to_pk.items() if pk and pk != viewer.id}
    if not target_pks:
        return 0

    return create_reco_impressions(
        db=db,
        viewer_user_pk=viewer.id,
        target_user_pks=target_pks,
        scene=normalized_scene,
        tab_key=normalized_tab,
        request_id=request_id,
    )


def save_network_feedback(
    db: Session,
    *,
    viewer: User,
    target_business_user_id: str,
    scene: str,
    tab: str,
    request_id: str | None,
    event_type: str,
    ext: dict | None,
) -> bool:
    normalized_event_type = event_type if event_type in SUPPORTED_EVENTS else ""
    if not normalized_event_type:
        return False

    normalized_target_id = str(target_business_user_id or "").strip()
    mapping = map_business_user_ids_to_pks(db=db, business_user_ids={normalized_target_id})
    target_pk = mapping.get(normalized_target_id)
    if not target_pk or target_pk == viewer.id:
        return False

    normalized_scene = scene if scene == "discover" else "discover"
    normalized_tab = tab if tab in SUPPORTED_TABS else "recommend"
    ext_json = json.dumps(ext or {}, ensure_ascii=False) if ext else None

    create_reco_feedback(
        db=db,
        viewer_user_pk=viewer.id,
        target_user_pk=int(target_pk),
        scene=normalized_scene,
        tab_key=normalized_tab,
        request_id=request_id,
        event_type=normalized_event_type,
        ext_json=ext_json,
    )
    return True
