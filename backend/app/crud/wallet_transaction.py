"""钱包交易流水CRUD操作"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException
from app.models.wallet_transaction import WalletTransaction


def create_wallet_transaction(
    db: Session,
    *,
    user_pk: int,
    change_amount: Decimal,
    balance_after: Decimal,
    biz_type: str,
    biz_key: str,
    title: str,
    remark: str | None = None,
    commit: bool = False,
) -> WalletTransaction:
    """创建钱包交易流水记录

    Args:
        db: 数据库会话
        user_pk: 用户ID
        change_amount: 变动金额（正数收入，负数支出）
        balance_after: 交易后余额
        biz_type: 业务类型
        biz_key: 业务唯一标识
        title: 交易标题
        remark: 备注信息
        commit: 是否立即提交

    Returns:
        WalletTransaction: 交易记录对象

    Raises:
        BusinessException: 当交易记录重复时抛出异常
    """
    transaction = WalletTransaction(
        user_pk=int(user_pk),
        change_amount=Decimal(str(change_amount)).quantize(Decimal("0.01")),
        balance_after=Decimal(str(balance_after)).quantize(Decimal("0.01")),
        biz_type=str(biz_type).strip(),
        biz_key=str(biz_key).strip(),
        title=str(title).strip(),
        remark=str(remark or "").strip() or None,
    )

    try:
        db.add(transaction)
        if commit:
            db.commit()
            db.refresh(transaction)
        return transaction
    except IntegrityError as exc:
        db.rollback()
        raise BusinessException(
            message="交易记录已存在，请勿重复操作",
            code=4590,
            status_code=400,
        ) from exc
