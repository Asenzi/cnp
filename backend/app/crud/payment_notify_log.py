"""支付回调日志CRUD操作"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.payment_notify_log import PaymentNotifyLog


def create_payment_notify_log(
    db: Session,
    *,
    order_no: str,
    notify_type: str,
    raw_body: str | None,
    result: str,
    result_message: str | None = None,
    commit: bool = False,
) -> PaymentNotifyLog:
    """创建支付回调通知日志

    Args:
        db: 数据库会话
        order_no: 订单号
        notify_type: 通知类型
        raw_body: 原始请求体
        result: 处理结果
        result_message: 结果消息
        commit: 是否立即提交

    Returns:
        PaymentNotifyLog: 日志对象
    """
    log = PaymentNotifyLog(
        order_no=str(order_no or "").strip() or "unknown",
        notify_type=str(notify_type or "").strip() or "unknown",
        raw_body=str(raw_body or "").strip()[:65535] if raw_body else None,  # 限制长度
        result=str(result or "").strip() or "unknown",
        result_message=str(result_message or "").strip()[:255] if result_message else None,
    )

    db.add(log)
    if commit:
        db.commit()
        db.refresh(log)
    return log
