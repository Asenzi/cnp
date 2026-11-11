import json
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from app.api.v1.circle import get_managed_circle_members, refund_managed_circle_member, remove_managed_circle_member
from app.core.exceptions import BusinessException
from app.models import Base, Circle, CircleJoinRequest, User, UserCircleMembership


def run():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    owner = User(user_id='OWNER01', phone='18800000001', nickname='owner')
    member = User(user_id='MEMBER01', phone='18800000002', nickname='member')
    outsider = User(user_id='OTHER01', phone='18800000003', nickname='outsider')
    db.add_all([owner, member, outsider])
    db.flush()
    circle = Circle(circle_code='C123456789', owner_user_pk=owner.id, name='test circle',
        industry_label='technology', description='test', cover_url='https://example.com/a.png',
        avatar_url='https://example.com/b.png', join_type='paid', join_price=Decimal('9.80'), member_count=2)
    owner_membership = UserCircleMembership(user_pk=owner.id, circle_code=circle.circle_code, is_active=True)
    membership = UserCircleMembership(user_pk=member.id, circle_code=circle.circle_code, is_active=True)
    order = CircleJoinRequest(user_pk=member.id, circle_code=circle.circle_code,
        status='approved', amount=Decimal('9.80'), pay_channel='virtualpay', payment_status='paid')
    db.add_all([circle, owner_membership, membership, order])
    db.commit()

    request = Request({'type': 'http', 'scheme': 'https', 'server': ('example.com', 443), 'path': '/'})
    listing = get_managed_circle_members(circle.circle_code, request, offset=0, limit=20, user_id=owner.id, db=db)
    listing_data = json.loads(listing.body)['data']
    member_item = next(item for item in listing_data['items'] if item['user_id'] == member.user_id)
    assert member_item['join_amount'] == '9.80'
    assert member_item['can_refund'] is False
    try:
        get_managed_circle_members(circle.circle_code, request, offset=0, limit=20, user_id=outsider.id, db=db)
        assert False, 'non-owner must not see payment information'
    except BusinessException:
        db.rollback()

    for actor, target in ((outsider.id, member.user_id), (owner.id, owner.user_id)):
        try:
            remove_managed_circle_member(circle.circle_code, target, user_id=actor, db=db)
            assert False, 'operation must be rejected'
        except BusinessException:
            db.rollback()

    try:
        refund_managed_circle_member(circle.circle_code, member.user_id, user_id=owner.id, db=db)
        assert False, 'virtual payment must not be marked refunded'
    except BusinessException as exc:
        assert '不支持自动退费' in str(exc)
        db.rollback()
    assert db.scalar(select(CircleJoinRequest).where(CircleJoinRequest.id == order.id)).payment_status == 'paid'
    assert db.scalar(select(UserCircleMembership).where(UserCircleMembership.id == membership.id)).is_active is True

    remove_managed_circle_member(circle.circle_code, member.user_id, user_id=owner.id, db=db)
    assert db.scalar(select(UserCircleMembership).where(UserCircleMembership.id == membership.id)).is_active is False
    assert db.scalar(select(Circle).where(Circle.id == circle.id)).member_count == 1
    assert db.scalar(select(CircleJoinRequest).where(CircleJoinRequest.id == order.id)).payment_status == 'paid'


if __name__ == '__main__':
    run()
