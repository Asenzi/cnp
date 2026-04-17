from collections import defaultdict
from typing import Any
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.circle import Circle
from app.models.network_reco_feedback import NetworkRecoFeedback
from app.models.network_reco_impression import NetworkRecoImpression
from app.models.user import User
from app.models.user_block import UserBlock
from app.models.user_circle_membership import UserCircleMembership
from app.models.user_connection import UserConnection


def list_candidate_users(
    db: Session,
    *,
    viewer_user_pk: int,
    limit_pool: int,
    keyword: str | None = None,
    city_name: str | None = None,
    industry_label: str | None = None,
    domain: str | None = None,
) -> list[User]:
    stmt = select(User).where(
        User.is_active.is_(True),
        User.id != viewer_user_pk,
    )

    normalized_keyword = str(keyword or "").strip()
    if normalized_keyword:
        pattern = f"%{normalized_keyword}%"
        stmt = stmt.where(
            or_(
                User.nickname.like(pattern),
                User.industry_label.like(pattern),
                User.city_name.like(pattern),
                User.intro.like(pattern),
            )
        )

    normalized_city_name = str(city_name or "").strip()
    if normalized_city_name:
        stmt = stmt.where(User.city_name == normalized_city_name)

    normalized_industry_label = str(industry_label or "").strip()
    if normalized_industry_label:
        stmt = stmt.where(User.industry_label == normalized_industry_label)

    normalized_domain = str(domain or "").strip()
    if normalized_domain:
        domain_pattern = f"%{normalized_domain}%"
        stmt = stmt.where(
            or_(
                User.industry_label.like(domain_pattern),
                User.intro.like(domain_pattern),
            )
        )

    stmt = stmt.order_by(
        User.is_verified.desc(),
        User.last_login_at.desc(),
        User.created_at.desc(),
        User.id.desc(),
    ).limit(max(limit_pool, 1))
    return list(db.execute(stmt).scalars().all())


def get_bidirectional_blocked_user_pks(db: Session, *, viewer_user_pk: int) -> set[int]:
    out_set: set[int] = set()

    stmt_a = select(UserBlock.blocked_user_pk).where(UserBlock.user_pk == viewer_user_pk)
    stmt_b = select(UserBlock.user_pk).where(UserBlock.blocked_user_pk == viewer_user_pk)

    for value in db.execute(stmt_a).scalars().all():
        if value:
            out_set.add(int(value))
    for value in db.execute(stmt_b).scalars().all():
        if value:
            out_set.add(int(value))

    return out_set


def get_bidirectional_connected_user_pks(db: Session, *, viewer_user_pk: int) -> set[int]:
    out_set: set[int] = set()

    stmt_a = select(UserConnection.target_user_pk).where(
        UserConnection.user_pk == viewer_user_pk,
        UserConnection.is_active.is_(True),
        UserConnection.target_user_pk.is_not(None),
    )
    stmt_b = select(UserConnection.user_pk).where(
        UserConnection.target_user_pk == viewer_user_pk,
        UserConnection.is_active.is_(True),
    )

    for value in db.execute(stmt_a).scalars().all():
        if value:
            out_set.add(int(value))
    for value in db.execute(stmt_b).scalars().all():
        if value:
            out_set.add(int(value))

    return out_set


def get_user_circle_codes(db: Session, *, user_pk: int) -> set[str]:
    stmt = select(UserCircleMembership.circle_code).where(
        UserCircleMembership.user_pk == user_pk,
        UserCircleMembership.is_active.is_(True),
    )
    return {str(code) for code in db.execute(stmt).scalars().all() if code}


def get_circle_overlap_counts(
    db: Session,
    *,
    viewer_circle_codes: set[str],
    candidate_user_pks: set[int],
) -> dict[int, int]:
    if not viewer_circle_codes or not candidate_user_pks:
        return {}

    stmt = (
        select(UserCircleMembership.user_pk, func.count(UserCircleMembership.id))
        .where(
            UserCircleMembership.is_active.is_(True),
            UserCircleMembership.circle_code.in_(viewer_circle_codes),
            UserCircleMembership.user_pk.in_(candidate_user_pks),
        )
        .group_by(UserCircleMembership.user_pk)
    )
    rows = db.execute(stmt).all()
    return {int(user_pk): int(count_value or 0) for user_pk, count_value in rows if user_pk}


