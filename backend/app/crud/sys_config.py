from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sys_config import SysConfig


def get_sys_config_values(
    db: Session,
    *,
    config_keys: set[str],
) -> dict[str, str]:
    normalized_keys = {str(item or "").strip() for item in config_keys if str(item or "").strip()}
    if not normalized_keys:
        return {}

    stmt = select(SysConfig.config_key, SysConfig.config_value).where(SysConfig.config_key.in_(normalized_keys))
    rows = db.execute(stmt).all()
    return {
        str(config_key): str(config_value or "")
        for config_key, config_value in rows
        if config_key
    }
