from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from secrets import token_hex

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.exceptions import BusinessException
from app.crud import get_sys_config_values
from app.models.sys_config import SysConfig
from app.models.user_contact_package_balance import UserContactPackageBalance

CONTACT_PACKAGE_PRODUCT_TYPE = "contact_package"
CONTACT_PACKAGE_CONFIG_GROUP = "payment"
CONTACT_PACKAGE_DISPLAY_CONFIG_KEY = "contact.package.display_enabled"
CONTACT_PACKAGE_PLANS_CONFIG_KEY = "contact.package.plans_json"
CONTACT_PACKAGE_PLAN_ID_PREFIX = "contact_package_"
LEGACY_CONTACT_PACKAGE_PLAN_ID_PREFIX = "contact_pack_"

DEFAULT_CONTACT_PACKAGE_PLANS = [
    {
        "id": "contact_pack_a",
        "name": "人群包A",
        "price": Decimal("15.00"),
        "view_count": 30,
        "enabled": True,
    },
    {
        "id": "contact_pack_b",
        "name": "人群包B",
        "price": Decimal("36.00"),
        "view_count": 80,
        "enabled": True,
    },
]


def _utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _normalize_text(value: object) -> str:
    return str(value or "").strip()


def _to_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return int(value) == 1
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on", "active"}:
            return True
        if normalized in {"0", "false", "no", "off", "inactive"}:
            return False
    return default


def _to_int(value: object, default: int, *, min_value: int = 0, max_value: int = 100000) -> int:
    try:
        parsed = int(str(value))
    except Exception:  # noqa: BLE001
        return default
    if parsed < min_value:
        return min_value
    if parsed > max_value:
        return max_value
    return parsed


def _to_decimal(value: object, default: Decimal) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except Exception:  # noqa: BLE001
        return default
    if parsed < 0:
        return default
    return parsed.quantize(Decimal("0.01"))


def _json_dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _legacy_contact_package_key(plan_id: str, field: str) -> str:
    return f"contact.package.{plan_id}.{field}"


def _sanitize_plan_id(raw_value: object) -> str:
    normalized = _normalize_text(raw_value).lower()
    if not normalized:
        return ""
    return re.sub(r"[^a-z0-9_-]+", "_", normalized).strip("_")


def _is_contact_package_storage_ready(db: Session) -> bool:
    try:
        db.execute(select(UserContactPackageBalance.user_pk).limit(1)).first()
        return True
    except SQLAlchemyError:
        return False


def is_contact_package_plan_id(plan_id: str) -> bool:
    normalized_plan_id = _sanitize_plan_id(plan_id)
    if not normalized_plan_id:
        return False
    return normalized_plan_id.startswith(CONTACT_PACKAGE_PLAN_ID_PREFIX) or normalized_plan_id.startswith(
        LEGACY_CONTACT_PACKAGE_PLAN_ID_PREFIX
    )


def _normalize_plan_id(raw_value: object, seen_ids: set[str]) -> str:
    candidate = _sanitize_plan_id(raw_value)
    if not is_contact_package_plan_id(candidate):
        candidate = ""
    if not candidate:
        candidate = f"{CONTACT_PACKAGE_PLAN_ID_PREFIX}{token_hex(4)}"
    while candidate in seen_ids:
        candidate = f"{CONTACT_PACKAGE_PLAN_ID_PREFIX}{token_hex(4)}"
    seen_ids.add(candidate)
    return candidate


def _build_default_admin_plans() -> list[dict]:
    return [
        {
            "id": str(item["id"]),
            "name": str(item["name"]),
            "price": float(item["price"]),
            "view_count": int(item["view_count"]),
            "enabled": bool(item.get("enabled", True)),
        }
        for item in DEFAULT_CONTACT_PACKAGE_PLANS
    ]


def _load_contact_package_config_values(db: Session) -> dict[str, str]:
    return get_sys_config_values(
        db=db,
        config_keys={CONTACT_PACKAGE_DISPLAY_CONFIG_KEY, CONTACT_PACKAGE_PLANS_CONFIG_KEY},
    )