def get_shared_circle_names(
    db: Session,
    *,
    viewer_circle_codes: set[str],
    candidate_user_pks: set[int],
    max_per_user: int = 3,
) -> dict[int, list[str]]:
    if not viewer_circle_codes or not candidate_user_pks:
        return {}

    stmt = (
        select(UserCircleMembership.user_pk, Circle.name)
        .join(Circle, Circle.circle_code == UserCircleMembership.circle_code)
        .where(
            UserCircleMembership.is_active.is_(True),
            UserCircleMembership.circle_code.in_(viewer_circle_codes),
            UserCircleMembership.user_pk.in_(candidate_user_pks),
        )
        .order_by(UserCircleMembership.user_pk.desc(), Circle.id.desc())
    )
    rows = db.execute(stmt).all()
    out_map: dict[int, list[str]] = defaultdict(list)
    for user_pk, circle_name in rows:
        if not user_pk or not circle_name:
            continue
        normalized_name = str(circle_name).strip()
        if not normalized_name:
            continue
        target_key = int(user_pk)
        existing = out_map[target_key]
        if normalized_name in existing:
            continue
        if len(existing) >= max(max_per_user, 1):
            continue
        existing.append(normalized_name)
    return dict(out_map)


def get_joined_circle_names(
    db: Session,
    *,
    candidate_user_pks: set[int],
    max_per_user: int = 3,
) -> dict[int, list[str]]:
    if not candidate_user_pks:
        return {}

    stmt = (
        select(UserCircleMembership.user_pk, Circle.name)
        .join(Circle, Circle.circle_code == UserCircleMembership.circle_code)
        .where(
            UserCircleMembership.is_active.is_(True),
            UserCircleMembership.user_pk.in_(candidate_user_pks),
        )
        .order_by(UserCircleMembership.user_pk.desc(), UserCircleMembership.id.desc())
    )
    rows = db.execute(stmt).all()
    out_map: dict[int, list[str]] = defaultdict(list)
    for user_pk, circle_name in rows:
        if not user_pk or not circle_name:
            continue
        normalized_name = str(circle_name).strip()
        if not normalized_name:
            continue
        target_key = int(user_pk)
        existing = out_map[target_key]
        if normalized_name in existing:
            continue
        if len(existing) >= max(max_per_user, 1):
            continue
        existing.append(normalized_name)
    return dict(out_map)


def get_candidate_circle_names(
    db: Session,
    *,
    candidate_user_pks: set[int],
    max_per_user: int = 3,
) -> dict[int, list[str]]:
    if not candidate_user_pks:
        return {}

    stmt = (
        select(UserCircleMembership.user_pk, Circle.name)
        .join(Circle, Circle.circle_code == UserCircleMembership.circle_code)
        .where(
            UserCircleMembership.is_active.is_(True),
            UserCircleMembership.user_pk.in_(candidate_user_pks),
        )
        .order_by(UserCircleMembership.user_pk.desc(), UserCircleMembership.id.desc(), Circle.id.desc())
    )
    rows = db.execute(stmt).all()
    out_map: dict[int, list[str]] = defaultdict(list)
    for user_pk, circle_name in rows:
        if not user_pk or not circle_name:
            continue
        normalized_name = str(circle_name).strip()
        if not normalized_name:
            continue
        target_key = int(user_pk)
        existing = out_map[target_key]
        if normalized_name in existing:
            continue
        if len(existing) >= max(max_per_user, 1):
            continue
        existing.append(normalized_name)
    return dict(out_map)


