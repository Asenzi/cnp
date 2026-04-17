from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import func, select

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.crud import create_circle, create_user
from app.models.circle import Circle
from app.models.resource_post import ResourcePost
from app.models.user import User
from app.models.user_circle_membership import UserCircleMembership
from app.post import create_resource_post


@dataclass(frozen=True)
class IndustryOption:
    code: str
    label: str


INDUSTRIES: list[IndustryOption] = [
    IndustryOption("internet", "Internet"),
    IndustryOption("finance", "Finance"),
    IndustryOption("ai", "AI"),
    IndustryOption("marketing", "Marketing"),
    IndustryOption("manufacture", "Manufacture"),
    IndustryOption("education", "Education"),
    IndustryOption("health", "Healthcare"),
]

CITY_OPTIONS: list[tuple[str, str]] = [
    ("440100", "Guangzhou"),
    ("440300", "Shenzhen"),
    ("310100", "Shanghai"),
    ("110100", "Beijing"),
    ("330100", "Hangzhou"),
]

RESOURCE_TITLE_TEMPLATES: list[str] = [
    "Looking for strategic partners in {industry}",
    "Resource exchange for {industry} projects",
    "Need cooperation for regional expansion",
    "Open to cross-industry collaboration",
    "Seeking reliable B2B channel partners",
]

RESOURCE_DESC_TEMPLATES: list[str] = [
    "We are actively connecting with professionals and teams for long-term collaboration. "
    "If you have practical resources and clear goals, feel free to reach out.",
    "Current focus is on practical business cooperation. We value execution, communication "
    "efficiency, and sustainable outcomes.",
    "This post is for project matchmaking and resource sharing. We can discuss market "
    "expansion, delivery support, and strategic alignment.",
    "Looking for stable partners with relevant experience. Prefer practical and result-driven "
    "communication style for faster decision making.",
    "Open to cooperation in product, channel, operation, and growth. Please share your "
    "background and expected collaboration model.",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Bulk seed test accounts, circle memberships, and pure-text resource posts."
        )
    )
    parser.add_argument("--count", type=int, default=55, help="How many test accounts to create.")
    parser.add_argument("--seed", type=int, default=20260319, help="Random seed.")
    parser.add_argument("--password", type=str, default="123456", help="Default plaintext password.")
    parser.add_argument(
        "--nickname-prefix",
        type=str,
        default="test_user_",
        help="Nickname prefix for generated users.",
    )
    parser.add_argument(
        "--marker",
        type=str,
        default="seed_bulk_20260319",
        help="Marker stored in user intro for traceability.",
    )
    parser.add_argument("--min-circles", type=int, default=1, help="Min circles joined per user.")
    parser.add_argument("--max-circles", type=int, default=3, help="Max circles joined per user.")
    parser.add_argument("--min-posts", type=int, default=1, help="Min resource posts per user.")
    parser.add_argument("--max-posts", type=int, default=3, help="Max resource posts per user.")
    parser.add_argument(
        "--circle-pool-min",
        type=int,
        default=8,
        help="Ensure at least this many active circles exist before seeding.",
    )
    return parser.parse_args()


def _normalize_ranges(args: argparse.Namespace) -> None:
    args.count = max(int(args.count), 1)
    args.min_circles = max(int(args.min_circles), 1)
    args.max_circles = max(int(args.max_circles), args.min_circles)
    args.min_posts = max(int(args.min_posts), 1)
    args.max_posts = max(int(args.max_posts), args.min_posts)
    args.circle_pool_min = max(int(args.circle_pool_min), 3)


def _pick_industry() -> IndustryOption:
    return random.choice(INDUSTRIES)


def _pick_city() -> tuple[str, str]:
    return random.choice(CITY_OPTIONS)


