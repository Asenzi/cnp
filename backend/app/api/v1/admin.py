import json
from datetime import datetime

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.admin.service import (
    get_admin_dashboard_overview,
    get_admin_profile_data,
    list_admin_circles,
    list_admin_recharge_orders,
    list_admin_resource_posts,
    list_admin_sys_configs,
    list_admin_users,
    login_admin,
    set_admin_circle_status,
    set_admin_resource_post_pin,
    set_admin_resource_post_status,
    set_admin_user_active,
    upsert_admin_sys_config,
)
from app.api.deps import db_session, get_current_admin_user, get_current_admin_user_from_header_or_query
from app.core.exceptions import BusinessException
from app.core.response import success_response
from app.crud import get_user_real_name_profile, get_user_verification_by_id
from app.models.admin_user import AdminUser
from app.review import list_admin_content_reviews, review_content_submission
from app.schemas.admin import (
    AdminCircleStatusPayload,
    AdminConfigUpsertPayload,
    AdminLoginRequest,
    AdminResourcePostPinPayload,
    AdminResourcePostStatusPayload,
    AdminUserStatusPayload,
)
from app.schemas.review import AdminContentReviewActionRequest
from app.schemas.verification import AdminVerificationReviewRequest
from app.verification.constants import VerificationStatus, VerificationType
from app.verification.files import guess_media_type, resolve_id_card_file_path
from app.verification.service import list_admin_verifications, review_verification_submission

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/ping", summary="Admin module ping")
def admin_ping(_: AdminUser = Depends(get_current_admin_user)):
    return success_response(message="admin module ready")


@router.post("/auth/login", summary="Admin login")
def admin_login(
    payload: AdminLoginRequest,
    db: Session = Depends(db_session),
):
    result = login_admin(
        db=db,
        username=payload.username,
        password=payload.password,
    )
    return success_response(data=result.model_dump(mode="json"))


@router.get("/auth/profile", summary="Get current admin profile")
def admin_profile(
    admin: AdminUser = Depends(get_current_admin_user),
):
    return success_response(data=get_admin_profile_data(admin))


@router.get("/dashboard/overview", summary="Get admin dashboard overview")
def admin_dashboard_overview(
    _: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(db_session),
):
    return success_response(data=get_admin_dashboard_overview(db=db))


@router.get("/users", summary="List users for admin")
def admin_list_users(
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    keyword: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    is_verified: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(db_session),
):
    return success_response(
        data=list_admin_users(
            db=db,
            created_from=created_from,
            created_to=created_to,
            is_verified=is_verified,
            keyword=keyword,
            is_active=is_active,
            page=page,
            page_size=page_size,
        )
    )


@router.post("/users/{user_pk}/status", summary="Enable or disable user")
def admin_update_user_status(
    user_pk: int = Path(..., ge=1),
    payload: AdminUserStatusPayload = ...,
    admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(db_session),
):
    return success_response(
        data=set_admin_user_active(
            db=db,
            user_pk=user_pk,
            is_active=payload.is_active,
            actor_admin_id=int(admin.id),
        ),
        message="用户状态已更新",
    )


@router.get("/circles", summary="List circles for admin")
def admin_list_circles(
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    keyword: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(db_session),
):
    return success_response(
        data=list_admin_circles(
            db=db,
            created_from=created_from,
            created_to=created_to,
            keyword=keyword,
            status=status,
            page=page,
            page_size=page_size,
        )
    )


@router.post("/circles/{circle_code}/status", summary="Update circle status")
def admin_update_circle_status(
    circle_code: str,
    payload: AdminCircleStatusPayload,
    _: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(db_session),
):
    return success_response(
        data=set_admin_circle_status(
            db=db,
            circle_code=circle_code,
            status=payload.status,
        ),
        message="圈子状态已更新",
    )


@router.get("/posts", summary="List resource posts for admin")
def admin_list_posts(
    keyword: str | None = Query(default=None),
    status: str | None = Query(default=None),
    mode: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(db_session),
):
    return success_response(
        data=list_admin_resource_posts(
            db=db,
            keyword=keyword,
            status=status,
            mode=mode,
            page=page,
            page_size=page_size,
        )
    )


@router.post("/posts/{post_code}/status", summary="Update resource post status")
def admin_update_post_status(
    post_code: str,
    payload: AdminResourcePostStatusPayload,
    _: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(db_session),
):
    return success_response(
        data=set_admin_resource_post_status(
            db=db,
            post_code=post_code,
            status=payload.status,
        ),
        message="资源状态已更新",
    )


