import json

from sqlalchemy import create_engine, text

from app.core.config import settings


DEFAULT_ASSET_URL = str(settings.DEFAULT_AVATAR_URL or "/static/logo.png").strip() or "/static/logo.png"


def is_local_temp_url(value: str | None) -> bool:
    normalized = str(value or "").strip().lower()
    return bool(normalized) and (
        normalized.startswith("http://tmp/")
        or normalized.startswith("https://tmp/")
        or normalized.startswith("wxfile://")
        or normalized.startswith("file://")
        or normalized.startswith("blob:")
        or normalized.startswith("data:image/")
    )


def is_usable_asset_url(value: str | None) -> bool:
    normalized = str(value or "").strip()
    return bool(normalized) and not is_local_temp_url(normalized)


def resolve_circle_asset(*, current: str | None, peer: str | None, owner_avatar: str | None) -> str:
    if is_usable_asset_url(current):
        return str(current).strip()
    if is_usable_asset_url(peer):
        return str(peer).strip()
    if is_usable_asset_url(owner_avatar) and str(owner_avatar).strip() != DEFAULT_ASSET_URL:
        return str(owner_avatar).strip()
    return DEFAULT_ASSET_URL


def clean_resource_images(raw_images: str | None) -> tuple[str | None, bool]:
    if not raw_images:
        return raw_images, False
    try:
        parsed = json.loads(raw_images)
    except json.JSONDecodeError:
        return raw_images, False
    if not isinstance(parsed, list):
        return raw_images, False

    cleaned = []
    changed = False
    for item in parsed:
        value = str(item or "").strip()
        if not value:
            changed = True
            continue
        if is_local_temp_url(value):
            changed = True
            continue
        cleaned.append(value[:255])

    if not changed:
        return raw_images, False
    return (json.dumps(cleaned, ensure_ascii=False) if cleaned else None), True


def fix_circles(conn) -> None:
    rows = conn.execute(
        text(
            """
            SELECT c.id, c.circle_code, c.name, c.cover_url, c.avatar_url, u.avatar_url AS owner_avatar_url
            FROM circles c
            LEFT JOIN users u ON u.id = c.owner_user_pk
            ORDER BY c.id DESC
            """
        )
    ).mappings().all()

    bad_rows = [
        row for row in rows
        if is_local_temp_url(row.get("cover_url")) or is_local_temp_url(row.get("avatar_url"))
    ]
    print(f"circle_bad_rows={len(bad_rows)}")
    for row in bad_rows[:20]:
        print({
            "circle_code": row.get("circle_code"),
            "name": row.get("name"),
            "cover_url": row.get("cover_url"),
            "avatar_url": row.get("avatar_url"),
        })

    updated = 0
    for row in bad_rows:
        cover_url = resolve_circle_asset(
            current=row.get("cover_url"),
            peer=row.get("avatar_url"),
            owner_avatar=row.get("owner_avatar_url"),
        )
        avatar_url = resolve_circle_asset(
            current=row.get("avatar_url"),
            peer=row.get("cover_url"),
            owner_avatar=row.get("owner_avatar_url"),
        )
        result = conn.execute(
            text(
                """
                UPDATE circles
                SET cover_url = :cover_url, avatar_url = :avatar_url
                WHERE id = :id
                """
            ),
            {
                "id": row.get("id"),
                "cover_url": cover_url,
                "avatar_url": avatar_url,
            },
        )
        updated += int(result.rowcount or 0)

    print(f"circle_updated_rows={updated}")


def fix_resource_posts(conn) -> None:
    rows = conn.execute(
        text(
            """
            SELECT id, post_code, title, images_json
            FROM resource_posts
            WHERE images_json IS NOT NULL AND images_json != ''
            ORDER BY id DESC
            """
        )
    ).mappings().all()

    updated = 0
    bad_preview = []
    for row in rows:
        next_images_json, changed = clean_resource_images(row.get("images_json"))
        if not changed:
            continue
        if len(bad_preview) < 20:
            bad_preview.append({
                "post_code": row.get("post_code"),
                "title": row.get("title"),
                "images_json": row.get("images_json"),
            })
        result = conn.execute(
            text(
                """
                UPDATE resource_posts
                SET images_json = :images_json
                WHERE id = :id
                """
            ),
            {
                "id": row.get("id"),
                "images_json": next_images_json,
            },
        )
        updated += int(result.rowcount or 0)

    print(f"resource_post_bad_rows={updated}")
    for row in bad_preview:
        print(row)
    print(f"resource_post_updated_rows={updated}")


def main() -> None:
    engine = create_engine(settings.DATABASE_URL)
    with engine.begin() as conn:
        fix_circles(conn)
        fix_resource_posts(conn)


if __name__ == "__main__":
    main()
