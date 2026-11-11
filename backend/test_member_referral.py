"""Offline referral regression checks; uses only an in-memory database."""
import unittest
from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Base, User, MemberOrder, SplitTransaction
from app.payment.service import _resolve_order_referral_partner
from app.settlement.service import settle_member_referral_commission, _resolve_service_fee_rate


class ReferralTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.city = self.user("CITY", "city_partner")
        self.a = self.user("AAAA", "salon_owner")
        self.b = self.user("BBBB", "salon_owner")
        self.a.city_partner_user_pk = self.city.id
        self.b.city_partner_user_pk = self.city.id
        self.buyer = self.user("USER", None)
        self.buyer.inviter_user_pk = self.a.id
        self.verify_buyer()
        self.db.commit()

    def verify_buyer(self):
        from app.models import UserRealNameProfile
        profile = self.db.scalar(select(UserRealNameProfile).where(UserRealNameProfile.user_pk == self.buyer.id))
        if profile is None:
            profile = UserRealNameProfile(user_pk=self.buyer.id, real_name="test", id_number_masked="***",
                                          id_number_hash="test", id_number_encrypted="", id_front_url="", id_back_url="")
            self.db.add(profile)
        profile.verified_at = datetime.now()
        self.db.flush()

    def unverify_buyer(self):
        from app.models import UserRealNameProfile
        profile = self.db.scalar(select(UserRealNameProfile).where(UserRealNameProfile.user_pk == self.buyer.id))
        profile.verified_at = None
        self.db.commit()

    def test_unverified_payment_waits_and_modified_code_wins(self):
        from app.verification.referral import confirm_membership_referral, current_invite_code
        self.unverify_buyer()
        order = self.pay("AAAA", "WAIT")
        self.assertEqual(self.shares(order), {})
        self.assertIsNone(self.buyer.member_referral_snapshot)
        self.assertEqual(current_invite_code(self.db, self.buyer), "AAAA")
        confirm_membership_referral(self.db, self.buyer, "BBBB")
        self.assertEqual(self.shares(order), {})
        self.verify_buyer()
        confirm_membership_referral(self.db, self.buyer, "BBBB")
        self.assertEqual(self.shares(order), {self.city.id: Decimal("30"), self.b.id: Decimal("40")})
        self.assertEqual(self.shares(self.pay("AAAA", "RENEW_MODIFIED")),
                         {self.city.id: Decimal("30"), self.b.id: Decimal("40")})

    def test_verification_can_clear_code_and_lock_platform(self):
        from app.verification.referral import confirm_membership_referral
        self.unverify_buyer()
        order = self.pay("AAAA", "CLEAR")
        self.verify_buyer()
        confirm_membership_referral(self.db, self.buyer, "")
        self.assertEqual(self.shares(order), {})
        self.assertEqual(self.buyer.member_referral_snapshot, "{}")

    def test_locked_invite_cannot_change_and_invalid_code_rejected(self):
        from app.verification.referral import validate_invite_code
        from app.core.exceptions import BusinessException
        with self.assertRaises(BusinessException):
            validate_invite_code(self.db, self.buyer, "ZZZZ")
        self.pay("AAAA", "LOCKED")
        with self.assertRaises(BusinessException):
            validate_invite_code(self.db, self.buyer, "BBBB")

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def user(self, code, role):
        user = User(user_id=code, phone=code, partner_type=role,
                    partner_invite_code=code if role else None, is_active=True)
        self.db.add(user)
        self.db.flush()
        return user

    def pay(self, code, number):
        owner = _resolve_order_referral_partner(self.db, user=self.buyer, invite_code=code)
        order = MemberOrder(order_no=number, user_pk=self.buyer.id, plan_id="yearly",
                            plan_name="yearly", amount=Decimal("100"), status="paid",
                            paid_at=datetime.now(), referral_partner_user_pk=owner, referral_captured=True)
        self.db.add(order)
        self.db.flush()
        settle_member_referral_commission(self.db, order=order)
        self.db.commit()
        return order

    def shares(self, order):
        return {r.split_to_user_pk: r.split_amount for r in self.db.scalars(
            select(SplitTransaction).where(SplitTransaction.order_no == order.order_no))}

    def test_latest_b_overrides_registration_a(self):
        order = self.pay("BBBB", "B_FIRST")
        self.assertEqual(self.shares(order), {self.city.id: Decimal("30"), self.b.id: Decimal("40")})

    def test_platform_first_stays_platform_on_renewal(self):
        self.assertEqual(self.shares(self.pay("", "PLATFORM")), {})
        self.assertEqual(self.shares(self.pay("AAAA", "RENEW")), {})

    def test_missing_code_does_not_use_registration(self):
        self.assertEqual(self.shares(self.pay(None, "MISSING")), {})

    def test_city_direct_gets_sixty(self):
        self.assertEqual(self.shares(self.pay("CITY", "CITY_FIRST")), {self.city.id: Decimal("60")})

    def test_renewal_keeps_first_partner_and_city(self):
        self.pay("AAAA", "FIRST")
        other = self.user("OTHR", "city_partner")
        self.a.city_partner_user_pk = other.id
        self.db.commit()
        order = self.pay("BBBB", "RENEW")
        self.assertEqual(self.shares(order), {self.city.id: Decimal("30"), self.a.id: Decimal("40")})
        self.assertEqual(self.a.city_partner_user_pk, other.id)

    def test_duplicate_callback_does_not_credit_twice(self):
        order = self.pay("AAAA", "ONCE")
        settle_member_referral_commission(self.db, order=order)
        self.db.commit()
        self.assertEqual(len(self.shares(order)), 2)
        from app.models import UserSettlement
        account = self.db.scalar(select(UserSettlement).where(UserSettlement.user_pk == self.a.id))
        self.assertEqual(account.available_balance, Decimal("40"))

    def test_circle_owner_referral_has_no_distribution(self):
        self.buyer.is_circle_owner = True
        ordinary = self.user("NORM", None)
        ordinary.is_circle_owner = True
        self.db.commit()
        self.assertEqual(self.shares(self.pay("NORM", "ORDINARY")), {})
        self.assertEqual(_resolve_service_fee_rate(self.db), Decimal("0.10"))

    def test_circle_join_hundred_pays_owner_ninety(self):
        from app.models import Circle, CircleJoinRequest
        from app.settlement.service import create_or_update_circle_join_split
        circle = Circle(circle_code="CIRCLE", owner_user_pk=self.a.id, name="Circle",
                        industry_label="test", description="test", cover_url="", avatar_url="")
        self.db.add(circle)
        join = CircleJoinRequest(user_pk=self.buyer.id, circle_code="CIRCLE",
                                 order_no="JOIN", amount=Decimal("100"))
        self.db.add(join)
        self.db.flush()
        row = create_or_update_circle_join_split(self.db, join_request=join, circle=circle)
        self.assertEqual(row.split_amount, Decimal("90"))
        self.assertEqual(row.platform_fee, Decimal("10"))

    def test_existing_first_paid_platform_cannot_be_claimed(self):
        first = MemberOrder(order_no="OLD", user_pk=self.buyer.id, plan_id="yearly",
                            plan_name="yearly", status="paid", paid_at=datetime(2025, 1, 1),
                            amount=Decimal("100"), referral_captured=True)
        self.db.add(first)
        self.db.commit()
        self.assertEqual(self.shares(self.pay("AAAA", "NEW")), {})

    def test_pending_order_uses_first_completed_conversion(self):
        pending = MemberOrder(order_no="PENDING", user_pk=self.buyer.id, plan_id="yearly",
                              plan_name="yearly", status="pending", amount=Decimal("100"),
                              referral_partner_user_pk=self.a.id, referral_captured=True)
        self.db.add(pending)
        self.db.commit()
        self.pay("BBBB", "FIRST_PAID")
        pending.status = "paid"
        pending.paid_at = datetime.now()
        settle_member_referral_commission(self.db, order=pending)
        self.db.commit()
        self.assertEqual(self.shares(pending), {self.city.id: Decimal("30"), self.b.id: Decimal("40")})


if __name__ == "__main__":
    unittest.main()
