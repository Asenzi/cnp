"""Retry pending product-safety checks.

Default is dry-run. Use --apply to call providers and promote approved profile fields.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.api.v1.user import _assert_profile_image_safe, _assert_profile_text_safe  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.product_safety import ProductSafetyRetryTask  # noqa: E402
from app.models.user import User  # noqa: E402


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    with SessionLocal() as db:
        rows = list(
            db.execute(
                select(ProductSafetyRetryTask)
                .where(
                    ProductSafetyRetryTask.status == "pending",
                    (ProductSafetyRetryTask.next_retry_at.is_(None))
                    | (ProductSafetyRetryTask.next_retry_at <= _now()),
                )
                .order_by(ProductSafetyRetryTask.id.asc())
                .limit(max(int(args.limit or 100), 1))
            ).scalars()
        )
        print(f"pending={len(rows)} apply={bool(args.apply)}")
        if not args.apply:
            return 0

        for task in rows:
            user = db.get(User, int(task.user_pk)) if task.user_pk else None
            if user is None:
                task.status = "failed"
                task.last_error = "user missing"
                continue
            value = str(task.content_value or "").strip()
            try:
                if task.content_type == "avatar":
                    _assert_profile_image_safe(user=user, media_url=value)
                    user.avatar_url = value
                    user.avatar_review_status = "approved"
                    user.avatar_reviewed_at = _now()
                elif task.content_type in {"nickname", "intro"}:
                    _assert_profile_text_safe(user=user, fields={task.content_type: value})
                    setattr(user, task.content_type, value)
                    setattr(user, f"{task.content_type}_review_status", "approved")
                    setattr(user, f"{task.content_type}_reviewed_at", _now())
                task.status = "done"
            except Exception as exc:  # noqa: BLE001
                task.attempt_count = int(task.attempt_count or 0) + 1
                task.last_error = str(exc)[:255]
                if task.attempt_count >= 3:
                    task.status = "failed"
            db.add(task)
            db.add(user)
        db.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
