from types import SimpleNamespace

from app.api.v1 import user as user_api
from app.core.exceptions import BusinessException


def demo():
    original_enabled = user_api.settings.WECHAT_CONTENT_SECURITY_ENABLED
    original_token = user_api._get_wechat_access_token
    original_request_json = user_api._request_json
    fake_user = SimpleNamespace(wechat_openid="openid")

    try:
        user_api.settings.WECHAT_CONTENT_SECURITY_ENABLED = True
        user_api._get_wechat_access_token = lambda: "token"

        user_api._request_json = lambda url, data=None: {"errcode": 0, "result": {"suggest": "pass"}}
        user_api._assert_wechat_text_safe(user=fake_user, fields={"nickname": "正常昵称"})

        user_api._request_json = lambda url, data=None: {"errcode": 87014, "result": {"suggest": "risky"}}
        try:
            user_api._assert_wechat_text_safe(user=fake_user, fields={"nickname": "bad"})
        except BusinessException as exc:
            assert exc.code == 4261
        else:
            raise AssertionError("risky text was not blocked")

        user_api._request_json = lambda url, data=None: {"errcode": 0}
        user_api._submit_wechat_image_check(user=fake_user, media_url="https://example.com/a.jpg")

        pending_user = SimpleNamespace(user_id="12345678", avatar_url="https://bad.example/a.jpg", avatar_review_status="pending")
        assert user_api._public_avatar_value(pending_user) == user_api.settings.DEFAULT_AVATAR_URL

        original_require_ims = user_api.settings.PRODUCT_SAFETY_REQUIRE_IMS
        original_ims_url = user_api.settings.PRODUCT_SAFETY_IMS_URL
        user_api.settings.PRODUCT_SAFETY_REQUIRE_IMS = True
        user_api.settings.PRODUCT_SAFETY_IMS_URL = ""
        try:
            user_api._assert_ims_safe(content_type="text", value="正常内容", user=fake_user)
        except BusinessException as exc:
            assert exc.code == 4265
        else:
            raise AssertionError("missing IMS config was not blocked")
        finally:
            user_api.settings.PRODUCT_SAFETY_REQUIRE_IMS = original_require_ims
            user_api.settings.PRODUCT_SAFETY_IMS_URL = original_ims_url
    finally:
        user_api.settings.WECHAT_CONTENT_SECURITY_ENABLED = original_enabled
        user_api._get_wechat_access_token = original_token
        user_api._request_json = original_request_json


if __name__ == "__main__":
    demo()
