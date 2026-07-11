"""Mark historical unreviewed avatars as pending/default-visible.

Default is dry-run. Use --apply only after reviewing the affected count.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes")
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()

    session = SessionLocal()
    try:
        rows = list(
            session.execute(
                select(User)
                .where(
                    User.avatar_url != settings.DEFAULT_AVATAR_URL,
                    User.avatar_review_status != "approved",
                )
                .order_by(User.id.asc())
                .limit(max(int(args.limit or 1000), 1))
            ).scalars()
        )
        print(f"affected={len(rows)} apply={bool(args.apply)}")
        if not args.apply:
            return 0
        for user in rows:
            user.avatar_review_status = "pending"
            user.avatar_candidate_url = user.avatar_url
            session.add(user)
        session.commit()
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
