from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PaymentNotifyLog(Base):
    """支付回调通知日志表"""
    __tablename__ = "payment_notify_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="订单号",
    )
    notify_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="通知类型: wxpay, alipay等",
    )
    raw_body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="原始请求体",
    )
    result: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        index=True,
        comment="处理结果: success, failed",
    )
    result_message: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="结果消息",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
    )