def get_connection_overlap_counts(
    db: Session,
    *,
    viewer_connected_user_pks: set[int],
    candidate_user_pks: set[int],
) -> dict[int, int]:
    if not viewer_connected_user_pks or not candidate_user_pks:
        return {}

    out_map: dict[int, int] = defaultdict(int)

    stmt_a = (
        select(UserConnection.user_pk, func.count(UserConnection.id))
        .where(
            UserConnection.is_active.is_(True),
            UserConnection.user_pk.in_(candidate_user_pks),
            UserConnection.target_user_pk.in_(viewer_connected_user_pks),
        )
        .group_by(UserConnection.user_pk)
    )
    stmt_b = (
        select(UserConnection.target_user_pk, func.count(UserConnection.id))
        .where(
            UserConnection.is_active.is_(True),
            UserConnection.target_user_pk.in_(candidate_user_pks),
            UserConnection.user_pk.in_(viewer_connected_user_pks),
            UserConnection.target_user_pk.is_not(None),
        )
        .group_by(UserConnection.target_user_pk)
    )

    for user_pk, count_value in db.execute(stmt_a).all():
        if user_pk:
            out_map[int(user_pk)] += int(count_value or 0)
    for user_pk, count_value in db.execute(stmt_b).all():
        if user_pk:
            out_map[int(user_pk)] += int(count_value or 0)

    return dict(out_map)


def get_shared_connection_names(
    db: Session,
    *,
    viewer_connected_user_pks: set[int],
    candidate_user_pks: set[int],
    max_per_user: int = 3,
) -> dict[int, list[str]]:
    if not viewer_connected_user_pks or not candidate_user_pks:
        return {}

    out_map: dict[int, list[str]] = defaultdict(list)

    stmt_a = (
        select(UserConnection.user_pk, User.nickname)
        .join(User, User.id == UserConnection.target_user_pk)
        .where(
            UserConnection.is_active.is_(True),
            UserConnection.user_pk.in_(candidate_user_pks),
            UserConnection.target_user_pk.in_(viewer_connected_user_pks),
        )
    )
    stmt_b = (
        select(UserConnection.target_user_pk, User.nickname)
        .join(User, User.id == UserConnection.user_pk)
        .where(
            UserConnection.is_active.is_(True),
            UserConnection.target_user_pk.in_(candidate_user_pks),
            UserConnection.user_pk.in_(viewer_connected_user_pks),
            UserConnection.target_user_pk.is_not(None),
        )
    )

    for user_pk, nickname in [*db.execute(stmt_a).all(), *db.execute(stmt_b).all()]:
        if not user_pk or not nickname:
            continue
        normalized_name = str(nickname).strip()
        if not normalized_name:
            continue
        target_key = int(user_pk)
        existing = out_map[target_key]
        if normalized_name in existing:
            continue
        if len(existing) >= max(max_per_user, 1):
            continue
        existing.append(normalized_name)

    return dict(out_map)


def get_impression_counts_in_days(
    db: Session,
    *,
    viewer_user_pk: int,
    candidate_user_pks: set[int],
    days: int,
) -> dict[int, int]:
    if not candidate_user_pks:
        return {}

    since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=max(days, 1))
    stmt = (
        select(NetworkRecoImpression.target_user_pk, func.count(NetworkRecoImpression.id))
        .where(
            NetworkRecoImpression.viewer_user_pk == viewer_user_pk,
            NetworkRecoImpression.target_user_pk.in_(candidate_user_pks),
            NetworkRecoImpression.created_at >= since,
        )
        .group_by(NetworkRecoImpression.target_user_pk)
    )
    rows = db.execute(stmt).all()
    return {int(user_pk): int(count_value or 0) for user_pk, count_value in rows if user_pk}


def get_global_impression_counts_in_days(
    db: Session,
    *,
    candidate_user_pks: set[int],
    days: int,
) -> dict[int, int]:
    if not candidate_user_pks:
        return {}

    since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=max(days, 1))
    stmt = (
        select(NetworkRecoImpression.target_user_pk, func.count(NetworkRecoImpression.id))
        .where(
            NetworkRecoImpression.target_user_pk.in_(candidate_user_pks),
            NetworkRecoImpression.created_at >= since,
        )
        .group_by(NetworkRecoImpression.target_user_pk)
    )
    rows = db.execute(stmt).all()
    return {int(user_pk): int(count_value or 0) for user_pk, count_value in rows if user_pk}


