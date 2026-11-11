"""Membership referral confirmation at real-name verification."""
import json
from sqlalchemy import select
from app.models.user import User
from app.models.member_order import MemberOrder
from app.core.exceptions import BusinessException
from app.partners import resolve_partner_invite_code


def has_real_name_verification(db, user):
    from app.models.user_real_name_profile import UserRealNameProfile
    return db.scalar(select(UserRealNameProfile.id).where(
        UserRealNameProfile.user_pk == user.id,
        UserRealNameProfile.verified_at.is_not(None),
    ).limit(1)) is not None


def paid_membership_orders(db, user):
    return db.scalars(select(MemberOrder).where(
        MemberOrder.user_pk == user.id, MemberOrder.status == "paid",
        MemberOrder.plan_id.in_(("yearly", "quarterly", "monthly")),
    ).order_by(MemberOrder.paid_at, MemberOrder.id)).all()


def current_invite_code(db, user):
    if user.member_referral_snapshot is not None:
        partner_id = json.loads(user.member_referral_snapshot).get("partner_id")
    else:
        orders = paid_membership_orders(db, user)
        partner_id = orders[0].referral_partner_user_pk if orders else None
    partner = db.get(User, partner_id) if partner_id else None
    return str(partner.partner_invite_code or "") if partner else ""


def validate_invite_code(db, user, code):
    if code is None:
        return
    if user.member_referral_snapshot is not None:
        if code != current_invite_code(db, user):
            raise BusinessException(message="首次会员归属已确认，不能再次修改邀请码", code=4370, status_code=409)
        return
    if code:
        partner = resolve_partner_invite_code(db, code)
        if partner is None or partner.id == user.id:
            raise BusinessException(message="邀请码无效，请填写有效的合作邀请码", code=4371, status_code=400)
        from app.payment.service import _resolve_order_referral_partner
        _resolve_order_referral_partner(db, user=user, invite_code=code)


def prepare_membership_referral(db, user, code):
    from app.payment.service import _resolve_order_referral_partner
    user = db.scalar(select(User).where(User.id == user.id).with_for_update().execution_options(populate_existing=True))
    validate_invite_code(db, user, code)
    orders = paid_membership_orders(db, user)
    if user.member_referral_snapshot is None and code is not None:
        partner_id = _resolve_order_referral_partner(db, user=user, invite_code=code)
        for order in orders:
            order.referral_partner_user_pk = partner_id
            order.referral_captured = True
        db.flush()
    return user, orders


def confirm_membership_referral(db, user, code):
    from app.settlement.service import settle_member_referral_commission
    if not has_real_name_verification(db, user):
        return
    user, orders = prepare_membership_referral(db, user, code)
    for order in orders:
        settle_member_referral_commission(db, order=order)
    db.commit()
