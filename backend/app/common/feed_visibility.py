from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.crud.sys_config import get_sys_config_values
from app.models.sys_config import SysConfig

FEED_SELF_VISIBILITY_CONFIGS: dict[str, dict[str, str]] = {
    "network": {
        "key": "feed.visibility.show_self_network",
        "description": "人脉推荐流是否允许当前用户看到自己的人脉卡片，1=显示，0=隐藏",
    },
    "resource": {
        "key": "feed.visibility.show_self_resource",
        "description": "资源推荐流是否允许当前用户看到自己发布的资源，1=显示，0=隐藏",
    },
    "circle": {
        "key": "feed.visibility.show_self_circle",
        "description": "圈子推荐流是否允许当前用户看到自己创建的圈子，1=显示，0=隐藏",
    },
}

DEFAULT_SELF_VISIBILITY_VALUE = "0"


def normalize_config_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return int(value) == 1
    normalized = str(value or "").strip().lower()
    if not normalized:
        return bool(default)
    if normalized in {"1", "true", "yes", "on", "enabled", "show", "visible"}:
        return True
    if normalized in {"0", "false", "no", "off", "disabled", "hide", "hidden"}:
        return False
    return bool(default)


def get_feed_self_visibility_key(channel: str) -> str:
    normalized_channel = str(channel or "").strip().lower()
    meta = FEED_SELF_VISIBILITY_CONFIGS.get(normalized_channel)
    return str(meta["key"]) if meta else ""


def is_feed_self_visible(db: Session, *, channel: str, default: bool = False) -> bool:
    config_key = get_feed_self_visibility_key(channel)
    if not config_key:
        return bool(default)
    values = get_sys_config_values(db=db, config_keys={config_key})
    return normalize_config_bool(values.get(config_key), default=default)


def ensure_default_feed_visibility_configs() -> None:
    rows = [
        (
            meta["key"],
            DEFAULT_SELF_VISIBILITY_VALUE,
            "feed_visibility",
            meta["description"],
        )
        for meta in FEED_SELF_VISIBILITY_CONFIGS.values()
    ]
    with SessionLocal() as db:
        existing_keys = {
            str(key)
            for key in db.execute(
                select(SysConfig.config_key).where(SysConfig.config_key.in_([row[0] for row in rows]))
            ).scalars().all()
            if key
        }
        for config_key, config_value, config_group, description in rows:
            if config_key in existing_keys:
                continue
            db.add(
                SysConfig(
                    config_key=config_key,
                    config_value=config_value,
                    config_group=config_group,
                    description=description,
                )
            )
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise
