from pydantic import BaseModel
from fastapi import APIRouter, Depends, Header
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.core.exceptions import BusinessException
from app.core.response import success_response
from app.crud import get_user_by_business_user_id, get_user_by_id
from app.product_safety import report_content
from app.product_safety.tencent_cloud import moderate_with_tencent_cloud
from app.schemas.product_safety import ContentReportRequest
from app.core.config import settings

router = APIRouter(prefix="/product-safety", tags=["ProductSafety"])

REPORTABLE_TYPES = {"user", "avatar", "profile", "post", "comment", "message", "circle"}


class ImsModerationRequest(BaseModel):
    content_type: str
    value: str
    user_id: str | None = None
    openid: str | None = None


@router.post("/reports", summary="Report unsafe content")
def create_content_report(
    payload: ContentReportRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    reporter = get_user_by_id(db=db, user_id=user_id)
    if reporter is None:
        raise BusinessException(message="用户不存在", code=4041, status_code=404)

    target_type = str(payload.target_type or "").strip().lower()
    target_id = str(payload.target_id or "").strip()
    if target_type not in REPORTABLE_TYPES:
        raise BusinessException(message="举报类型无效", code=4281, status_code=400)
    if not target_id:
        raise BusinessException(message="举报对象不能为空", code=4282, status_code=400)

    target_user = None
    if target_type in {"user", "avatar", "profile"}:
        target_user = get_user_by_business_user_id(db=db, business_user_id=target_id)
        if target_user is None:
            raise BusinessException(message="举报用户不存在", code=4042, status_code=404)
        if int(target_user.id) == int(reporter.id):
            raise BusinessException(message="不能举报自己", code=4283, status_code=400)

    try:
        report = report_content(
            db=db,
            reporter=reporter,
            target_user=target_user,
            target_type=target_type,
            target_id=target_id,
            reason=payload.reason,
        )
        db.commit()
        db.refresh(report)
    except SQLAlchemyError as exc:
        db.rollback()
        raise BusinessException(message="举报失败，请稍后重试", code=5281, status_code=500) from exc

    return success_response(
        data={"report_id": int(report.id), "status": str(report.status or "pending")},
        message="举报已提交",
    )


@router.post("/ims/tencent", summary="Tencent Cloud IMS/TMS adapter")
def moderate_with_tencent_adapter(
    payload: ImsModerationRequest,
    authorization: str | None = Header(default=None),
):
    expected_token = str(settings.PRODUCT_SAFETY_IMS_TOKEN or "").strip()
    provided_token = str(authorization or "").removeprefix("Bearer ").strip()
    if not expected_token or provided_token != expected_token:
        raise BusinessException(message="内容审核服务鉴权失败", code=4277, status_code=401)

    return moderate_with_tencent_cloud(
        content_type=str(payload.content_type or "").strip().lower(),
        value=str(payload.value or "").strip(),
        user_id=str(payload.user_id or "").strip(),
    )