def _generate_unique_phone(db, used_phones: set[str]) -> str:
    for _ in range(5000):
        candidate = f"1{random.randint(3, 9)}{random.randint(100000000, 999999999)}"
        if candidate in used_phones:
            continue
        existed = db.execute(select(User.id).where(User.phone == candidate)).scalar_one_or_none()
        if existed is None:
            used_phones.add(candidate)
            return candidate
    raise RuntimeError("Failed to generate unique phone number.")


def _get_or_create_seed_owner(db, marker: str, used_phones: set[str]) -> User:
    existing = db.execute(
        select(User).where(User.intro == f"{marker}:circle_owner").order_by(User.id.desc()).limit(1)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    industry = _pick_industry()
    owner = create_user(
        db=db,
        phone=_generate_unique_phone(db, used_phones),
        nickname="seed_circle_owner",
        intro=f"{marker}:circle_owner",
        industry_code=industry.code,
        industry_label=industry.label,
        show_contact=True,
        is_verified=True,
    )
    owner.password_hash = get_password_hash("123456")
    city_code, city_name = _pick_city()
    owner.city_code = city_code
    owner.city_name = city_name
    db.add(owner)
    db.commit()
    db.refresh(owner)
    return owner


def _list_active_circles(db) -> list[Circle]:
    return list(
        db.execute(
            select(Circle).where(Circle.status == "active").order_by(Circle.id.desc())
        ).scalars()
    )


def _ensure_circle_pool(
    db,
    *,
    pool_min: int,
    marker: str,
    used_phones: set[str],
) -> list[Circle]:
    circles = _list_active_circles(db)
    if len(circles) >= pool_min:
        return circles

    owner = _get_or_create_seed_owner(db, marker=marker, used_phones=used_phones)
    missing = pool_min - len(circles)
    now_suffix = datetime.now(UTC).strftime("%m%d%H%M%S")

    for idx in range(1, missing + 1):
        industry = _pick_industry()
        create_circle(
            db=db,
            owner_user_pk=owner.id,
            name=f"seed_circle_{now_suffix}_{idx}",
            industry_label=industry.label,
            description="Seeded circle for testing account/circle/resource workflows.",
            cover_url="/static/logo.png",
            avatar_url="/static/logo.png",
            join_type="free",
            join_price=0,
            rules_text="Seed test rule.",
            need_post_review=False,
        )

    return _list_active_circles(db)


def _count_user_active_memberships(db, user_pk: int) -> int:
    value = db.execute(
        select(func.count(UserCircleMembership.id)).where(
            UserCircleMembership.user_pk == user_pk,
            UserCircleMembership.is_active.is_(True),
        )
    ).scalar_one_or_none()
    return int(value or 0)


def _count_circle_active_members(db, circle_code: str) -> int:
    value = db.execute(
        select(func.count(UserCircleMembership.id)).where(
            UserCircleMembership.circle_code == circle_code,
            UserCircleMembership.is_active.is_(True),
        )
    ).scalar_one_or_none()
    return int(value or 0)


def _join_random_circles(
    db,
    *,
    user: User,
    circles: list[Circle],
    min_circles: int,
    max_circles: int,
) -> tuple[int, set[str]]:
    if not circles:
        return 0, set()

    upper = min(max_circles, len(circles))
    lower = min(min_circles, upper)
    join_count = random.randint(lower, upper)
    picked = random.sample(circles, k=join_count)

    touched_circle_codes: set[str] = set()
    for circle in picked:
        touched_circle_codes.add(circle.circle_code)
        membership = db.execute(
            select(UserCircleMembership).where(
                UserCircleMembership.user_pk == user.id,
                UserCircleMembership.circle_code == circle.circle_code,
            )
        ).scalar_one_or_none()
        if membership is None:
            membership = UserCircleMembership(
                user_pk=user.id,
                circle_code=circle.circle_code,
                is_active=True,
            )
            membership.created_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
            )
            db.add(membership)
        elif not membership.is_active:
            membership.is_active = True
            db.add(membership)

    db.commit()
    return join_count, touched_circle_codes