def get_recent_impression_target_user_pks(
    db: Session,
    *,
    viewer_user_pk: int,
    tab_key: str,
    scene: str = "discover",
    days: int = 1,
    limit: int = 60,
) -> list[int]:
    safe_limit = min(max(int(limit or 60), 1), 500)
    since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=max(days, 1))
    stmt = (
        select(NetworkRecoImpression.target_user_pk)
        .where(
            NetworkRecoImpression.viewer_user_pk == viewer_user_pk,
            NetworkRecoImpression.scene == str(scene or "discover"),
            NetworkRecoImpression.tab_key == str(tab_key or "recommend"),
            NetworkRecoImpression.created_at >= since,
            NetworkRecoImpression.target_user_pk.is_not(None),
        )
        .order_by(NetworkRecoImpression.id.desc())
        .limit(safe_limit * 4)
    )
    rows = db.execute(stmt).scalars().all()

    out_list: list[int] = []
    seen: set[int] = set()
    for user_pk in rows:
        if not user_pk:
            continue
        normalized = int(user_pk)
        if normalized in seen:
            continue
        seen.add(normalized)
        out_list.append(normalized)
        if len(out_list) >= safe_limit:
            break
    return out_list


def get_feedback_counts_in_days(
    db: Session,
    *,
    viewer_user_pk: int,
    candidate_user_pks: set[int],
    days: int,
    event_types: set[str],
) -> dict[int, int]:
    if not candidate_user_pks or not event_types:
        return {}

    since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=max(days, 1))
    stmt = (
        select(NetworkRecoFeedback.target_user_pk, func.count(NetworkRecoFeedback.id))
        .where(
            NetworkRecoFeedback.viewer_user_pk == viewer_user_pk,
            NetworkRecoFeedback.target_user_pk.in_(candidate_user_pks),
            NetworkRecoFeedback.event_type.in_(event_types),
            NetworkRecoFeedback.created_at >= since,
        )
        .group_by(NetworkRecoFeedback.target_user_pk)
    )
    rows = db.execute(stmt).all()
    return {int(user_pk): int(count_value or 0) for user_pk, count_value in rows if user_pk}


def get_global_feedback_counts_in_days(
    db: Session,
    *,
    candidate_user_pks: set[int],
    days: int,
    event_types: set[str],
) -> dict[int, int]:
    if not candidate_user_pks or not event_types:
        return {}

    since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=max(days, 1))
    stmt = (
        select(NetworkRecoFeedback.target_user_pk, func.count(NetworkRecoFeedback.id))
        .where(
            NetworkRecoFeedback.target_user_pk.in_(candidate_user_pks),
            NetworkRecoFeedback.event_type.in_(event_types),
            NetworkRecoFeedback.created_at >= since,
        )
        .group_by(NetworkRecoFeedback.target_user_pk)
    )
    rows = db.execute(stmt).all()
    return {int(user_pk): int(count_value or 0) for user_pk, count_value in rows if user_pk}


def get_feedback_targets_in_days(
    db: Session,
    *,
    viewer_user_pk: int,
    days: int,
    event_types: set[str],
) -> set[int]:
    if not event_types:
        return set()

    since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=max(days, 1))
    stmt = select(NetworkRecoFeedback.target_user_pk).where(
        NetworkRecoFeedback.viewer_user_pk == viewer_user_pk,
        NetworkRecoFeedback.event_type.in_(event_types),
        NetworkRecoFeedback.created_at >= since,
    )
    return {int(user_pk) for user_pk in db.execute(stmt).scalars().all() if user_pk}


def get_feedback_ext_rows_in_days(
    db: Session,
    *,
    viewer_user_pk: int,
    candidate_user_pks: set[int],
    days: int,
    event_types: set[str],
) -> list[tuple[int, str, str | None]]:
    if not candidate_user_pks or not event_types:
        return []

    since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=max(days, 1))
    stmt = (
        select(
            NetworkRecoFeedback.target_user_pk,
            NetworkRecoFeedback.event_type,
            NetworkRecoFeedback.ext_json,
        )
        .where(
            NetworkRecoFeedback.viewer_user_pk == viewer_user_pk,
            NetworkRecoFeedback.target_user_pk.in_(candidate_user_pks),
            NetworkRecoFeedback.event_type.in_(event_types),
            NetworkRecoFeedback.created_at >= since,
        )
        .order_by(NetworkRecoFeedback.id.desc())
    )
    rows = db.execute(stmt).all()
    return [
        (int(target_user_pk), str(event_type), ext_json)
        for target_user_pk, event_type, ext_json in rows
        if target_user_pk and event_type
    ]


