"""Shared WeChat Mini Program access-token management.

WeChat may invalidate tokens obtained independently for the same AppID.  Keep a
single Redis-backed cache for every web/worker process and use the stable-token
endpoint so login, content moderation and mini-program-code generation do not
invalidate each other's credentials.
"""

from __future__ import annotations

import json
import time
from hashlib import sha256
from threading import Lock
from urllib.request import Request as UrlRequest, urlopen

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.logger import logger

_LOCAL_CACHE: dict[str, str | float] = {"token": "", "expires_at": 0.0}
_LOCAL_LOCK = Lock()
_REDIS_CLIENT: Redis | None = None
_TOKEN_EXPIRY_SAFETY_SECONDS = 120


def _redis_key(app_id: str) -> str:
    fingerprint = sha256(app_id.encode("utf-8")).hexdigest()[:16]
    return f"wechat:miniapp:access_token:{fingerprint}"


def _get_redis_client() -> Redis | None:
    global _REDIS_CLIENT
    if not settings.REDIS_ENABLED:
        return None
    if _REDIS_CLIENT is None:
        try:
            _REDIS_CLIENT = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
        except (RedisError, OSError, ValueError) as exc:
            logger.warning(f"WeChat token Redis initialization skipped: {exc}")
            return None
    return _REDIS_CLIENT


def _read_cached_token(app_id: str) -> str:
    client = _get_redis_client()
    if client is not None:
        try:
            token = str(client.get(_redis_key(app_id)) or "").strip()
            if token:
                return token
        except (RedisError, OSError) as exc:
            logger.warning(f"WeChat token Redis read skipped: {exc}")

    now = time.time()
    token = str(_LOCAL_CACHE.get("token") or "").strip()
    expires_at = float(_LOCAL_CACHE.get("expires_at") or 0)
    return token if token and expires_at > now else ""


def invalidate_wechat_access_token() -> None:
    """Invalidate both shared and process-local copies after token errors."""
    app_id = str(settings.WECHAT_MINI_APP_ID or "").strip()
    _LOCAL_CACHE.update(token="", expires_at=0.0)
    if not app_id:
        return
    client = _get_redis_client()
    if client is not None:
        try:
            client.delete(_redis_key(app_id))
        except (RedisError, OSError) as exc:
            logger.warning(f"WeChat token Redis invalidation skipped: {exc}")


def get_wechat_access_token(*, force_refresh: bool = False) -> str:
    app_id = str(settings.WECHAT_MINI_APP_ID or "").strip()
    app_secret = str(settings.WECHAT_MINI_APP_SECRET or "").strip()
    if not app_id or not app_secret:
        return ""

    if force_refresh:
        invalidate_wechat_access_token()
    else:
        cached = _read_cached_token(app_id)
        if cached:
            return cached

    with _LOCAL_LOCK:
        if not force_refresh:
            cached = _read_cached_token(app_id)
            if cached:
                return cached

        body = json.dumps(
            {
                "grant_type": "client_credential",
                "appid": app_id,
                "secret": app_secret,
                "force_refresh": bool(force_refresh),
            }
        ).encode("utf-8")
        request = UrlRequest(
            "https://api.weixin.qq.com/cgi-bin/stable_token",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=8) as response:  # noqa: S310 - fixed trusted WeChat URL.
            payload = json.loads(response.read().decode("utf-8"))

        token = str(payload.get("access_token") or "").strip()
        if not token:
            logger.warning(
                "WeChat stable token missing, "
                f"errcode={payload.get('errcode')}, errmsg={payload.get('errmsg')}"
            )
            return ""

        expires_in = max(int(payload.get("expires_in") or 7200) - _TOKEN_EXPIRY_SAFETY_SECONDS, 300)
        _LOCAL_CACHE.update(token=token, expires_at=time.time() + expires_in)
        client = _get_redis_client()
        if client is not None:
            try:
                client.setex(_redis_key(app_id), expires_in, token)
            except (RedisError, OSError) as exc:
                logger.warning(f"WeChat token Redis write skipped: {exc}")
        return token
