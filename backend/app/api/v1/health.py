from fastapi import APIRouter

from app.core.response import success_response

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="健康检查")
def health_check():
    return success_response(data={"status": "ok"})