def list_recent_feedback_target_profiles(
    db: Session,
    *,
    viewer_user_pk: int,
    days: int,
    event_types: set[str],
    limit: int = 80,
) -> list[dict[str, Any]]:
    if not event_types:
        return []

    safe_limit = min(max(int(limit or 80), 1), 300)
    since = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=max(days, 1))
    stmt = (
        select(
            NetworkRecoFeedback.target_user_pk,
            NetworkRecoFeedback.event_type,
            NetworkRecoFeedback.created_at,
            User.industry_label,
            User.city_name,
            User.is_verified,
        )
        .join(User, User.id == NetworkRecoFeedback.target_user_pk)
        .where(
            NetworkRecoFeedback.viewer_user_pk == viewer_user_pk,
            NetworkRecoFeedback.event_type.in_(event_types),
            NetworkRecoFeedback.created_at >= since,
        )
        .order_by(NetworkRecoFeedback.created_at.desc(), NetworkRecoFeedback.id.desc())
        .limit(safe_limit)
    )

    rows = db.execute(stmt).all()
    return [
        {
            "target_user_pk": int(target_user_pk),
            "event_type": str(event_type),
            "created_at": created_at,
            "industry_label": str(industry_label or "").strip(),
            "city_name": str(city_name or "").strip(),
            "is_verified": bool(is_verified),
        }
        for target_user_pk, event_type, created_at, industry_label, city_name, is_verified in rows
        if target_user_pk and event_type
    ]


def map_business_user_ids_to_pks(
    db: Session,
    *,
    business_user_ids: set[str],
) -> dict[str, int]:
    if not business_user_ids:
        return {}

    stmt = select(User.user_id, User.id).where(User.user_id.in_(business_user_ids))
    rows = db.execute(stmt).all()
    return {str(user_id): int(user_pk) for user_id, user_pk in rows if user_id and user_pk}


def list_filter_option_values(
    db: Session,
    *,
    limit: int = 20,
) -> dict[str, list[str]]:
    safe_limit = min(max(int(limit or 20), 1), 100)

    city_stmt = (
        select(User.city_name, func.count(User.id))
        .where(
            User.is_active.is_(True),
            User.city_name.is_not(None),
            User.city_name != "",
        )
        .group_by(User.city_name)
        .order_by(func.count(User.id).desc(), User.city_name.asc())
        .limit(safe_limit)
    )
    industry_stmt = (
        select(User.industry_label, func.count(User.id))
        .where(
            User.is_active.is_(True),
            User.industry_label.is_not(None),
            User.industry_label != "",
        )
        .group_by(User.industry_label)
        .order_by(func.count(User.id).desc(), User.industry_label.asc())
        .limit(safe_limit)
    )

    city_rows = db.execute(city_stmt).all()
    industry_rows = db.execute(industry_stmt).all()

    return {
        "cities": [str(value).strip() for value, _ in city_rows if value and str(value).strip()],
        "industries": [str(value).strip() for value, _ in industry_rows if value and str(value).strip()],
    }


def create_reco_impressions(
    db: Session,
    *,
    viewer_user_pk: int,
    target_user_pks: set[int],
    scene: str,
    tab_key: str,
    request_id: str | None,
) -> int:
    if not target_user_pks:
        return 0

    rows = [
        NetworkRecoImpression(
            viewer_user_pk=viewer_user_pk,
            target_user_pk=target_user_pk,
            scene=scene,
            tab_key=tab_key,
            request_id=request_id,
        )
        for target_user_pk in target_user_pks
    ]
    db.add_all(rows)
    db.commit()
    return len(rows)


def create_reco_feedback(
    db: Session,
    *,
    viewer_user_pk: int,
    target_user_pk: int,
    scene: str,
    tab_key: str,
    request_id: str | None,
    event_type: str,
    ext_json: str | None,
) -> None:
    row = NetworkRecoFeedback(
        viewer_user_pk=viewer_user_pk,
        target_user_pk=target_user_pk,
        scene=scene,
        tab_key=tab_key,
        request_id=request_id,
        event_type=event_type,
        ext_json=ext_json,
    )
    db.add(row)
    db.commit()
