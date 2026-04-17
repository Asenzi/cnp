from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.core.response import success_response
from app.points import claim_daily_check_in, get_points_center_overview, list_user_points_records

router = APIRouter(prefix="/points", tags=["Points"])


@router.get("/ping", summary="Points module ping")
def points_ping():
    return success_response(message="points module ready")


@router.get("/center", summary="Get points center overview")
def get_points_center(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = get_points_center_overview(db=db, user_pk=user_id)
    return success_response(data=payload)


@router.get("/records", summary="List points records")
def get_points_records(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = list_user_points_records(
        db=db,
        user_pk=user_id,
        cursor=cursor,
        limit=limit,
    )
    return success_response(data=payload)


@router.post("/check-in", summary="Claim daily check-in points")
def post_points_check_in(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = claim_daily_check_in(db=db, user_pk=user_id)
    return success_response(data=payload, message="签到成功")
