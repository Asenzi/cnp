"""订单统计服务"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.member_order import MemberOrder
from app.models.wallet_recharge_order import WalletRechargeOrder


def _utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def get_payment_statistics(
    db: Session,
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    """获取支付统计数据

    Args:
        db: 数据库会话
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        dict: 统计数据
    """
    now = _utc_now_naive()
    if end_date is None:
        end_date = now
    if start_date is None:
        start_date = now - timedelta(days=30)

    # 会员订单统计
    member_stmt = select(
        func.count(MemberOrder.id).label("count"),
        func.sum(MemberOrder.amount).label("total_amount"),
    ).where(
        and_(
            MemberOrder.status == "paid",
            MemberOrder.paid_at >= start_date,
            MemberOrder.paid_at < end_date,
        )
    )
    member_result = db.execute(member_stmt).first()
    member_count = int(member_result.count or 0) if member_result else 0
    member_amount = Decimal(str(member_result.total_amount or 0)) if member_result else Decimal("0.00")

    # 钱包充值统计
    wallet_stmt = select(
        func.count(WalletRechargeOrder.id).label("count"),
        func.sum(WalletRechargeOrder.amount).label("total_amount"),
    ).where(
        and_(
            WalletRechargeOrder.status == "paid",
            WalletRechargeOrder.paid_at >= start_date,
            WalletRechargeOrder.paid_at < end_date,
        )
    )
    wallet_result = db.execute(wallet_stmt).first()
    wallet_count = int(wallet_result.count or 0) if wallet_result else 0
    wallet_amount = Decimal(str(wallet_result.total_amount or 0)) if wallet_result else Decimal("0.00")

    # 总计
    total_count = member_count + wallet_count
    total_amount = (member_amount + wallet_amount).quantize(Decimal("0.01"))

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total": {
            "count": total_count,
            "amount": float(total_amount),
        },
        "member_orders": {
            "count": member_count,
            "amount": float(member_amount.quantize(Decimal("0.01"))),
        },
        "wallet_recharges": {
            "count": wallet_count,
            "amount": float(wallet_amount.quantize(Decimal("0.01"))),
        },
    }


def get_user_payment_summary(db: Session, *, user_pk: int) -> dict:
    """获取用户支付汇总信息

    Args:
        db: 数据库会话
        user_pk: 用户ID

    Returns:
        dict: 用户支付汇总
    """
    # 会员订单统计
    member_stmt = select(
        func.count(MemberOrder.id).label("count"),
        func.sum(MemberOrder.amount).label("total_amount"),
    ).where(
        and_(
            MemberOrder.user_pk == user_pk,
            MemberOrder.status == "paid",
        )
    )
    member_result = db.execute(member_stmt).first()
    member_count = int(member_result.count or 0) if member_result else 0
    member_amount = Decimal(str(member_result.total_amount or 0)) if member_result else Decimal("0.00")

    # 钱包充值统计
    wallet_stmt = select(
        func.count(WalletRechargeOrder.id).label("count"),
        func.sum(WalletRechargeOrder.amount).label("total_amount"),
    ).where(
        and_(
            WalletRechargeOrder.user_pk == user_pk,
            WalletRechargeOrder.status == "paid",
        )
    )
    wallet_result = db.execute(wallet_stmt).first()
    wallet_count = int(wallet_result.count or 0) if wallet_result else 0
    wallet_amount = Decimal(str(wallet_result.total_amount or 0)) if wallet_result else Decimal("0.00")

    # 总消费金额
    total_amount = (member_amount + wallet_amount).quantize(Decimal("0.01"))

    return {
        "user_pk": user_pk,
        "total_spent": float(total_amount),
        "member_orders": {
            "count": member_count,
            "amount": float(member_amount.quantize(Decimal("0.01"))),
        },
        "wallet_recharges": {
            "count": wallet_count,
            "amount": float(wallet_amount.quantize(Decimal("0.01"))),
        },
    }
