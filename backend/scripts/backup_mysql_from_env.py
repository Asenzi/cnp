from __future__ import annotations

import argparse
import gzip
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Destination .sql.gz path")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(output.parent, 0o700)

    dump_environment = os.environ.copy()
    dump_environment["MYSQL_PWD"] = str(settings.MYSQL_PASSWORD)

    command = [
        "mysqldump",
        "--default-character-set=utf8mb4",
        "--single-transaction",
        "--quick",
        "--routines",
        "--events",
        "--triggers",
        "--hex-blob",
        "--set-gtid-purged=OFF",
        "--host",
        str(settings.MYSQL_HOST),
        "--port",
        str(settings.MYSQL_PORT),
        "--user",
        str(settings.MYSQL_USER),
        str(settings.MYSQL_DB),
    ]

    with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        with tmp_path.open("wb") as raw_output:
            subprocess.run(
                command,
                stdout=raw_output,
                stderr=subprocess.PIPE,
                env=dump_environment,
                check=True,
            )
        with tmp_path.open("rb") as source, gzip.open(output, "wb", compresslevel=9) as target:
            shutil.copyfileobj(source, target)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or b"").decode("utf-8", errors="replace").strip()
        print(f"mysqldump failed: {stderr or exc}", file=sys.stderr)
        return exc.returncode or 1
    finally:
        tmp_path.unlink(missing_ok=True)

    subprocess.run(["gzip", "-t", str(output)], check=True)
    print(f"backup_path={output}")
    print(f"backup_size={output.stat().st_size}")
    print(f"backup_sha256={sha256_file(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
