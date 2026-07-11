from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.core.exceptions import BusinessException

VERSION = "2020-12-29"


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _authorization(*, host: str, service: str, action: str, payload_json: str, timestamp: int) -> str:
    secret_id = str(settings.TENCENT_CLOUD_SECRET_ID or "").strip()
    secret_key = str(settings.TENCENT_CLOUD_SECRET_KEY or "").strip()
    if not secret_id or not secret_key:
        raise BusinessException(message="腾讯云内容安全配置不完整", code=4271, status_code=503)

    date = datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%d")
    scope = f"{date}/{service}/tc3_request"
    canonical_request = "\n".join(
        [
            "POST",
            "/",
            "",
            "content-type:application/json; charset=utf-8\n"
            f"host:{host}\n"
            f"x-tc-action:{action.lower()}\n",
            "content-type;host;x-tc-action",
            _sha256_hex(payload_json),
        ]
    )
    string_to_sign = "\n".join(["TC3-HMAC-SHA256", str(timestamp), scope, _sha256_hex(canonical_request)])
    secret_date = _sign(f"TC3{secret_key}".encode("utf-8"), date)
    secret_service = _sign(secret_date, service)
    secret_signing = _sign(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    return (
        "TC3-HMAC-SHA256 "
        f"Credential={secret_id}/{scope}, "
        "SignedHeaders=content-type;host;x-tc-action, "
        f"Signature={signature}"
    )


def _request_tencent_cloud(*, host: str, service: str, action: str, payload: dict) -> dict:
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    timestamp = int(datetime.now(timezone.utc).timestamp())
    region = str(settings.TENCENT_CLOUD_REGION or "ap-guangzhou").strip()
    request = Request(
        url=f"https://{host}",
        method="POST",
        data=payload_json.encode("utf-8"),
        headers={
            "Authorization": _authorization(
                host=host,
                service=service,
                action=action,
                payload_json=payload_json,
                timestamp=timestamp,
            ),
            "Content-Type": "application/json; charset=utf-8",
            "Host": host,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": VERSION,
            "X-TC-Region": region,
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise BusinessException(message=f"腾讯云内容安全请求失败: {detail or exc.reason}", code=4272, status_code=502) from exc
    except URLError as exc:
        raise BusinessException(message=f"腾讯云内容安全网络异常: {exc.reason}", code=4273, status_code=502) from exc

    try:
        parsed = json.loads(raw)
    except ValueError as exc:
        raise BusinessException(message="腾讯云内容安全返回格式无效", code=4274, status_code=502) from exc

    response_payload = parsed.get("Response") if isinstance(parsed, dict) else None
    if not isinstance(response_payload, dict):
        raise BusinessException(message="腾讯云内容安全返回内容缺失", code=4275, status_code=502)
    error = response_payload.get("Error")
    if isinstance(error, dict):
        raise BusinessException(
            message=f"腾讯云内容安全失败: {error.get('Message') or error.get('Code') or 'unknown error'}",
            code=4276,
            status_code=502,
            data={"provider_error": error},
        )
    return response_payload


def moderate_with_tencent_cloud(*, content_type: str, value: str, user_id: str = "") -> dict:
    data_id = (user_id or uuid.uuid4().hex).replace("-", "_")[:32]
    if content_type == "text":
        payload = {
            "Content": base64.b64encode(value.encode("utf-8")).decode("ascii"),
            "DataId": data_id,
            "Type": "TEXT",
        }
        response = _request_tencent_cloud(
            host="tms.tencentcloudapi.com",
            service="tms",
            action="TextModeration",
            payload=payload,
        )
    elif content_type == "image":
        payload = {
            "FileUrl": value,
            "DataId": data_id,
            "Type": "IMAGE",
        }
        response = _request_tencent_cloud(
            host="ims.tencentcloudapi.com",
            service="ims",
            action="ImageModeration",
            payload=payload,
        )
    else:
        raise BusinessException(message="审核内容类型无效", code=4270, status_code=400)

    suggestion = str(response.get("Suggestion") or "").strip().lower()
    return {
        "status": "pass" if suggestion == "pass" else "reject",
        "suggest": suggestion or "reject",
        "label": response.get("Label") or "",
        "sub_label": response.get("SubLabel") or "",
        "score": response.get("Score") or 0,
        "request_id": response.get("RequestId") or "",
    }
