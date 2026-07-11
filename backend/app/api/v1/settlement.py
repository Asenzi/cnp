from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user_id
from app.core.response import success_response
from app.schemas.settlement import WithdrawalCreateRequest
from app.settlement import (
    create_user_withdrawal,
    get_user_income_overview,
    list_user_settlement_ledgers,
    list_user_withdrawals,
)

router = APIRouter(prefix="/settlement", tags=["Settlement"])


@router.get("/income", summary="Get current user income overview")
def get_income_overview(
    limit: int = Query(default=20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    payload = get_user_income_overview(db=db, user_pk=user_id, limit=limit)
    return success_response(data=payload)


@router.get("/ledgers", summary="List current user settlement ledgers")
def get_settlement_ledgers(
    limit: int = Query(default=30, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    return success_response(data=list_user_settlement_ledgers(db=db, user_pk=user_id, limit=limit))


@router.get("/withdrawals", summary="List current user withdrawals")
def get_withdrawals(
    limit: int = Query(default=30, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    return success_response(data=list_user_withdrawals(db=db, user_pk=user_id, limit=limit))


@router.post("/withdrawals", summary="Create current user withdrawal")
def create_withdrawal(
    payload: WithdrawalCreateRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(db_session),
):
    data = create_user_withdrawal(
        db=db,
        user_pk=user_id,
        amount=payload.amount,
        withdraw_type=payload.withdraw_type,
        withdraw_account=payload.withdraw_account,
    )
    return success_response(data=data, message="提现申请已提交")
