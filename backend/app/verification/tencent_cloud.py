from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.core.exceptions import BusinessException

FACEID_HOST = "faceid.tencentcloudapi.com"
FACEID_ENDPOINT = f"https://{FACEID_HOST}"
FACEID_SERVICE = "faceid"
FACEID_VERSION = "2018-03-01"
PROVIDER_NAME = "tencent_cloud"


@dataclass(slots=True)
class TencentDetectAuthResult:
    provider_biz_token: str
    provider_request_id: str | None
    redirect_url: str | None
    raw_response: dict


@dataclass(slots=True)
class TencentDetectInfoResult:
    provider_request_id: str | None
    is_success: bool
    fail_reason: str | None
    real_name: str | None
    id_number: str | None
    raw_response: dict


def _utc_timestamp() -> int:
    return int(datetime.now(UTC).timestamp())


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _build_authorization(*, action: str, payload_json: str, timestamp: int) -> str:
    secret_id = str(settings.TENCENT_CLOUD_SECRET_ID or "").strip()
    secret_key = str(settings.TENCENT_CLOUD_SECRET_KEY or "").strip()
    region = str(settings.TENCENT_CLOUD_REGION or "ap-guangzhou").strip()
    if not secret_id or not secret_key:
        raise BusinessException(message="腾讯云实名认证配置不完整", code=4351, status_code=503)

    date = datetime.fromtimestamp(timestamp, UTC).strftime("%Y-%m-%d")
    credential_scope = f"{date}/{FACEID_SERVICE}/tc3_request"
    hashed_request_payload = _sha256_hex(payload_json)
    canonical_request = "\n".join(
        [
            "POST",
            "/",
            "",
            "content-type:application/json; charset=utf-8\n"
            f"host:{FACEID_HOST}\n"
            f"x-tc-action:{action.lower()}\n",
            "content-type;host;x-tc-action",
            hashed_request_payload,
        ]
    )
    string_to_sign = "\n".join(
        [
            "TC3-HMAC-SHA256",
            str(timestamp),
            credential_scope,
            _sha256_hex(canonical_request),
        ]
    )
    secret_date = _sign(f"TC3{secret_key}".encode("utf-8"), date)
    secret_service = _sign(secret_date, FACEID_SERVICE)
    secret_signing = _sign(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    return (
        "TC3-HMAC-SHA256 "
        f"Credential={secret_id}/{credential_scope}, "
        "SignedHeaders=content-type;host;x-tc-action, "
        f"Signature={signature}"
    )


def _request_faceid_api(*, action: str, payload: dict) -> dict:
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    timestamp = _utc_timestamp()
    region = str(settings.TENCENT_CLOUD_REGION or "ap-guangzhou").strip()
    request = Request(
        url=FACEID_ENDPOINT,
        method="POST",
        data=payload_json.encode("utf-8"),
        headers={
            "Authorization": _build_authorization(action=action, payload_json=payload_json, timestamp=timestamp),
            "Content-Type": "application/json; charset=utf-8",
            "Host": FACEID_HOST,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": FACEID_VERSION,
            "X-TC-Region": region,
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise BusinessException(
            message=f"腾讯云实名认证请求失败: {detail or exc.reason}",
            code=4352,
            status_code=502,
        ) from exc
    except URLError as exc:
        raise BusinessException(
            message=f"腾讯云实名认证网络异常: {exc.reason}",
            code=4353,
            status_code=502,
        ) from exc

    try:
        parsed = json.loads(body)
    except ValueError as exc:
        raise BusinessException(message="腾讯云实名认证返回格式无效", code=4354, status_code=502) from exc

    response_payload = parsed.get("Response") if isinstance(parsed, dict) else None
    if not isinstance(response_payload, dict):
        raise BusinessException(message="腾讯云实名认证返回内容缺失", code=4355, status_code=502)
    error = response_payload.get("Error")
    if isinstance(error, dict):
        raise BusinessException(
            message=f"腾讯云实名认证失败: {error.get('Message') or error.get('Code') or 'unknown error'}",
            code=4356,
            status_code=400,
            data={"provider_error": error},
        )
    return response_payload


def create_detect_auth(*, real_name: str, id_number: str) -> TencentDetectAuthResult:
    app_id = str(settings.TENCENT_CLOUD_FACEID_APP_ID or "").strip()
    rule_id = str(settings.TENCENT_CLOUD_FACEID_RULE_ID or "").strip()
    redirect_url = str(settings.TENCENT_CLOUD_FACEID_REDIRECT_URL or "").strip()
    if not app_id or not rule_id:
        raise BusinessException(message="腾讯云实名认证规则配置不完整", code=4357, status_code=503)

    payload = {
        "RuleId": rule_id,
        "Name": real_name,
        "IdCard": id_number,
        "RedirectUrl": redirect_url or None,
        "RedirectType": "0",
        "DetectMode": "0",
    }
    response_payload = _request_faceid_api(action="DetectAuth", payload=payload)
    biz_token = str(response_payload.get("BizToken") or "").strip()
    if not biz_token:
        raise BusinessException(message="腾讯云实名认证未返回 BizToken", code=4358, status_code=502)

    return TencentDetectAuthResult(
        provider_biz_token=biz_token,
        provider_request_id=str(response_payload.get("RequestId") or "").strip() or None,
        redirect_url=str(response_payload.get("Url") or redirect_url).strip() or None,
        raw_response=response_payload,
    )


def get_detect_info_enhanced(*, provider_biz_token: str) -> TencentDetectInfoResult:
    response_payload = _request_faceid_api(
        action="GetDetectInfoEnhanced",
        payload={
            "BizToken": provider_biz_token,
            "RuleId": str(settings.TENCENT_CLOUD_FACEID_RULE_ID or "").strip() or None,
            "InfoType": "0",
        },
    )
    detect_info = response_payload.get("DetectInfo")
    if isinstance(detect_info, str):
        try:
            detect_info = json.loads(detect_info)
        except ValueError:
            detect_info = {}
    detect_info = detect_info if isinstance(detect_info, dict) else {}
    text_info = detect_info.get("Text")
    text_info = text_info if isinstance(text_info, dict) else {}

    err_code = text_info.get("ErrCode")
    err_msg = text_info.get("ErrMsg")
    is_success = str(err_code) in {"0", ""} and response_payload.get("BizToken") is not None

    return TencentDetectInfoResult(
        provider_request_id=str(response_payload.get("RequestId") or "").strip() or None,
        is_success=is_success,
        fail_reason=None if is_success else str(err_msg or "腾讯云实名认证未通过").strip(),
        real_name=str(text_info.get("Name") or "").strip() or None,
        id_number=str(text_info.get("IdCard") or "").strip() or None,
        raw_response=response_payload,
    )
