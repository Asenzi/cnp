from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id, get_optional_current_user_id
from app.api.v1.user import _assert_profile_image_safe, _assert_profile_text_safe
from app.circle import list_circle_discover_recommendations
from app.core.asset_urls import is_local_only_asset_url, normalize_persisted_asset_url, sanitize_public_asset_url
from app.core.config import settings
from app.core.exceptions import BusinessException
from app.core.profile_display import public_avatar_url, public_nickname
from app.core.response import success_response
from app.core.storage import upload_public_asset
from app.crud import (
    count_circle_members,
    count_user_joined_circles,
    create_circle,
    get_circle_by_code,
    get_user_by_business_user_id,
    get_user_by_id,
    list_circle_members,
    list_user_joined_circles,
)
from app.models.circle import Circle
from app.models.circle_interest import CircleInterest
from app.models.circle_join_request import CircleJoinRequest
from app.models.notification import Notification
from app.models.user import User
from app.models.user_circle_membership import UserCircleMembership
from app.payment import confirm_circle_join_payment, create_circle_join_payment, get_circle_join_order
from app.payment.circle_join import approve_join_request, normalize_circle_join_price_tier, refund_circle_join_payment
from app.post import list_circle_resource_posts
from app.review import submit_circle_update_review
from app.schemas.circle import (
    CircleCreateRequest,
    CircleData,
    CircleJoinPaymentConfirm,
    CircleJoinRequestCreate,
    CircleUpdateRequest,
    CircleOwnerData,
    MyCircleItem,
    MyCircleListData,
)

router = APIRouter(prefix='/circle', tags=['Circle'])

STATIC_DIR = Path(__file__).resolve().parents[3] / 'static'
COVER_UPLOAD_DIR = STATIC_DIR / 'uploads' / 'circle-covers'

MAX_COVER_FILE_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_COVER_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
CONTENT_TYPE_EXTENSION_MAP = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/webp': '.webp',
}
def _require_current_user(db: Session, current_user_pk: int):
    user = get_user_by_id(db=db, user_id=current_user_pk)
    if user is None:
        raise BusinessException(message='用户不存在', code=4041, status_code=404)
    return user


def _require_circle_owner(db: Session, *, circle_code: str, current_user_pk: int) -> tuple[Circle, User]:
    circle = get_circle_by_code(db=db, circle_code=circle_code)
    if circle is None:
        raise BusinessException(message='圈子不存在', code=4043, status_code=404)
    owner = _require_current_user(db=db, current_user_pk=current_user_pk)
    if int(circle.owner_user_pk) != int(owner.id):
        raise BusinessException(message='仅圈主可修改圈子资料', code=4356, status_code=403)
    return circle, owner


def _to_public_file_url(file_url: str, request: Request) -> str:
    if file_url.startswith(('http://', 'https://', 'data:image/', 'wxfile://', 'file://')):
        return file_url
    if file_url.startswith('/static/'):
        return f"{str(request.base_url).rstrip('/')}{file_url}"
    return file_url


def _resolve_circle_asset_urls(cover_url: str | None, avatar_url: str | None, request: Request) -> tuple[str, str]:
    default_asset_url = str(settings.DEFAULT_AVATAR_URL or '/static/logo.png').strip() or '/static/logo.png'
    safe_cover_url = sanitize_public_asset_url(cover_url)
    safe_avatar_url = sanitize_public_asset_url(avatar_url)
    resolved_cover = safe_cover_url or safe_avatar_url or default_asset_url
    resolved_avatar = safe_avatar_url or safe_cover_url or default_asset_url
    return _to_public_file_url(resolved_cover, request), _to_public_file_url(resolved_avatar, request)


def _to_public_circle_asset_url(asset_url: str | None, request: Request) -> str:
    normalized = sanitize_public_asset_url(asset_url, '')
    if not normalized or normalized == settings.DEFAULT_AVATAR_URL:
        return ''
    return _to_public_file_url(normalized, request)


def _normalize_circle_asset_url(asset_url: str, *, request: Request, field_label: str) -> str:
    return normalize_persisted_asset_url(asset_url, request=request, field_label=field_label)


def _circle_collection_counts(db: Session, circle_pks: list[int]) -> dict[int, int]:
    normalized_pks = sorted({int(circle_pk) for circle_pk in circle_pks if circle_pk})
    if not normalized_pks:
        return {}
    rows = db.execute(
        select(CircleInterest.circle_pk, func.count(CircleInterest.id))
        .where(CircleInterest.circle_pk.in_(normalized_pks))
        .group_by(CircleInterest.circle_pk)
    ).all()
    return {int(circle_pk): int(count or 0) for circle_pk, count in rows}


