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
    """
    使用腾讯云身份证二要素核验（IdCardVerification）
    只验证姓名和身份证号是否匹配，无需人脸识别
    """
    # 使用二要素验证接口，不需要 AppId 和 RuleId
    payload = {
        "Name": real_name,
        "IdCard": id_number,
    }
    response_payload = _request_faceid_api(action="IdCardVerification", payload=payload)

    # 二要素验证直接返回结果，不需要跳转
    result = str(response_payload.get("Result") or "").strip()
    description = str(response_payload.get("Description") or "").strip()

    # Result 为 "0" 表示一致，其他值表示不一致
    is_match = result == "0"

    if not is_match:
        raise BusinessException(
            message=f"身份信息验证失败: {description or '姓名与身份证号不匹配'}",
            code=4358,
            status_code=400
        )

    # 生成一个伪 BizToken，用于后续流程
    import uuid
    biz_token = f"idcard_verify_{uuid.uuid4().hex}"

    return TencentDetectAuthResult(
        provider_biz_token=biz_token,
        provider_request_id=str(response_payload.get("RequestId") or "").strip() or None,
        redirect_url=None,  # 二要素验证不需要跳转
        raw_response=response_payload,
    )


def get_detect_info_enhanced(*, provider_biz_token: str) -> TencentDetectInfoResult:
    """
    获取二要素验证结果
    由于二要素验证是同步的，这里直接返回成功状态
    """
    # 二要素验证在 create_detect_auth 中已经完成
    # 这里直接返回成功状态
    return TencentDetectInfoResult(
        provider_request_id=provider_biz_token,
        is_success=True,
        fail_reason=None,
        real_name=None,  # 二要素验证不返回姓名
        id_number=None,  # 二要素验证不返回身份证号
        raw_response={"status": "verified", "biz_token": provider_biz_token},
    )
