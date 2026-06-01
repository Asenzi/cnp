from sqlalchemy import create_engine, text

from app.core.config import settings


DEFAULT_COVER_URL = str(settings.DEFAULT_AVATAR_URL or "/static/logo.png").strip() or "/static/logo.png"
DEFAULT_AVATAR_URL = DEFAULT_COVER_URL


def main() -> None:
    engine = create_engine(settings.DATABASE_URL)
    bad_url_where = """
        LOWER(cover_url) LIKE 'http://tmp/%'
        OR LOWER(cover_url) LIKE 'https://tmp/%'
        OR LOWER(avatar_url) LIKE 'http://tmp/%'
        OR LOWER(avatar_url) LIKE 'https://tmp/%'
        OR LOWER(cover_url) LIKE 'wxfile://%'
        OR LOWER(avatar_url) LIKE 'wxfile://%'
        OR LOWER(cover_url) LIKE 'file://%'
        OR LOWER(avatar_url) LIKE 'file://%'
    """

    with engine.begin() as conn:
        before_rows = conn.execute(
            text(
                f"""
                SELECT circle_code, name, cover_url, avatar_url
                FROM circles
                WHERE {bad_url_where}
                ORDER BY id DESC
                """
            )
        ).mappings().all()

        print(f"found_bad_rows={len(before_rows)}")
        for row in before_rows[:20]:
            print(dict(row))

        if not before_rows:
            return

        result = conn.execute(
            text(
                f"""
                UPDATE circles
                SET
                  cover_url = CASE
                    WHEN (
                      LOWER(cover_url) LIKE 'http://tmp/%'
                      OR LOWER(cover_url) LIKE 'https://tmp/%'
                      OR LOWER(cover_url) LIKE 'wxfile://%'
                      OR LOWER(cover_url) LIKE 'file://%'
                    ) THEN :default_cover
                    ELSE cover_url
                  END,
                  avatar_url = CASE
                    WHEN (
                      LOWER(avatar_url) LIKE 'http://tmp/%'
                      OR LOWER(avatar_url) LIKE 'https://tmp/%'
                      OR LOWER(avatar_url) LIKE 'wxfile://%'
                      OR LOWER(avatar_url) LIKE 'file://%'
                    ) THEN :default_avatar
                    ELSE avatar_url
                  END
                WHERE {bad_url_where}
                """
            ),
            {
                "default_cover": DEFAULT_COVER_URL,
                "default_avatar": DEFAULT_AVATAR_URL,
            },
        )

        print(f"updated_rows={result.rowcount}")

        after_rows = conn.execute(
            text(
                f"""
                SELECT circle_code, name, cover_url, avatar_url
                FROM circles
                WHERE {bad_url_where}
                ORDER BY id DESC
                """
            )
        ).mappings().all()
        print(f"remaining_bad_rows={len(after_rows)}")


if __name__ == "__main__":
    main()