def _serialize_circle(
    circle,
    owner,
    request: Request,
    db: Session,
    current_user_pk: int | None = None,
) -> dict:
    member_count = count_circle_members(db=db, circle_code=circle.circle_code)
    collect_count = _circle_collection_counts(db, [int(circle.id)]).get(int(circle.id), 0)
    cover_url, avatar_url = _resolve_circle_asset_urls(circle.cover_url, circle.avatar_url or circle.cover_url, request)
    is_interested = False
    is_joined = False
    join_request = None
    if current_user_pk is not None:
        is_interested = db.scalar(
            select(CircleInterest.id).where(
                CircleInterest.user_pk == current_user_pk,
                CircleInterest.circle_pk == circle.id,
            )
        ) is not None
        is_joined = db.scalar(
            select(UserCircleMembership.id).where(
                UserCircleMembership.user_pk == current_user_pk,
                UserCircleMembership.circle_code == circle.circle_code,
                UserCircleMembership.is_active.is_(True),
            )
        ) is not None
        join_request = db.scalar(
            select(CircleJoinRequest).where(
                CircleJoinRequest.user_pk == current_user_pk,
                CircleJoinRequest.circle_code == circle.circle_code,
            )
        )
    payload = CircleData(
        circle_code=circle.circle_code,
        name=circle.name,
        industry_label=circle.industry_label,
        description=circle.description,
        cover_url=cover_url,
        avatar_url=avatar_url,
        join_type=circle.join_type,
        join_price=float(circle.join_price or 0),
        rules_text=circle.rules_text,
        member_count=member_count if member_count > 0 else int(circle.member_count or 0),
        post_count=int(circle.post_count or 0),
        owner=CircleOwnerData(
            user_id=owner.user_id,
            nickname=public_nickname(owner),
            avatar_url=_to_public_file_url(public_avatar_url(owner), request),
            is_verified=bool(owner.is_verified),
        ),
        is_interested=is_interested,
        interested=is_interested,
        is_collected=is_interested,
        collected=is_interested,
        collect_count=collect_count,
        favorite_count=collect_count,
        is_joined=is_joined,
        join_request_status=str(join_request.status or "") if join_request else "",
        join_payment_status=str(join_request.payment_status or "") if join_request else "",
        join_auto_approve_at=join_request.auto_approve_at if join_request else None,
        created_at=circle.created_at,
    )
    return payload.model_dump(mode='json')


def _serialize_my_circle_item(circle, membership, request: Request) -> dict:
    cover_url, avatar_url = _resolve_circle_asset_urls(circle.cover_url, circle.avatar_url or circle.cover_url, request)
    payload = MyCircleItem(
        circle_code=circle.circle_code,
        name=circle.name,
        industry_label=circle.industry_label,
        description=circle.description,
        cover_url=cover_url,
        avatar_url=avatar_url,
        join_type=circle.join_type,
        member_count=int(circle.member_count or 0),
        post_count=int(circle.post_count or 0),
        is_owner=bool(circle.owner_user_pk == membership.user_pk),
        joined_at=membership.created_at,
        last_active_at=circle.last_active_at,
    )
    return payload.model_dump(mode='json')


@router.post('/cover-file', summary='Upload circle cover image file')
async def upload_circle_cover_file(
    request: Request,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)

    content_type = (file.content_type or '').lower().strip()
    if content_type not in ALLOWED_COVER_CONTENT_TYPES:
        raise BusinessException(message='圈子封面仅支持 JPG/PNG/WEBP', code=4351, status_code=400)

    file_bytes = await file.read()
    if not file_bytes:
        raise BusinessException(message='上传文件为空', code=4352, status_code=400)

    if len(file_bytes) > MAX_COVER_FILE_SIZE_BYTES:
        raise BusinessException(message='圈子封面不能超过 10MB', code=4353, status_code=400)

    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in {'.jpg', '.jpeg', '.png', '.webp'}:
        suffix = CONTENT_TYPE_EXTENSION_MAP.get(content_type, '.jpg')

    stored = upload_public_asset(
        prefix='uploads/circle-covers',
        file_bytes=file_bytes,
        suffix=suffix,
        content_type=content_type,
        request=request,
    )
    display_name = (file.filename or '圈子封面').strip() or '圈子封面'
    if len(display_name) > 128:
        display_name = display_name[:128]

    return success_response(
        data={
            'name': display_name,
            'path': stored.path,
            'url': stored.url,
            'size': len(file_bytes),
        },
        message='圈子封面上传成功',
    )


