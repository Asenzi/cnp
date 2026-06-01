from fastapi import Request

from app.core.exceptions import BusinessException

LOCAL_ONLY_ASSET_PREFIXES = ("wxfile://", "file://", "blob:")
TMP_HTTP_PREFIXES = ("http://tmp/", "https://tmp/")


def is_local_only_asset_url(value: str | None) -> bool:
    normalized = str(value or "").strip().lower()
    return bool(normalized) and (
        normalized.startswith(LOCAL_ONLY_ASSET_PREFIXES)
        or normalized.startswith("data:image/")
        or normalized.startswith(TMP_HTTP_PREFIXES)
    )


def normalize_persisted_asset_url(
    asset_url: str | None,
    *,
    request: Request | None = None,
    field_label: str = "资源地址",
    allow_empty: bool = False,
) -> str:
    normalized = str(asset_url or "").strip()
    if not normalized:
        if allow_empty:
            return ""
        raise BusinessException(message=f"{field_label}不能为空", code=4358, status_code=400)

    if is_local_only_asset_url(normalized):
        raise BusinessException(
            message=f"{field_label}不能使用本地临时图片，请先上传后再提交",
            code=4359,
            status_code=400,
        )

    if request is not None:
        base_url = str(request.base_url).rstrip("/")
        if normalized.startswith(f"{base_url}/static/"):
            return normalized.replace(base_url, "", 1)

    return normalized


def sanitize_public_asset_url(value: str | None, fallback: str = "") -> str:
    normalized = str(value or "").strip()
    if not normalized or is_local_only_asset_url(normalized):
        return str(fallback or "").strip()
    return normalized