@router.post("/posts/{post_code}/pin", summary="Update resource post pin state")
def admin_update_post_pin(
    post_code: str,
    payload: AdminResourcePostPinPayload,
    _: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(db_session),
):
    return success_response(
        data=set_admin_resource_post_pin(
            db=db,
            post_code=post_code,
            pinned=payload.pinned,
        ),
        message="资源置顶状态已更新",
    )


@router.get("/verifications", summary="List verification submissions for admin review")
def admin_list_verifications_view(
    status: VerificationStatus | None = Query(default=VerificationStatus.PENDING),
    verify_type: VerificationType | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(db_session),
):
    data = list_admin_verifications(
        db=db,
        status=status,
        verify_type=verify_type,
        page=page,
        page_size=page_size,
    )
    return success_response(data=data.model_dump(mode="json"))


@router.post("/verifications/{verification_id}/review", summary="Approve or reject verification")
def admin_review_verification(
    verification_id: int,
    payload: AdminVerificationReviewRequest,
    _: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(db_session),
):
    item = review_verification_submission(
        db=db,
        verification_id=verification_id,
        action=payload.action,
        reject_reason=payload.reject_reason,
    )
    return success_response(data=item.model_dump(mode="json"), message="审核处理完成")


@router.get(
    "/verifications/{verification_id}/real-name-files/{side}",
    summary="Preview real-name id-card file for admin review",
)
def admin_preview_real_name_file(
    verification_id: int,
    side: str = Path(..., pattern="^(front|back)$"),
    _: AdminUser = Depends(get_current_admin_user_from_header_or_query),
    db: Session = Depends(db_session),
):
    record = get_user_verification_by_id(db=db, verification_id=verification_id)
    if record is None:
        raise BusinessException(message="认证记录不存在", code=4404, status_code=404)
    if str(record.verify_type or "") != VerificationType.REAL_NAME.value:
        raise BusinessException(message="该认证类型不支持证件预览", code=4407, status_code=400)

    profile = get_user_real_name_profile(db=db, user_pk=int(record.user_pk))
    if profile is not None:
        file_url = str(profile.id_front_url if side == "front" else profile.id_back_url).strip()
    else:
        try:
            payload = json.loads(record.submit_payload_json or "{}")
        except (TypeError, ValueError):
            payload = {}
        key = "id_front_url" if side == "front" else "id_back_url"
        file_url = str(payload.get(key) or "").strip() if isinstance(payload, dict) else ""

    if not file_url:
        raise BusinessException(message="实名认证资料不存在", code=4346, status_code=404)

    file_path = resolve_id_card_file_path(file_url)
    return FileResponse(
        path=file_path,
        media_type=guess_media_type(file_path),
        filename=file_path.name,
        headers={"Cache-Control": "private, no-store"},
    )


@router.get("/content-reviews", summary="List content reviews for admin")
def admin_list_content_reviews_view(
    review_type: str | None = Query(default=None),
    status: str | None = Query(default="pending"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(db_session),
):
    data = list_admin_content_reviews(
        db=db,
        review_type=review_type,
        status=status,
        page=page,
        page_size=page_size,
    )
    return success_response(data=data.model_dump(mode="json"))


@router.post("/content-reviews/{review_id}/review", summary="Approve or reject content review")
def admin_review_content(
    review_id: int,
    payload: AdminContentReviewActionRequest,
    admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(db_session),
):
    item = review_content_submission(
        db=db,
        review_id=review_id,
        action=payload.action,
        reject_reason=payload.reject_reason,
        admin_id=int(admin.id),
    )
    return success_response(data=item.model_dump(mode="json"), message="审核处理完成")


@router.get("/recharges", summary="List wallet recharge orders for admin")
def admin_list_recharges(
    keyword: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(db_session),
):
    return success_response(
        data=list_admin_recharge_orders(
            db=db,
            keyword=keyword,
            status=status,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/configs", summary="List system configs for admin")
def admin_list_configs(
    keyword: str | None = Query(default=None),
    config_group: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    _: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(db_session),
):
    return success_response(
        data=list_admin_sys_configs(
            db=db,
            keyword=keyword,
            config_group=config_group,
            page=page,
            page_size=page_size,
        )
    )


@router.put("/configs/{config_key}", summary="Create or update system config")
def admin_upsert_config(
    config_key: str,
    payload: AdminConfigUpsertPayload,
    _: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(db_session),
):
    return success_response(
        data=upsert_admin_sys_config(
            db=db,
            config_key=config_key,
            config_value=payload.config_value,
            config_group=payload.config_group,
            description=payload.description,
        ),
        message="系统配置已保存",
    )