@router.post('', summary='Create circle')
def create_new_circle(
    payload: CircleCreateRequest,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    owner = _require_current_user(db=db, current_user_pk=user_id)
    if not bool(owner.is_verified):
        raise BusinessException(message='完成实名认证后才可创建圈子', code=4357, status_code=403)
    if not bool(owner.is_circle_owner):
        raise BusinessException(message='开通永久圈主身份后才可创建圈子', code=4358, status_code=403)

    join_type = payload.join_type.strip().lower()
    join_price = Decimal('0.00')
    if join_type == 'paid':
        if payload.join_price is None:
            raise BusinessException(message='付费加入需要填写有效金额', code=4354, status_code=400)
        join_price = normalize_circle_join_price_tier(payload.join_price)

    normalized_rules = (payload.rules_text or '').strip() or None
    cover_url = _normalize_circle_asset_url(payload.cover_url, request=request, field_label='圈子封面')
    avatar_url = _normalize_circle_asset_url(payload.avatar_url, request=request, field_label='圈子头像')
    _assert_profile_text_safe(
        user=owner,
        fields={
            "name": payload.name,
            "industry_label": payload.industry_label,
            "description": payload.description,
            "rules_text": payload.rules_text,
        },
    )
    _assert_profile_image_safe(user=owner, media_url=_to_public_file_url(cover_url, request))
    _assert_profile_image_safe(user=owner, media_url=_to_public_file_url(avatar_url, request))

    try:
        circle = create_circle(
            db=db,
            owner_user_pk=owner.id,
            name=payload.name.strip(),
            industry_label=payload.industry_label.strip(),
            description=payload.description.strip(),
            cover_url=cover_url,
            avatar_url=avatar_url,
            join_type=join_type,
            join_price=join_price,
            rules_text=normalized_rules,
            need_post_review=False,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise BusinessException(message='创建圈子失败，请稍后重试', code=5351, status_code=500) from exc

    return success_response(
        data=_serialize_circle(circle=circle, owner=owner, request=request, db=db),
        message='圈子创建成功',
    )


@router.patch('/{circle_code}', summary='Update circle info')
def update_circle_info(
    circle_code: str,
    payload: CircleUpdateRequest,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    normalized_circle_code = str(circle_code or '').strip()
    if not normalized_circle_code:
        raise BusinessException(message='圈子编号不能为空', code=4355, status_code=400)

    circle, owner = _require_circle_owner(
        db=db,
        circle_code=normalized_circle_code,
        current_user_pk=user_id,
    )

    updates: dict[str, object] = {}
    if payload.name is not None:
        updates['name'] = payload.name.strip()
    if payload.industry_label is not None:
        updates['industry_label'] = payload.industry_label.strip()
    if payload.description is not None:
        updates['description'] = payload.description.strip()
    if payload.cover_url is not None:
        updates['cover_url'] = _normalize_circle_asset_url(
            payload.cover_url,
            request=request,
            field_label='圈子封面',
        )
    if payload.avatar_url is not None:
        updates['avatar_url'] = _normalize_circle_asset_url(
            payload.avatar_url,
            request=request,
            field_label='圈子头像',
        )
    if payload.join_type is not None:
        updates['join_type'] = payload.join_type.strip().lower()
    if payload.join_price is not None:
        updates['join_price'] = Decimal(payload.join_price).quantize(Decimal('0.01'))
    if payload.rules_text is not None:
        updates['rules_text'] = payload.rules_text.strip() or None

    updates = {
        field_name: field_value
        for field_name, field_value in updates.items()
        if getattr(circle, field_name) != field_value
    }
    if not updates:
        raise BusinessException(message='没有可更新的字段', code=5703, status_code=400)
    _assert_profile_text_safe(
        user=owner,
        fields={
            key: value
            for key, value in updates.items()
            if key in {"name", "industry_label", "description", "rules_text"}
        },
    )
    if "cover_url" in updates:
        _assert_profile_image_safe(user=owner, media_url=_to_public_file_url(str(updates["cover_url"] or ""), request))
    if "avatar_url" in updates:
        _assert_profile_image_safe(user=owner, media_url=_to_public_file_url(str(updates["avatar_url"] or ""), request))

    join_type = str(updates.get('join_type') or circle.join_type or '').strip().lower()
    join_price = updates.get('join_price', circle.join_price)
    if join_type == 'paid':
        join_price = normalize_circle_join_price_tier(join_price)
        if updates.get('join_price') != join_price:
            updates['join_price'] = join_price
    elif 'join_price' in updates:
        updates['join_price'] = Decimal('0.00')

    try:
        review_result = submit_circle_update_review(
            db=db,
            circle=circle,
            owner=owner,
            updates=updates,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise BusinessException(message='圈子资料更新失败，请稍后重试', code=5352, status_code=500) from exc

    payload_data = _serialize_circle(circle=circle, owner=owner, request=request, db=db)
    payload_data['_review'] = review_result['review']
    review_required = bool(review_result['review']['review_required'])
    return success_response(
        data=payload_data,
        message='圈子资料已提交审核' if review_required else '圈子资料更新成功',
    )


@router.get('/me', summary='List circles joined by current user, excluding owned circles')
def get_my_circles(
    request: Request,
    offset: int = 0,
    limit: int = 20,
    keyword: str | None = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    current_user = _require_current_user(db=db, current_user_pk=user_id)

    safe_offset = max(int(offset or 0), 0)
    safe_limit = min(max(int(limit or 20), 1), 50)
    normalized_keyword = str(keyword or '').strip() or None

    rows = list_user_joined_circles(
        db=db,
        user_pk=current_user.id,
        offset=safe_offset,
        limit=safe_limit,
        keyword=normalized_keyword,
    )
    total = count_user_joined_circles(
        db=db,
        user_pk=current_user.id,
        keyword=normalized_keyword,
    )

    items = [
        _serialize_my_circle_item(circle=circle, membership=membership, request=request)
        for circle, membership in rows
    ]
    payload = MyCircleListData(
        items=items,
        total=int(total),
        offset=safe_offset,
        limit=safe_limit,
        has_more=(safe_offset + len(items)) < int(total),
    ).model_dump(mode='json')
    return success_response(data=payload)


@router.get('/owned', summary='List circles owned by current user')
def get_owned_circles(
    request: Request,
    offset: int = 0,
    limit: int = 20,
    keyword: str | None = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    owner = _require_current_user(db=db, current_user_pk=user_id)
    safe_offset = max(int(offset or 0), 0)
    safe_limit = min(max(int(limit or 20), 1), 50)
    normalized_keyword = str(keyword or '').strip()

    filters = [Circle.owner_user_pk == int(owner.id)]
    if normalized_keyword:
        pattern = f'%{normalized_keyword}%'
        filters.append(
            Circle.name.like(pattern)
            | Circle.circle_code.like(pattern)
            | Circle.industry_label.like(pattern)
        )

    total = db.scalar(
        select(func.count(Circle.id)).where(*filters)
    ) or 0
    circles = db.execute(
        select(Circle)
        .where(*filters)
        .order_by(Circle.updated_at.desc(), Circle.id.desc())
        .offset(safe_offset)
        .limit(safe_limit)
    ).scalars().all()

    circle_codes = [str(circle.circle_code) for circle in circles]
    join_counts: dict[str, int] = {}
    if circle_codes:
        join_counts = {
            str(code): int(count or 0)
            for code, count in db.execute(
                select(CircleJoinRequest.circle_code, func.count(CircleJoinRequest.id))
                .where(
                    CircleJoinRequest.circle_code.in_(circle_codes),
                    CircleJoinRequest.status == 'pending',
                    CircleJoinRequest.payment_status == 'paid',
                )
                .group_by(CircleJoinRequest.circle_code)
            ).all()
        }

    collection_counts = _circle_collection_counts(
        db,
        [int(circle.id) for circle in circles],
    )
    items = []
    for circle in circles:
        cover_url, avatar_url = _resolve_circle_asset_urls(
            circle.cover_url,
            circle.avatar_url or circle.cover_url,
            request,
        )
        items.append({
            'circle_code': circle.circle_code,
            'name': circle.name,
            'industry_label': circle.industry_label,
            'description': circle.description,
            'cover_url': cover_url,
            'avatar_url': avatar_url,
            'join_type': circle.join_type,
            'join_price': float(circle.join_price or 0),
            'status': circle.status,
            'member_count': count_circle_members(db=db, circle_code=circle.circle_code),
            'post_count': int(circle.post_count or 0),
            'collect_count': collection_counts.get(int(circle.id), 0),
            'pending_join_count': join_counts.get(str(circle.circle_code), 0),
            'last_active_at': circle.last_active_at.isoformat() if circle.last_active_at else None,
            'created_at': circle.created_at.isoformat() if circle.created_at else None,
            'updated_at': circle.updated_at.isoformat() if circle.updated_at else None,
        })

    return success_response(
        data={
            'items': items,
            'total': int(total),
            'offset': safe_offset,
            'limit': safe_limit,
            'has_more': safe_offset + len(items) < int(total),
        }
    )


@router.get('/discover', summary='List discover circles')
def get_discover_circles(
    request: Request,
    tab: str = 'recommend',
    offset: int = 0,
    limit: int = 20,
    keyword: str | None = None,
    city_name: str | None = None,
    industry_label: str | None = None,
    request_id: str | None = None,
    exclude_circle_codes: str | None = None,
    user_id: int | None = Depends(get_optional_current_user_id),
    db: Session = Depends(db_session),
):
    if user_id is None:
        payload = _list_public_discover_circles(
            db=db,
            request=request,
            tab=tab,
            offset=offset,
            limit=limit,
            keyword=keyword,
            city_name=city_name,
            industry_label=industry_label,
        )
        return success_response(data=payload)

    current_user = _require_current_user(db=db, current_user_pk=user_id)
    normalized_exclude_circle_codes = [
        str(item or '').strip()
        for item in str(exclude_circle_codes or '').split(',')
        if str(item or '').strip()
    ]
    payload = list_circle_discover_recommendations(
        db=db,
        viewer=current_user,
        tab=tab,
        offset=offset,
        limit=limit,
        keyword=keyword,
        city_name=city_name,
        industry_label=industry_label,
        request_id=request_id,
        exclude_circle_codes=normalized_exclude_circle_codes,
    )
    items = payload.get('items') if isinstance(payload, dict) else None
    if isinstance(items, list):
        circle_codes = [
            str(item.get('circle_code') or '').strip()
            for item in items
            if isinstance(item, dict) and str(item.get('circle_code') or '').strip()
        ]
        interested_circle_codes = set()
        circle_pk_by_code: dict[str, int] = {}
        collection_counts: dict[int, int] = {}
        if circle_codes:
            circle_rows = db.execute(
                select(Circle.id, Circle.circle_code).where(Circle.circle_code.in_(circle_codes))
            ).all()
            circle_pk_by_code = {
                str(code or '').strip(): int(circle_pk)
                for circle_pk, code in circle_rows
                if str(code or '').strip()
            }
            collection_counts = _circle_collection_counts(db, list(circle_pk_by_code.values()))
            interested_circle_codes = {
                str(code or '').strip()
                for code in db.execute(
                    select(Circle.circle_code)
                    .join(CircleInterest, CircleInterest.circle_pk == Circle.id)
                    .where(
                        CircleInterest.user_pk == int(user_id),
                        Circle.circle_code.in_(circle_codes),
                    )
                ).scalars().all()
            }
        for item in items:
            if not isinstance(item, dict):
                continue
            raw_cover_url = str(item.get('cover_url') or '').strip()
            raw_avatar_url = str(item.get('avatar_url') or '').strip()
            raw_owner_avatar_url = str(item.get('owner_avatar_url') or '').strip()
            item['cover_url'] = _to_public_circle_asset_url(raw_cover_url, request)
            item['avatar_url'] = _to_public_circle_asset_url(raw_avatar_url, request)
            item['owner_avatar_url'] = _to_public_file_url(raw_owner_avatar_url, request) if raw_owner_avatar_url else ''
            circle_code = str(item.get('circle_code') or '').strip()
            circle_pk = circle_pk_by_code.get(circle_code)
            collect_count = collection_counts.get(circle_pk, 0) if circle_pk is not None else 0
            is_interested = circle_code in interested_circle_codes
            item['interested'] = is_interested
            item['is_interested'] = is_interested
            item['collected'] = is_interested
            item['is_collected'] = is_interested
            item['collect_count'] = collect_count
            item['favorite_count'] = collect_count
    return success_response(data=payload)


@router.get('/user/{target_user_id}', summary='List circles joined by target user')
def get_user_circles(
    target_user_id: str,
    request: Request,
    offset: int = 0,
    limit: int = 20,
    keyword: str | None = None,
    user_id: int | None = Depends(get_optional_current_user_id),
    db: Session = Depends(db_session),
):
    if user_id is not None:
        _require_current_user(db=db, current_user_pk=user_id)

    normalized_target_user_id = str(target_user_id or '').strip()
    if len(normalized_target_user_id) != 8:
        raise BusinessException(message='目标用户ID格式无效', code=4233, status_code=400)

    target_user = get_user_by_business_user_id(db=db, business_user_id=normalized_target_user_id)
    if target_user is None or not bool(target_user.is_active):
        raise BusinessException(message='目标用户不存在', code=4042, status_code=404)

    safe_offset = max(int(offset or 0), 0)
    safe_limit = min(max(int(limit or 20), 1), 50)
    normalized_keyword = str(keyword or '').strip() or None

    rows = list_user_joined_circles(
        db=db,
        user_pk=int(target_user.id),
        offset=safe_offset,
        limit=safe_limit,
        keyword=normalized_keyword,
    )
    total = count_user_joined_circles(
        db=db,
        user_pk=int(target_user.id),
        keyword=normalized_keyword,
    )

    items = [
        _serialize_my_circle_item(circle=circle, membership=membership, request=request)
        for circle, membership in rows
    ]
    payload = MyCircleListData(
        items=items,
        total=int(total),
        offset=safe_offset,
        limit=safe_limit,
        has_more=(safe_offset + len(items)) < int(total),
    ).model_dump(mode='json')
    return success_response(data=payload)


def _parse_offset_cursor(cursor: str | None) -> int:
    try:
        return max(int(str(cursor or '').strip() or '0'), 0)
    except (TypeError, ValueError):
        return 0


def _serialize_public_discover_circle(circle: Circle, owner: User, request: Request) -> dict:
    cover_url, avatar_url = _resolve_circle_asset_urls(circle.cover_url, circle.avatar_url or circle.cover_url, request)
    member_count = int(circle.member_count or 0)
    post_count = int(circle.post_count or 0)
    return {
        'circle_code': circle.circle_code,
        'circleCode': circle.circle_code,
        'id': circle.circle_code,
        'name': circle.name,
        'title': circle.name,
        'industry_label': circle.industry_label,
        'industryLabel': circle.industry_label,
        'description': circle.description,
        'cover_url': cover_url,
        'coverImage': cover_url,
        'avatar_url': avatar_url,
        'join_type': circle.join_type,
        'join_price': float(circle.join_price or 0),
        'member_count': member_count,
        'members': member_count,
        'post_count': post_count,
        'posts': post_count,
        'owner_user_id': str(owner.user_id or '').strip(),
        'owner_nickname': public_nickname(owner),
        'owner_avatar_url': _to_public_file_url(public_avatar_url(owner), request),
        'owner_city_name': str(owner.city_name or '').strip(),
        'owner_is_verified': bool(owner.is_verified),
        'ownerVerified': bool(owner.is_verified),
        'is_joined': False,
        'interested': False,
        'is_interested': False,
        'collected': False,
        'is_collected': False,
        'collect_count': 0,
        'favorite_count': 0,
        'reason_tags': [],
        'last_active_at': circle.last_active_at.isoformat() if circle.last_active_at else None,
        'created_at': circle.created_at.isoformat() if circle.created_at else None,
    }


def _list_public_discover_circles(
    db: Session,
    *,
    request: Request,
    tab: str,
    offset: int,
    limit: int,
    keyword: str | None,
    city_name: str | None,
    industry_label: str | None,
) -> dict:
    safe_offset = max(int(offset or 0), 0)
    safe_limit = min(max(int(limit or 20), 1), 50)
    safe_tab = str(tab or 'recommend').strip()
    safe_keyword = str(keyword or '').strip()
    safe_city = str(city_name or '').strip()
    safe_industry = str(industry_label or '').strip()
    conditions = [
        Circle.status == 'active',
        User.is_active.is_(True),
    ]
    if safe_industry:
        conditions.append(Circle.industry_label == safe_industry)
    if safe_city and safe_city != '全国':
        conditions.append(User.city_name == safe_city)
    if safe_keyword:
        like_keyword = f'%{safe_keyword}%'
        conditions.append(
            (Circle.name.like(like_keyword))
            | (Circle.description.like(like_keyword))
            | (Circle.industry_label.like(like_keyword))
            | (User.nickname.like(like_keyword))
        )
    order_by = (
        Circle.created_at.desc(),
        Circle.id.desc(),
    ) if safe_tab == 'latest' else (
        Circle.last_active_at.desc(),
        Circle.post_count.desc(),
        Circle.member_count.desc(),
        Circle.created_at.desc(),
        Circle.id.desc(),
    )
    rows = db.execute(
        select(Circle, User)
        .join(User, User.id == Circle.owner_user_pk)
        .where(*conditions)
        .order_by(*order_by)
        .offset(safe_offset)
        .limit(safe_limit + 1)
    ).all()
    page_rows = rows[:safe_limit]
    has_more = len(rows) > safe_limit
    collection_counts = _circle_collection_counts(db, [int(circle.id) for circle, _owner in page_rows])
    items = []
    for circle, owner in page_rows:
        item = _serialize_public_discover_circle(circle=circle, owner=owner, request=request)
        collect_count = collection_counts.get(int(circle.id), 0)
        item['collect_count'] = collect_count
        item['favorite_count'] = collect_count
        items.append(item)
    return {
        'items': items,
        'total': safe_offset + len(page_rows) + (1 if has_more else 0),
        'offset': safe_offset,
        'limit': safe_limit,
        'has_more': has_more,
        'tab': safe_tab,
        'city_name': safe_city or None,
        'request_id': '',
    }


def _serialize_interested_circle(
    circle: Circle,
    owner: User | None,
    interest: CircleInterest,
    request: Request,
    collect_count: int,
) -> dict:
    cover_url, avatar_url = _resolve_circle_asset_urls(circle.cover_url, circle.avatar_url or circle.cover_url, request)
    item = {
        'circle_code': circle.circle_code,
        'circleCode': circle.circle_code,
        'id': circle.circle_code,
        'name': circle.name,
        'title': circle.name,
        'industry_label': circle.industry_label,
        'industryLabel': circle.industry_label,
        'description': circle.description,
        'cover_url': cover_url,
        'coverImage': cover_url,
        'avatar_url': avatar_url,
        'join_type': circle.join_type,
        'join_price': float(circle.join_price or 0),
        'member_count': int(circle.member_count or 0),
        'members': int(circle.member_count or 0),
        'post_count': int(circle.post_count or 0),
        'posts': int(circle.post_count or 0),
        'owner_user_id': str(owner.user_id or '').strip() if owner else '',
        'owner_nickname': public_nickname(owner) if owner else '',
        'owner_avatar_url': _to_public_file_url(public_avatar_url(owner), request) if owner else '',
        'owner_city_name': str(owner.city_name or '').strip() if owner else '',
        'owner_is_verified': bool(owner.is_verified) if owner else False,
        'ownerVerified': bool(owner.is_verified) if owner else False,
        'interested': True,
        'is_interested': True,
        'collected': True,
        'is_collected': True,
        'collect_count': int(collect_count or 0),
        'favorite_count': int(collect_count or 0),
        'created_at': circle.created_at.isoformat() if circle.created_at else None,
        'interested_at': interest.created_at.isoformat() if interest.created_at else None,
    }
    return item


def _list_circle_collections(
    request: Request,
    cursor: str | None,
    limit: int,
    user_id: int,
    db: Session,
):
    _require_current_user(db=db, current_user_pk=user_id)
    offset = _parse_offset_cursor(cursor)
    safe_limit = min(max(int(limit or 20), 1), 50)
    rows = db.execute(
        select(CircleInterest, Circle, User)
        .join(Circle, Circle.id == CircleInterest.circle_pk)
        .outerjoin(User, User.id == Circle.owner_user_pk)
        .where(
            CircleInterest.user_pk == int(user_id),
            Circle.status == 'active',
        )
        .order_by(CircleInterest.created_at.desc(), CircleInterest.id.desc())
        .offset(offset)
        .limit(safe_limit + 1)
    ).all()
    page_rows = rows[:safe_limit]
    has_more = len(rows) > safe_limit
    collection_counts = _circle_collection_counts(
        db,
        [int(circle.id) for _interest, circle, _owner in page_rows],
    )
    return success_response(
        data={
            'items': [
                _serialize_interested_circle(
                    circle=circle,
                    owner=owner,
                    interest=interest,
                    request=request,
                    collect_count=collection_counts.get(int(circle.id), 0),
                )
                for interest, circle, owner in page_rows
            ],
            'next_cursor': str(offset + len(page_rows)) if has_more else '',
            'has_more': has_more,
        }
    )


@router.get('/interests', summary='List collected circles')
def get_circle_interests(
    request: Request,
    cursor: str | None = None,
    limit: int = 20,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    return _list_circle_collections(request, cursor, limit, user_id, db)


@router.get('/collections', summary='List collected circles')
def get_circle_collections(
    request: Request,
    cursor: str | None = None,
    limit: int = 20,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    return _list_circle_collections(request, cursor, limit, user_id, db)


def _toggle_circle_collection(
    circle_code: str,
    desired: bool | None,
    user_id: int,
    db: Session,
):
    viewer = _require_current_user(db=db, current_user_pk=user_id)
    normalized_code = str(circle_code or '').strip()
    circle = get_circle_by_code(db=db, circle_code=normalized_code)
    if circle is None or str(circle.status or '') != 'active':
        raise BusinessException(message='圈子不存在', code=4043, status_code=404)

    existing = db.execute(
        select(CircleInterest).where(
            CircleInterest.user_pk == int(user_id),
            CircleInterest.circle_pk == int(circle.id),
        )
    ).scalar_one_or_none()
    should_collect = bool(desired) if desired is not None else existing is None
    if should_collect:
        if existing is None:
            db.add(CircleInterest(user_pk=int(user_id), circle_pk=int(circle.id)))
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
        is_collected = True
    else:
        if existing is not None:
            db.delete(existing)
            db.commit()
        is_collected = False

    collect_count = _circle_collection_counts(db, [int(circle.id)]).get(int(circle.id), 0)

    if (
        is_collected
        and existing is None
        and int(circle.owner_user_pk) != int(user_id)
    ):
        db.add(
            Notification(
                user_pk=int(circle.owner_user_pk),
                actor_user_pk=int(viewer.id),
                type='collection',
                title='圈子被收藏',
                content=(
                    f'{public_nickname(viewer)}'
                    f'收藏了你的圈子“{str(circle.name or "未命名圈子").strip()}”'
                ),
                link_type='circle',
                link_id=str(circle.circle_code or '').strip(),
                is_read=False,
            )
        )
        db.commit()

    return success_response(
        data={
            'is_collected': is_collected,
            'collected': is_collected,
            'is_interested': is_collected,
            'interested': is_collected,
            'collect_count': collect_count,
            'favorite_count': collect_count,
        },
        message='已收藏' if is_collected else '已取消收藏',
    )


@router.post('/{circle_code}/interest/toggle', summary='Toggle circle collect status')
def toggle_circle_interest(
    circle_code: str,
    desired: bool | None = Query(default=None, description='Desired collect state'),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    return _toggle_circle_collection(circle_code, desired, user_id, db)


@router.post('/{circle_code}/collect/toggle', summary='Toggle circle collect status')
def toggle_circle_collect(
    circle_code: str,
    desired: bool | None = Query(default=None, description='Desired collect state'),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    return _toggle_circle_collection(circle_code, desired, user_id, db)


@router.get('/join-requests', summary='Get sent and received circle join requests')
def get_join_requests(
    request: Request,
    status: str | None = Query(None, description="Filter by status: pending, approved, rejected, cancelled"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    """获取当前用户发出的申请，以及作为圈主收到的申请。"""
    user = _require_current_user(db=db, current_user_pk=user_id)
    query = (
        select(CircleJoinRequest, Circle, User)
        .join(Circle, Circle.circle_code == CircleJoinRequest.circle_code)
        .join(User, User.id == CircleJoinRequest.user_pk)
        .where(
            (CircleJoinRequest.user_pk == int(user.id))
            | (Circle.owner_user_pk == int(user.id))
        )
    )
    if status:
        query = query.where(CircleJoinRequest.status == status)
    rows = db.execute(
        query
        .order_by(CircleJoinRequest.updated_at.desc(), CircleJoinRequest.id.desc())
        .offset(offset)
        .limit(limit + 1)
    ).all()
    page_rows = rows[:limit]
    has_more = len(rows) > limit
    items = []
    for req, circle, applicant in page_rows:
        perspective = 'applicant' if int(req.user_pk) == int(user.id) else 'owner'
        circle_cover_url, circle_avatar_url = _resolve_circle_asset_urls(
            circle.cover_url,
            circle.avatar_url or circle.cover_url,
            request,
        )
        items.append({
            'id': req.id,
            'perspective': perspective,
            'user_pk': req.user_pk,
            'circle_code': req.circle_code,
            'status': req.status,
            'message': req.message,
            'reject_reason': req.reject_reason,
            'amount': float(req.amount or 0),
            'pay_channel': req.pay_channel,
            'payment_status': req.payment_status,
            'refund_status': req.refund_status,
            'auto_approve_at': req.auto_approve_at.isoformat() if req.auto_approve_at else None,
            'reviewed_at': req.reviewed_at.isoformat() if req.reviewed_at else None,
            'created_at': req.created_at.isoformat(),
            'updated_at': req.updated_at.isoformat(),
            'user': {
                'user_id': applicant.user_id,
                'nickname': public_nickname(applicant),
                'avatar_url': _to_public_file_url(public_avatar_url(applicant), request),
            },
            'circle': {
                'circle_code': circle.circle_code,
                'name': circle.name,
                'cover_url': circle_cover_url,
                'avatar_url': circle_avatar_url,
                'owner_user_pk': circle.owner_user_pk,
            },
        })

    return success_response(
        data={
            'items': items,
            'total': offset + len(items) + (1 if has_more else 0),
            'offset': offset,
            'limit': limit,
            'has_more': has_more,
        }
    )


@router.post('/{circle_code}/join-request', summary='Pay and submit circle join request')
def submit_join_request(
    circle_code: str,
    payload: CircleJoinRequestCreate,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    data = create_circle_join_payment(
        db=db,
        user_pk=user_id,
        circle_code=str(circle_code or "").strip(),
        message=str(payload.message or "").strip(),
        pay_channel=payload.pay_channel,
        client_ip=request.client.host if request.client else None,
        base_url=str(request.base_url).rstrip("/"),
    )
    message = "请完成小程序虚拟支付" if data.get("action") == "virtualpay_required" else "入圈申请已提交"
    return success_response(data=data, message=message)


@router.post('/join-orders/{order_no}/confirm', summary='Confirm circle join payment')
def confirm_join_order(
    order_no: str,
    payload: CircleJoinPaymentConfirm,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    return success_response(
        data=confirm_circle_join_payment(
            db=db,
            user_pk=user_id,
            order_no=order_no,
            transaction_id=payload.transaction_id,
        ),
        message="入圈费用支付成功",
    )


@router.get('/join-orders/{order_no}', summary='Get circle join payment status')
def get_join_order_status(
    order_no: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    return success_response(data=get_circle_join_order(db=db, user_pk=user_id, order_no=order_no))


@router.post('/join-requests/{request_id}/cancel', summary='Cancel own circle join request')
def cancel_join_request(
    request_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    user = _require_current_user(db=db, current_user_pk=user_id)
    join_request = db.execute(
        select(CircleJoinRequest)
        .where(CircleJoinRequest.id == request_id)
        .with_for_update()
    ).scalar_one_or_none()
    if join_request is None:
        raise BusinessException(message='申请不存在', code=4046, status_code=404)
    if int(join_request.user_pk) != int(user.id):
        raise BusinessException(message='只能取消自己提交的申请', code=4393, status_code=403)
    if str(join_request.status) != 'pending':
        raise BusinessException(message='当前申请已处理，无法取消', code=4394, status_code=409)
    if str(join_request.payment_status) == 'pending':
        raise BusinessException(message='支付结果确认中，暂时无法取消', code=4395, status_code=409)

    circle = db.scalar(select(Circle).where(Circle.circle_code == join_request.circle_code))
    if circle is None:
        raise BusinessException(message='圈子不存在', code=4043, status_code=404)

    was_paid = str(join_request.payment_status) == 'paid'
    if was_paid:
        refund_circle_join_payment(
            db,
            join_request=join_request,
            circle=circle,
            reason='用户主动取消入圈申请',
        )
    join_request.status = 'cancelled'
    join_request.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    join_request.reject_reason = '用户主动取消'
    join_request.auto_approve_at = None
    db.add(
        Notification(
            user_pk=int(circle.owner_user_pk),
            type='circle',
            title='入圈申请已取消',
            content=f'{public_nickname(user)}已取消加入“{circle.name}”的申请',
            link_type='circle',
            link_id=str(circle.circle_code),
            is_read=False,
        )
    )
    db.commit()
    return success_response(
        data={
            'request_id': int(join_request.id),
            'status': str(join_request.status),
            'payment_status': str(join_request.payment_status),
            'refund_status': str(join_request.refund_status),
        },
        message='申请已取消，已支付费用已原路退回' if was_paid else '申请已取消',
    )


@router.post('/join-requests/{request_id}/review', summary='Review circle join request')
def review_join_request(
    request_id: int,
    payload: dict,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    """审批圈子加入申请"""
    action = payload.get('action', '')
    reject_reason = payload.get('reject_reason')

    user = _require_current_user(db=db, current_user_pk=user_id)

    # 获取申请
    join_request = db.execute(
        select(CircleJoinRequest)
        .where(CircleJoinRequest.id == request_id)
        .with_for_update()
    ).scalar_one_or_none()

    if not join_request:
        raise BusinessException(code=404, message='申请不存在')

    # 检查圈子是否属于当前用户
    circle = db.execute(
        select(Circle).where(Circle.circle_code == join_request.circle_code)
    ).scalar_one_or_none()

    if not circle or circle.owner_user_pk != user.id:
        raise BusinessException(code=403, message='无权操作此申请')

    # 检查申请状态
    if join_request.status != 'pending':
        raise BusinessException(code=400, message='该申请已处理')

    if action == 'approve':
        approve_join_request(db, join_request=join_request, circle=circle)
    elif action == 'reject':
        refund_circle_join_payment(db, join_request=join_request, circle=circle)
        join_request.status = 'rejected'
        join_request.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        join_request.reject_reason = reject_reason or '不符合圈子要求'

    else:
        raise BusinessException(code=400, message='无效的操作')

    approved = action == 'approve'
    db.add(
        Notification(
            user_pk=int(join_request.user_pk),
            type='circle',
            title='入圈申请已通过' if approved else '入圈申请已拒绝',
            content=(
                f'您加入“{circle.name}”的申请已通过'
                if approved
                else f'您加入“{circle.name}”的申请已被拒绝'
            ),
            link_type='circle',
            link_id=str(circle.circle_code),
            is_read=False,
        )
    )
    db.commit()

    # Notify the applicant after the owner reviews the join request.
    from app.tasks.wechat import send_circle_join_result

    send_circle_join_result.delay(
        user_id=int(join_request.user_pk),
        circle_name=str(circle.name or "").strip(),
        circle_code=str(circle.circle_code or "").strip(),
        approved=approved,
        reason=reject_reason if action == "reject" else None,
    )

    return success_response(message=f'申请已{"通过" if action == "approve" else "拒绝"}')


@router.get('/{circle_code}', summary='Get circle detail')
def get_circle_detail(
    circle_code: str,
    request: Request,
    user_id: int | None = Depends(get_optional_current_user_id),
    db: Session = Depends(db_session),
):
    normalized_code = (circle_code or '').strip()
    if not normalized_code:
        raise BusinessException(message='圈子编号不能为空', code=4355, status_code=400)

    circle = get_circle_by_code(db=db, circle_code=normalized_code)
    if circle is None:
        raise BusinessException(message='圈子不存在', code=4043, status_code=404)

    owner = get_user_by_id(db=db, user_id=circle.owner_user_pk)
    if owner is None:
        raise BusinessException(message='圈主不存在', code=4044, status_code=404)

    return success_response(
        data=_serialize_circle(
            circle=circle,
            owner=owner,
            request=request,
            db=db,
            current_user_pk=user_id,
        )
    )


@router.get('/{circle_code}/posts', summary='List approved circle resource posts')
def get_circle_posts(
    circle_code: str,
    request: Request,
    cursor: str | None = None,
    limit: int = 20,
    user_id: int | None = Depends(get_optional_current_user_id),
    db: Session = Depends(db_session),
):
    if user_id is not None:
        _require_current_user(db=db, current_user_pk=user_id)
    payload = list_circle_resource_posts(
        db=db,
        viewer_user_pk=user_id,
        circle_code=circle_code,
        cursor=cursor,
        limit=limit,
    )
    items = payload.get('items') if isinstance(payload.get('items'), list) else []
    for item in items:
        images = item.get('images') if isinstance(item, dict) else []
        if isinstance(item, dict):
            item['images'] = [_to_public_file_url(str(image), request) for image in images]
            author = item.get('author') if isinstance(item.get('author'), dict) else {}
            item['author'] = {
                **author,
                'avatar_url': _to_public_file_url(str(author.get('avatar_url') or ''), request),
            }
    return success_response(data=payload)


@router.get('/{circle_code}/members', summary='List circle members')
def get_circle_members(
    circle_code: str,
    request: Request,
    offset: int = 0,
    limit: int = 20,
    user_id: int | None = Depends(get_optional_current_user_id),
    db: Session = Depends(db_session),
):
    if user_id is not None:
        _require_current_user(db=db, current_user_pk=user_id)

    normalized_code = (circle_code or '').strip()
    if not normalized_code:
        raise BusinessException(message='圈子编号不能为空', code=4355, status_code=400)

    circle = get_circle_by_code(db=db, circle_code=normalized_code)
    if circle is None:
        raise BusinessException(message='圈子不存在', code=4043, status_code=404)

    safe_offset = max(offset, 0)
    safe_limit = min(max(limit, 1), 50)

    members = list_circle_members(
        db=db,
        circle_code=normalized_code,
        offset=safe_offset,
        limit=safe_limit,
    )

    total = count_circle_members(db=db, circle_code=normalized_code)

    items = []
    for user, membership in members:
        items.append({
            'user_id': user.user_id,
            'nickname': public_nickname(user),
            'avatar_url': _to_public_file_url(public_avatar_url(user), request),
            'is_verified': bool(user.is_verified),
            'company_name': user.company_name,
            'job_title': user.job_title,
            'joined_at': membership.created_at.isoformat() if membership.created_at else None,
        })

    return success_response(data={
        'items': items,
        'total': total,
        'offset': safe_offset,
        'limit': safe_limit,
    })

