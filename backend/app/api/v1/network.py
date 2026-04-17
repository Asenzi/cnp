from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.core.exceptions import BusinessException
from app.core.response import success_response
from app.crud import get_user_by_id
from app.network import (
    list_network_filter_options,
    list_network_recommendations,
    save_network_feedback,
    save_network_impressions,
)
from app.schemas.network import NetworkFeedbackRequest, NetworkImpressionsBatchRequest

router = APIRouter(prefix="/network", tags=["Network"])


@router.get("/ping", summary="Network module health check")
def network_ping():
    return success_response(message="network module ready")


def _require_current_user(db: Session, current_user_pk: int):
    user = get_user_by_id(db=db, user_id=current_user_pk)
    if user is None:
        raise BusinessException(message="User not found", code=4041, status_code=404)
    return user


@router.get("/recommendations", summary="Get network recommendations")
def get_network_recommendations(
    tab: str = Query(default="recommend"),
    request_id: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    keyword: str | None = Query(default=None),
    city_name: str | None = Query(default=None),
    industry_label: str | None = Query(default=None),
    domain: str | None = Query(default=None),
    exclude_user_ids: str | None = Query(default=None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    excluded_ids = [item.strip() for item in str(exclude_user_ids or "").split(",") if item and item.strip()]
    viewer = _require_current_user(db=db, current_user_pk=user_id)
    payload = list_network_recommendations(
        db=db,
        viewer=viewer,
        tab=tab,
        request_id=request_id,
        cursor=cursor,
        limit=limit,
        keyword=keyword,
        city_name=city_name,
        industry_label=industry_label,
        domain=domain,
        exclude_business_user_ids=excluded_ids,
    )
    return success_response(data=payload)


@router.get("/filters", summary="Get network filter options")
def get_network_filters(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    _require_current_user(db=db, current_user_pk=user_id)
    payload = list_network_filter_options(db=db)
    return success_response(data=payload)


@router.post("/impressions/batch", summary="Report network recommendation impressions")
def report_network_impressions_batch(
    payload: NetworkImpressionsBatchRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    viewer = _require_current_user(db=db, current_user_pk=user_id)
    recorded = save_network_impressions(
        db=db,
        viewer=viewer,
        target_business_user_ids=payload.target_user_ids,
        scene=payload.scene,
        tab=payload.tab,
        request_id=payload.request_id,
    )
    return success_response(
        data={"recorded": recorded},
        message="impressions recorded",
    )


@router.post("/feedback", summary="Report network recommendation feedback")
def report_network_feedback(
    payload: NetworkFeedbackRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    viewer = _require_current_user(db=db, current_user_pk=user_id)
    saved = save_network_feedback(
        db=db,
        viewer=viewer,
        target_business_user_id=payload.target_user_id,
        scene=payload.scene,
        tab=payload.tab,
        request_id=payload.request_id,
        event_type=payload.event_type,
        ext=payload.ext,
    )
    return success_response(
        data={"saved": bool(saved)},
        message="feedback recorded" if saved else "feedback ignored",
    )