def _load_legacy_contact_package_config_values(db: Session) -> dict[str, str]:
    config_keys: set[str] = {CONTACT_PACKAGE_DISPLAY_CONFIG_KEY}
    for plan in DEFAULT_CONTACT_PACKAGE_PLANS:
        plan_id = str(plan["id"])
        for field in ("enabled", "name", "price", "view_count"):
            config_keys.add(_legacy_contact_package_key(plan_id, field))
    return get_sys_config_values(db=db, config_keys=config_keys)


def _build_legacy_admin_plans(config_values: dict[str, str]) -> list[dict]:
    plans: list[dict] = []
    for default in DEFAULT_CONTACT_PACKAGE_PLANS:
        plan_id = str(default["id"])
        plans.append(
            {
                "id": plan_id,
                "name": _normalize_text(config_values.get(_legacy_contact_package_key(plan_id, "name")))
                or str(default["name"]),
                "price": float(
                    _to_decimal(
                        config_values.get(_legacy_contact_package_key(plan_id, "price")),
                        default["price"],
                    )
                ),
                "view_count": _to_int(
                    config_values.get(_legacy_contact_package_key(plan_id, "view_count")),
                    int(default["view_count"]),
                    min_value=1,
                    max_value=100000,
                ),
                "enabled": _to_bool(
                    config_values.get(_legacy_contact_package_key(plan_id, "enabled")),
                    bool(default.get("enabled", True)),
                ),
            }
        )
    return plans


def _parse_contact_package_plans_json(raw_value: str | None) -> list[dict] | None:
    text = _normalize_text(raw_value)
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, list):
        return None

    plans: list[dict] = []
    seen_ids: set[str] = set()
    for item in parsed:
        if not isinstance(item, dict):
            continue
        name = _normalize_text(item.get("name"))
        price = _to_decimal(item.get("price"), Decimal("0.00"))
        view_count = _to_int(item.get("view_count"), 0, min_value=1, max_value=100000)
        if not name or price <= 0 or view_count <= 0:
            continue
        plans.append(
            {
                "id": _normalize_plan_id(item.get("id"), seen_ids),
                "name": name,
                "price": float(price),
                "view_count": view_count,
                "enabled": _to_bool(item.get("enabled"), True),
            }
        )
    return plans


