"""Payment domain module.

This package exposes a stable import surface while avoiding eager imports that
can create circular dependencies between payment and settlement modules.
"""

from importlib import import_module

_EXPORTS = {
    "auto_approve_due_circle_joins": ("app.payment.circle_join", "auto_approve_due_circle_joins"),
    "confirm_circle_join_payment": ("app.payment.circle_join", "confirm_circle_join_payment"),
    "create_circle_join_payment": ("app.payment.circle_join", "create_circle_join_payment"),
    "get_circle_join_order": ("app.payment.circle_join", "get_circle_join_order"),
    "consume_contact_package_view": ("app.payment.contact_package", "consume_contact_package_view"),
    "resolve_contact_package_snapshot": ("app.payment.contact_package", "resolve_contact_package_snapshot"),
    "CIRCLE_OWNER_PLAN_ID": ("app.payment.service", "CIRCLE_OWNER_PLAN_ID"),
    "confirm_member_order_payment": ("app.payment.service", "confirm_member_order_payment"),
    "ensure_default_payment_configs": ("app.payment.service", "ensure_default_payment_configs"),
    "get_circle_owner_overview": ("app.payment.service", "get_circle_owner_overview"),
    "get_member_order_status": ("app.payment.service", "get_member_order_status"),
    "get_member_center_overview": ("app.payment.service", "get_member_center_overview"),
    "handle_wechat_pay_notify_xml": ("app.payment.service", "handle_wechat_pay_notify_xml"),
    "list_member_orders": ("app.payment.service", "list_member_orders"),
    "resolve_member_snapshot": ("app.payment.service", "resolve_member_snapshot"),
    "subscribe_member_plan": ("app.payment.service", "subscribe_member_plan"),
}

__all__ = list(_EXPORTS.keys())


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