def _create_resource_posts(
    db,
    *,
    user: User,
    min_posts: int,
    max_posts: int,
) -> int:
    post_count = random.randint(min_posts, max_posts)
    for _ in range(post_count):
        industry = _pick_industry()
        title = random.choice(RESOURCE_TITLE_TEMPLATES).format(industry=industry.label)
        description = random.choice(RESOURCE_DESC_TEMPLATES)
        mode = random.choice(["cooperate", "resource"])
        create_resource_post(
            db=db,
            author=user,
            mode=mode,
            title=title,
            description=description,
            industry_label=industry.label,
            images=[],
        )
    return post_count


def _refresh_user_circle_count(db, user: User) -> None:
    user.circle_count = _count_user_active_memberships(db, user.id)
    db.add(user)
    db.commit()


def _refresh_circle_member_counts(db, circle_codes: set[str]) -> None:
    if not circle_codes:
        return
    rows = db.execute(select(Circle).where(Circle.circle_code.in_(list(circle_codes)))).scalars().all()
    for circle in rows:
        circle.member_count = _count_circle_active_members(db, circle.circle_code)
        db.add(circle)
    db.commit()


def seed_bulk_test_accounts(args: argparse.Namespace) -> None:
    random.seed(args.seed)

    used_phones: set[str] = set()
    created_users = 0
    total_joined_memberships = 0
    total_created_posts = 0
    touched_circle_codes: set[str] = set()

    with SessionLocal() as db:
        circles = _ensure_circle_pool(
            db,
            pool_min=args.circle_pool_min,
            marker=args.marker,
            used_phones=used_phones,
        )
        if not circles:
            raise RuntimeError("No active circles available after ensuring pool.")

        for i in range(1, args.count + 1):
            industry = _pick_industry()
            city_code, city_name = _pick_city()
            user = create_user(
                db=db,
                phone=_generate_unique_phone(db, used_phones),
                nickname=f"{args.nickname_prefix}{i:03d}",
                intro=args.marker,
                industry_code=industry.code,
                industry_label=industry.label,
                show_contact=True,
                is_verified=bool(random.randint(0, 1)),
            )
            user.password_hash = get_password_hash(args.password)
            user.city_code = city_code
            user.city_name = city_name
            db.add(user)
            db.commit()
            db.refresh(user)

            joined_count, joined_codes = _join_random_circles(
                db,
                user=user,
                circles=circles,
                min_circles=args.min_circles,
                max_circles=args.max_circles,
            )
            _refresh_user_circle_count(db, user)

            created_post_count = _create_resource_posts(
                db,
                user=user,
                min_posts=args.min_posts,
                max_posts=args.max_posts,
            )

            created_users += 1
            total_joined_memberships += joined_count
            total_created_posts += created_post_count
            touched_circle_codes.update(joined_codes)

            print(
                f"[{created_users}/{args.count}] "
                f"user={user.nickname} phone={user.phone} "
                f"joined={joined_count} posts={created_post_count}"
            )

        _refresh_circle_member_counts(db, touched_circle_codes)

        seeded_user_count = db.execute(
            select(func.count(User.id)).where(User.intro == args.marker)
        ).scalar_one_or_none()
        seeded_post_count = db.execute(
            select(func.count(ResourcePost.id))
            .join(User, User.id == ResourcePost.author_user_pk)
            .where(User.intro == args.marker)
        ).scalar_one_or_none()

    print("---- Seed completed ----")
    print(f"new_users_created={created_users}")
    print(f"new_memberships_created_or_activated={total_joined_memberships}")
    print(f"new_resource_posts_created={total_created_posts}")
    print(f"seed_marker={args.marker}")
    print(f"seed_users_total_now={int(seeded_user_count or 0)}")
    print(f"seed_posts_total_now={int(seeded_post_count or 0)}")


if __name__ == "__main__":
    parsed_args = parse_args()
    _normalize_ranges(parsed_args)
    seed_bulk_test_accounts(parsed_args)
