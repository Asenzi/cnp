from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from secrets import token_hex

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.circle import list_circle_discover_recommendations
from app.core.exceptions import BusinessException
from app.core.response import success_response
from app.crud import (
    count_circle_members,
    count_user_joined_circles,
    create_circle,
    get_circle_by_code,
    get_user_by_business_user_id,
    get_user_by_id,
    list_user_joined_circles,
)
from app.models.circle import Circle
from app.models.user import User
from app.post import list_circle_resource_posts, list_pending_circle_post_syncs, review_circle_post_sync
from app.review import submit_circle_update_review
from app.schemas.circle import (
    CircleCreateRequest,
    CircleData,
    CirclePostSyncReviewRequest,
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


def _serialize_circle(circle, owner, request: Request, db: Session) -> dict:
    member_count = count_circle_members(db=db, circle_code=circle.circle_code)
    payload = CircleData(
        circle_code=circle.circle_code,
        name=circle.name,
        industry_label=circle.industry_label,
        description=circle.description,
        cover_url=_to_public_file_url(circle.cover_url, request),
        avatar_url=_to_public_file_url(circle.avatar_url or circle.cover_url, request),
        join_type=circle.join_type,
        join_price=float(circle.join_price or 0),
        rules_text=circle.rules_text,
        need_post_review=bool(circle.need_post_review),
        member_count=member_count if member_count > 0 else int(circle.member_count or 0),
        post_count=int(circle.post_count or 0),
        owner=CircleOwnerData(
            user_id=owner.user_id,
            nickname=owner.nickname,
            avatar_url=_to_public_file_url(owner.avatar_url, request),
            is_verified=bool(owner.is_verified),
        ),
        created_at=circle.created_at,
    )
    return payload.model_dump(mode='json')


def _serialize_my_circle_item(circle, membership, request: Request) -> dict:
    payload = MyCircleItem(
        circle_code=circle.circle_code,
        name=circle.name,
        industry_label=circle.industry_label,
        description=circle.description,
        cover_url=_to_public_file_url(circle.cover_url, request),
        avatar_url=_to_public_file_url(circle.avatar_url or circle.cover_url, request),
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

    COVER_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{token_hex(4)}{suffix}"
    save_path = COVER_UPLOAD_DIR / file_name
    save_path.write_bytes(file_bytes)

    relative_url = f'/static/uploads/circle-covers/{file_name}'
    public_url = _to_public_file_url(relative_url, request)
    display_name = (file.filename or '圈子封面').strip() or '圈子封面'
    if len(display_name) > 128:
        display_name = display_name[:128]

    return success_response(
        data={
            'name': display_name,
            'path': relative_url,
            'url': public_url,
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
        raise BusinessException(message='完成实名认证后才可创建圈子并成为圈主', code=4357, status_code=403)

    join_type = payload.join_type.strip().lower()
    join_price = Decimal('0.00')
    if join_type == 'paid':
        if payload.join_price is None or Decimal(payload.join_price) <= 0:
            raise BusinessException(message='付费加入需要填写有效金额', code=4354, status_code=400)
        join_price = Decimal(payload.join_price).quantize(Decimal('0.01'))

    normalized_rules = (payload.rules_text or '').strip() or None

    try:
        circle = create_circle(
            db=db,
            owner_user_pk=owner.id,
            name=payload.name.strip(),
            industry_label=payload.industry_label.strip(),
            description=payload.description.strip(),
            cover_url=payload.cover_url.strip(),
            avatar_url=payload.avatar_url.strip(),
            join_type=join_type,
            join_price=join_price,
            rules_text=normalized_rules,
            need_post_review=bool(payload.need_post_review),
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
        updates['cover_url'] = payload.cover_url.strip()
    if payload.avatar_url is not None:
        updates['avatar_url'] = payload.avatar_url.strip()
    if payload.join_type is not None:
        updates['join_type'] = payload.join_type.strip().lower()
    if payload.join_price is not None:
        updates['join_price'] = Decimal(payload.join_price).quantize(Decimal('0.01'))
    if payload.rules_text is not None:
        updates['rules_text'] = payload.rules_text.strip() or None
    if payload.need_post_review is not None:
        updates['need_post_review'] = bool(payload.need_post_review)

    updates = {
        field_name: field_value
        for field_name, field_value in updates.items()
        if getattr(circle, field_name) != field_value
    }
    if not updates:
        raise BusinessException(message='没有可更新的字段', code=5703, status_code=400)

    join_type = str(updates.get('join_type') or circle.join_type or '').strip().lower()
    join_price = updates.get('join_price', circle.join_price)
    if join_type == 'paid' and Decimal(str(join_price or 0)).quantize(Decimal('0.01')) <= Decimal('0.00'):
        raise BusinessException(message='付费加入需要填写有效金额', code=4354, status_code=400)

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


@router.get('/me', summary='List circles joined by current user')
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


@router.get('/discover', summary='List discover circles')
def get_discover_circles(
    tab: str = 'recommend',
    offset: int = 0,
    limit: int = 20,
    keyword: str | None = None,
    city_name: str | None = None,
    industry_label: str | None = None,
    request_id: str | None = None,
    exclude_circle_codes: str | None = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
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
    return success_response(data=payload)


@router.get('/user/{target_user_id}', summary='List circles joined by target user')
def get_user_circles(
    target_user_id: str,
    request: Request,
    offset: int = 0,
    limit: int = 20,
    keyword: str | None = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
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


@router.get('/{circle_code}', summary='Get circle detail')
def get_circle_detail(
    circle_code: str,
    request: Request,
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

    return success_response(data=_serialize_circle(circle=circle, owner=owner, request=request, db=db))


@router.get('/{circle_code}/posts', summary='List approved circle resource posts')
def get_circle_posts(
    circle_code: str,
    request: Request,
    cursor: str | None = None,
    limit: int = 20,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
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


@router.get('/{circle_code}/post-syncs/pending', summary='List pending circle post sync requests')
def get_pending_circle_post_syncs(
    circle_code: str,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    items = list_pending_circle_post_syncs(
        db=db,
        circle_code=circle_code,
        owner_user_pk=user_id,
    )
    for item in items:
        images = item.get('images') if isinstance(item, dict) else []
        item['images'] = [_to_public_file_url(str(image), request) for image in images]
        author = item.get('author') if isinstance(item.get('author'), dict) else {}
        item['author'] = {
            **author,
            'avatar_url': _to_public_file_url(str(author.get('avatar_url') or ''), request),
        }
    return success_response(data={'items': items, 'total': len(items)})


@router.post('/{circle_code}/post-syncs/{sync_id}/review', summary='Review pending circle post sync')
def post_circle_sync_review(
    circle_code: str,
    sync_id: int,
    payload: CirclePostSyncReviewRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    result = review_circle_post_sync(
        db=db,
        circle_code=circle_code,
        sync_id=sync_id,
        owner_user_pk=user_id,
        action=payload.action,
        reject_reason=payload.reject_reason,
    )
    return success_response(data=result, message='审核处理成功')
