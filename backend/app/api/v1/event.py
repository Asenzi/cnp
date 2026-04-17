from fastapi import APIRouter

from app.core.response import success_response

router = APIRouter(prefix="/event", tags=["Event"])


@router.get("/ping", summary="活动模块占位接口")
def event_ping():
    return success_response(message="event module placeholder")