def _validate_admin_plans(plans: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    seen_ids: set[str] = set()

    for index, item in enumerate(plans, start=1):
        if not isinstance(item, dict):
            raise BusinessException(
                message=f"第 {index} 个人群包配置格式不正确",
                code=4554,
                status_code=400,
            )

        name = _normalize_text(item.get("name"))
        if not name:
            raise BusinessException(
                message=f"第 {index} 个人群包名称不能为空",
                code=4555,
                status_code=400,
            )

        price = _to_decimal(item.get("price"), Decimal("0.00"))
        if price <= 0:
            raise BusinessException(
                message=f"第 {index} 个人群包金额必须大于 0",
                code=4556,
                status_code=400,
            )

        view_count = _to_int(item.get("view_count"), 0, min_value=1, max_value=100000)
        if view_count <= 0:
            raise BusinessException(
                message=f"第 {index} 个人群包查看次数必须大于 0",
                code=4557,
                status_code=400,
            )

        normalized.append(
            {
                "id": _normalize_plan_id(item.get("id"), seen_ids),
                "name": name,
                "price": float(price),
                "view_count": view_count,
                "enabled": _to_bool(item.get("enabled"), True),
            }
        )

    return normalized


def _upsert_sys_config_row(
    db: Session,
    *,
    config_key: str,
    config_value: str,
    description: str,
) -> None:
    row = db.execute(select(SysConfig).where(SysConfig.config_key == config_key).limit(1)).scalar_one_or_none()
    if row is None:
        row = SysConfig(
            config_key=config_key,
            config_value=config_value,
            config_group=CONTACT_PACKAGE_CONFIG_GROUP,
            description=description,
        )
    else:
        row.config_value = config_value
        row.config_group = CONTACT_PACKAGE_CONFIG_GROUP
        row.description = description
    db.add(row)


def ensure_default_contact_package_configs() -> None:
    with SessionLocal() as db:
        legacy_values = _load_legacy_contact_package_config_values(db=db)
        current_values = _load_contact_package_config_values(db=db)
        default_plans = _build_legacy_admin_plans(legacy_values) or _build_default_admin_plans()

        changed = False
        if CONTACT_PACKAGE_DISPLAY_CONFIG_KEY not in current_values:
            _upsert_sys_config_row(
                db=db,
                config_key=CONTACT_PACKAGE_DISPLAY_CONFIG_KEY,
                config_value="1",
                description="Contact package display switch",
            )
            changed = True

        if CONTACT_PACKAGE_PLANS_CONFIG_KEY not in current_values:
            _upsert_sys_config_row(
                db=db,
                config_key=CONTACT_PACKAGE_PLANS_CONFIG_KEY,
                config_value=_json_dumps(default_plans),
                description="Contact package plans json",
            )
            changed = True

        if changed:
            db.commit()


def get_admin_contact_package_config(db: Session) -> dict:
    config_values = _load_contact_package_config_values(db=db)
    display_enabled = _to_bool(config_values.get(CONTACT_PACKAGE_DISPLAY_CONFIG_KEY), True)
    parsed_plans = _parse_contact_package_plans_json(config_values.get(CONTACT_PACKAGE_PLANS_CONFIG_KEY))
    if parsed_plans is None:
        plans = _build_legacy_admin_plans(_load_legacy_contact_package_config_values(db=db))
    else:
        plans = parsed_plans
    return {
        "display_enabled": display_enabled,
        "plans": plans,
    }


def save_admin_contact_package_config(
    db: Session,
    *,
    display_enabled: bool,
    plans: list[dict],
) -> dict:
    normalized_plans = _validate_admin_plans(plans)

    _upsert_sys_config_row(
        db=db,
        config_key=CONTACT_PACKAGE_DISPLAY_CONFIG_KEY,
        config_value="1" if display_enabled else "0",
        description="Contact package display switch",
    )
    _upsert_sys_config_row(
        db=db,
        config_key=CONTACT_PACKAGE_PLANS_CONFIG_KEY,
        config_value=_json_dumps(normalized_plans),
        description="Contact package plans json",
    )
    db.commit()

    return {
        "display_enabled": bool(display_enabled),
        "plans": normalized_plans,
    }


def _build_runtime_plans(admin_plans: list[dict]) -> list[dict]:
    enabled_ids = [str(item["id"]) for item in admin_plans if bool(item.get("enabled"))]
    recommended_id = enabled_ids[0] if enabled_ids else ""

    runtime_plans: list[dict] = []
    for index, plan in enumerate(admin_plans, start=1):
        name = _normalize_text(plan.get("name"))
        price = _to_decimal(plan.get("price"), Decimal("0.00"))
        view_count = _to_int(plan.get("view_count"), 0, min_value=1, max_value=100000)
        if not name or price <= 0 or view_count <= 0:
            continue

        is_recommended = str(plan["id"]) == recommended_id
        runtime_plans.append(
            {
                "id": str(plan["id"]),
                "name": name,
                "subtitle": f"{view_count}次查看别人联系方式机会",
                "price": price,
                "original_price": Decimal("0.00"),
                "view_count": view_count,
                "recommended": is_recommended,
                "badge_text": "推荐" if is_recommended else "",
                "sort": index,
                "enabled": bool(plan.get("enabled")),
            }
        )

    return runtime_plans


def _resolve_contact_package_config(db: Session, *, include_disabled: bool = False) -> dict:
    admin_config = get_admin_contact_package_config(db=db)
    display_enabled = bool(admin_config["display_enabled"])
    plans = _build_runtime_plans(admin_config["plans"])

    if include_disabled:
        return {
            "display_enabled": display_enabled,
            "plans": plans,
        }

    if not display_enabled:
        return {
            "display_enabled": False,
            "plans": [],
        }

    return {
        "display_enabled": True,
        "plans": [item for item in plans if bool(item["enabled"])],
    }


def resolve_contact_package_plans(db: Session) -> list[dict]:
    return _resolve_contact_package_config(db=db, include_disabled=False)["plans"]


def resolve_contact_package_overview(db: Session) -> dict:
    return _resolve_contact_package_config(db=db, include_disabled=False)


def get_contact_package_plan(db: Session, *, plan_id: str, include_disabled: bool = False) -> dict | None:
    normalized_plan_id = _sanitize_plan_id(plan_id)
    if not normalized_plan_id:
        return None

    config = _resolve_contact_package_config(db=db, include_disabled=include_disabled)
    for plan in config["plans"]:
        if _sanitize_plan_id(plan.get("id")) == normalized_plan_id:
            return plan
    return None


def serialize_contact_package_plan(plan: dict) -> dict:
    return {
        "id": str(plan["id"]),
        "name": str(plan["name"]),
        "subtitle": str(plan["subtitle"]),
        "price": float(plan["price"]),
        "original_price": float(plan["original_price"]),
        "recommended": bool(plan["recommended"]),
        "badge_text": str(plan["badge_text"]),
        "view_count": int(plan["view_count"]),
        "product_type": CONTACT_PACKAGE_PRODUCT_TYPE,
    }


def _get_contact_package_balance(db: Session, *, user_pk: int) -> UserContactPackageBalance | None:
    stmt = select(UserContactPackageBalance).where(UserContactPackageBalance.user_pk == int(user_pk))
    try:
        return db.execute(stmt).scalar_one_or_none()
    except SQLAlchemyError:
        return None


def resolve_contact_package_snapshot(db: Session, *, user_pk: int) -> dict:
    balance = _get_contact_package_balance(db=db, user_pk=user_pk)
    remaining_views = max(int(balance.remaining_views or 0), 0) if balance is not None else 0
    used_views = max(int(balance.used_views or 0), 0) if balance is not None else 0
    purchased_views = max(int(balance.purchased_views or 0), 0) if balance is not None else 0
    return {
        "remaining_views": remaining_views,
        "used_views": used_views,
        "purchased_views": purchased_views,
        "has_remaining_views": remaining_views > 0,
        "last_order_no": _normalize_text(balance.last_order_no) if balance is not None else "",
    }


def grant_contact_package_views(
    db: Session,
    *,
    user_pk: int,
    order_no: str,
    view_count: int,
) -> dict:
    safe_view_count = max(int(view_count or 0), 0)
    if safe_view_count <= 0:
        raise BusinessException(message="人群包可用次数配置无效", code=4551, status_code=400)
    if not _is_contact_package_storage_ready(db):
        raise BusinessException(
            message="人群包模块尚未初始化，请先执行数据库迁移",
            code=4553,
            status_code=500,
        )

    balance = _get_contact_package_balance(db=db, user_pk=user_pk)
    if balance is None:
        balance = UserContactPackageBalance(
            user_pk=int(user_pk),
            purchased_views=safe_view_count,
            used_views=0,
            remaining_views=safe_view_count,
            last_order_no=_normalize_text(order_no) or None,
        )
    else:
        balance.purchased_views = max(int(balance.purchased_views or 0), 0) + safe_view_count
        balance.remaining_views = max(int(balance.remaining_views or 0), 0) + safe_view_count
        balance.last_order_no = _normalize_text(order_no) or balance.last_order_no

    db.add(balance)
    return resolve_contact_package_snapshot(db=db, user_pk=user_pk)


def consume_contact_package_view(
    db: Session,
    *,
    user_pk: int,
    commit: bool = False,
) -> dict:
    if not _is_contact_package_storage_ready(db):
        raise BusinessException(
            message="人群包模块尚未初始化，请先执行数据库迁移",
            code=4553,
            status_code=500,
        )

    balance = _get_contact_package_balance(db=db, user_pk=user_pk)
    if balance is None or int(balance.remaining_views or 0) <= 0:
        raise BusinessException(message="人群包剩余次数不足", code=4552, status_code=400)

    balance.remaining_views = max(int(balance.remaining_views or 0) - 1, 0)
    balance.used_views = max(int(balance.used_views or 0), 0) + 1
    db.add(balance)
    if commit:
        balance.updated_at = _utc_now_naive()
        db.commit()
        db.refresh(balance)
    return resolve_contact_package_snapshot(db=db, user_pk=user_pk)
