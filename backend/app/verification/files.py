import mimetypes
from pathlib import Path

from app.core.exceptions import BusinessException

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
PRIVATE_STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage" / "verification"
ID_CARD_STORAGE_DIR = PRIVATE_STORAGE_DIR / "id-cards"

LEGACY_ID_CARD_URL_PREFIX = "/static/uploads/id-cards/"
PRIVATE_ID_CARD_URL_PREFIX = "private://verification/id-cards/"


def build_private_id_card_file_ref(file_name: str) -> str:
    normalized = Path(str(file_name or "").strip()).name
    if not normalized:
        raise BusinessException(message="证件文件不存在", code=4344, status_code=404)
    return f"{PRIVATE_ID_CARD_URL_PREFIX}{normalized}"


def resolve_id_card_file_path(file_url: str | None) -> Path:
    normalized = str(file_url or "").strip()
    if not normalized:
        raise BusinessException(message="证件文件不存在", code=4344, status_code=404)

    storage_root: Path
    if normalized.startswith(PRIVATE_ID_CARD_URL_PREFIX):
        storage_root = ID_CARD_STORAGE_DIR.resolve()
        file_name = normalized.removeprefix(PRIVATE_ID_CARD_URL_PREFIX).strip()
    elif normalized.startswith(LEGACY_ID_CARD_URL_PREFIX):
        storage_root = (STATIC_DIR / "uploads" / "id-cards").resolve()
        file_name = normalized.removeprefix(LEGACY_ID_CARD_URL_PREFIX).strip()
    else:
        raise BusinessException(message="证件文件路径不合法", code=4345, status_code=400)

    file_name = Path(file_name).name
    if not file_name:
        raise BusinessException(message="证件文件不存在", code=4344, status_code=404)

    absolute_path = (storage_root / file_name).resolve()
    if storage_root not in absolute_path.parents or not absolute_path.is_file():
        raise BusinessException(message="证件文件不存在", code=4344, status_code=404)

    return absolute_path


def guess_media_type(path: Path) -> str:
    media_type, _ = mimetypes.guess_type(str(path))
    return media_type or "application/octet-stream"
