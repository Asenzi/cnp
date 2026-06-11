from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from secrets import token_hex

from fastapi import Request

from app.core.config import settings
from app.core.exceptions import BusinessException


STATIC_DIR = Path(__file__).resolve().parents[2] / "static"


@dataclass(frozen=True)
class StoredAsset:
    path: str
    url: str
    key: str
    backend: str


def normalize_file_suffix(raw_suffix: str, fallback: str) -> str:
    suffix = str(raw_suffix or "").strip().lower()
    if not suffix.startswith(".") or len(suffix) > 10:
        return fallback
    return suffix


def build_object_key(prefix: str, suffix: str) -> str:
    safe_prefix = str(prefix or "uploads").strip().strip("/")
    safe_suffix = normalize_file_suffix(suffix, ".bin")
    return f"{safe_prefix}/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{token_hex(4)}{safe_suffix}"


def _is_cos_enabled() -> bool:
    return (
        str(settings.STORAGE_BACKEND or "").strip().lower() == "cos"
        and bool(settings.COS_SECRET_ID)
        and bool(settings.COS_SECRET_KEY)
        and bool(settings.COS_REGION)
        and bool(settings.COS_BUCKET)
    )


def _build_cos_public_url(key: str) -> str:
    custom_domain = str(settings.COS_DOMAIN or "").strip().rstrip("/")
    if custom_domain:
        if custom_domain.startswith(("http://", "https://")):
            return f"{custom_domain}/{key}"
        scheme = str(settings.COS_SCHEME or "https").strip() or "https"
        return f"{scheme}://{custom_domain}/{key}"
    scheme = str(settings.COS_SCHEME or "https").strip() or "https"
    return f"{scheme}://{settings.COS_BUCKET}.cos.{settings.COS_REGION}.myqcloud.com/{key}"


def _upload_to_cos(*, key: str, body: bytes, content_type: str) -> StoredAsset:
    try:
        from qcloud_cos import CosConfig, CosS3Client
    except ImportError as exc:
        raise BusinessException(message="COS SDK 未安装，无法上传文件", code=5510, status_code=500) from exc

    try:
        config = CosConfig(
            Region=settings.COS_REGION,
            SecretId=settings.COS_SECRET_ID,
            SecretKey=settings.COS_SECRET_KEY,
            Scheme=str(settings.COS_SCHEME or "https").strip() or "https",
        )
        client = CosS3Client(config)
        client.put_object(
            Bucket=settings.COS_BUCKET,
            Body=BytesIO(body),
            Key=key,
            ContentType=content_type or "application/octet-stream",
            ACL="public-read",
        )
    except Exception as exc:  # noqa: BLE001
        raise BusinessException(message="文件上传 COS 失败，请稍后重试", code=5511, status_code=502) from exc

    public_url = _build_cos_public_url(key)
    return StoredAsset(path=public_url, url=public_url, key=key, backend="cos")


def _upload_to_local(*, key: str, body: bytes, request: Request | None) -> StoredAsset:
    save_path = STATIC_DIR / key
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(body)

    relative_url = f"/static/{key}"
    if request is None:
        public_url = relative_url
    else:
        public_url = f"{str(request.base_url).rstrip('/')}{relative_url}"
    return StoredAsset(path=relative_url, url=public_url, key=key, backend="local")


def upload_public_asset(
    *,
    prefix: str,
    file_bytes: bytes,
    suffix: str,
    content_type: str,
    request: Request | None = None,
) -> StoredAsset:
    if not file_bytes:
        raise BusinessException(message="上传文件为空", code=5509, status_code=400)

    key = build_object_key(prefix=prefix, suffix=suffix)
    if _is_cos_enabled():
        return _upload_to_cos(key=key, body=file_bytes, content_type=content_type)
    return _upload_to_local(key=key, body=file_bytes, request=request)
