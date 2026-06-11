from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.payment.circle_join import auto_approve_due_circle_joins


@celery_app.task(name="app.tasks.circle_join.auto_approve_circle_joins")
def auto_approve_circle_joins() -> dict:
    with SessionLocal() as db:
        count = auto_approve_due_circle_joins(db)
    return {"approved_count": count}
