from types import SimpleNamespace

from app.auth import service as auth_service


class FakeDb:
    def __init__(self):
        self.added = []
        self.committed = False
        self.refreshed = []
        self.rolled_back = False

    def add(self, item):
        self.added.append(item)

    def commit(self):
        self.committed = True

    def refresh(self, item):
        self.refreshed.append(item)

    def rollback(self):
        self.rolled_back = True


def demo():
    original_get_user_by_phone = auth_service.get_user_by_phone
    original_get_user_by_id = auth_service.get_user_by_id
    calls = []

    try:
        auth_service.get_user_by_phone = lambda db, phone: calls.append(phone) or None

        db = FakeDb()
        user = SimpleNamespace(id=1, phone="19900000074")
        result = auth_service._sync_authorized_phone_to_wechat_user(
            db=db,
            user=user,
            authorized_phone="18300000034",
        )

        assert result is user
        assert user.phone == "19900000074"
        assert calls == []
        assert db.added == []

        legacy_user = SimpleNamespace(id=2, phone="wx_legacy_identity")
        result = auth_service._sync_authorized_phone_to_wechat_user(
            db=db,
            user=legacy_user,
            authorized_phone="19900000074",
        )

        assert result is legacy_user
        assert legacy_user.phone == "19900000074"
        assert calls == ["19900000074"]
        assert db.added == [legacy_user]

        close_db = FakeDb()
        close_user = SimpleNamespace(
            id=3,
            phone="18800000003",
            is_active=True,
            banned_at=None,
            token_version=1,
            password_hash="hashed",
            wechat_openid="openid",
            wechat_unionid="unionid",
            wechat_session_key="session",
            wechat_bound_at="bound",
            display_phone="18800000003",
            display_wechat="wechat",
            email="user@example.com",
            show_contact=True,
        )
        auth_service.get_user_by_id = lambda db, user_id: close_user

        close_result = auth_service.close_account_for_user(
            db=close_db,
            current_user_pk=close_user.id,
            confirm_text="注销账号",
        )

        assert close_result.closed is True
        assert close_result.force_relogin is True
        assert close_user.is_active is False
        assert close_user.token_version == 2
        assert close_user.phone.startswith("closed_")
        assert close_user.password_hash is None
        assert close_user.wechat_openid is None
        assert close_user.wechat_unionid is None
        assert close_user.wechat_session_key is None
        assert close_user.wechat_bound_at is None
        assert close_user.display_phone is None
        assert close_user.display_wechat is None
        assert close_user.email is None
        assert close_user.show_contact is False
        assert close_db.added == [close_user]
    finally:
        auth_service.get_user_by_phone = original_get_user_by_phone
        auth_service.get_user_by_id = original_get_user_by_id


if __name__ == "__main__":
    demo()
