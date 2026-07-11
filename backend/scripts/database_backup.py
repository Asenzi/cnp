from __future__ import annotations

import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import datetime as _datetime

if not hasattr(_datetime, "UTC"):
    _datetime.UTC = _datetime.timezone.utc

from datetime import UTC, datetime, timedelta

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from qcloud_cos import CosConfig, CosS3Client

from app.core.config import settings


BACKUP_ROOT = Path(os.getenv("CNP_BACKUP_ROOT", "/var/backups/cnp/mysql"))
ENCRYPTION_KEY_PATH = Path(
    os.getenv("CNP_BACKUP_KEY_PATH", "/etc/cnp/backup-encryption.key")
)
BINLOG_DIR = Path(os.getenv("CNP_MYSQL_BINLOG_DIR", "/www/server/data"))
COS_PREFIX = os.getenv(
    "CNP_BACKUP_COS_PREFIX",
    f"private/database-backups/{settings.MYSQL_DB}",
).strip("/")
LOCAL_RETENTION_DAYS = int(os.getenv("CNP_BACKUP_LOCAL_RETENTION_DAYS", "8"))
DAILY_RETENTION_DAYS = int(os.getenv("CNP_BACKUP_DAILY_RETENTION_DAYS", "8"))
WEEKLY_RETENTION_DAYS = int(os.getenv("CNP_BACKUP_WEEKLY_RETENTION_DAYS", "36"))
MONTHLY_RETENTION_DAYS = int(os.getenv("CNP_BACKUP_MONTHLY_RETENTION_DAYS", "190"))
BINLOG_RETENTION_DAYS = int(os.getenv("CNP_BACKUP_BINLOG_RETENTION_DAYS", "36"))


def log(message: str) -> None:
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"{timestamp} {message}", flush=True)


def require_configuration() -> None:
    missing = []
    for name in ("COS_SECRET_ID", "COS_SECRET_KEY", "COS_REGION", "COS_BUCKET"):
        if not str(getattr(settings, name, "") or "").strip():
            missing.append(name)
    if missing:
        raise RuntimeError(f"COS configuration is incomplete: {', '.join(missing)}")
    if not ENCRYPTION_KEY_PATH.is_file():
        raise RuntimeError(f"Encryption key does not exist: {ENCRYPTION_KEY_PATH}")
    if ENCRYPTION_KEY_PATH.stat().st_mode & 0o077:
        raise RuntimeError("Encryption key permissions must be 0600 or stricter")


def cos_client() -> CosS3Client:
    config = CosConfig(
        Region=settings.COS_REGION,
        SecretId=settings.COS_SECRET_ID,
        SecretKey=settings.COS_SECRET_KEY,
        Scheme=str(settings.COS_SCHEME or "https").strip() or "https",
    )
    return CosS3Client(config)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def encrypt_file(source: Path, destination: Path) -> None:
    subprocess.run(
        [
            "openssl",
            "enc",
            "-aes-256-cbc",
            "-salt",
            "-pbkdf2",
            "-iter",
            "200000",
            "-pass",
            f"file:{ENCRYPTION_KEY_PATH}",
            "-in",
            str(source),
            "-out",
            str(destination),
        ],
        check=True,
    )


def create_database_dump(work_dir: Path, timestamp: str) -> tuple[Path, dict]:
    sql_path = work_dir / f"{settings.MYSQL_DB}_{timestamp}.sql"
    gzip_path = work_dir / f"{sql_path.name}.gz"
    encrypted_path = BACKUP_ROOT / f"{gzip_path.name}.enc"
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

    log("Creating transaction-consistent MySQL dump")
    with sql_path.open("wb") as output:
        subprocess.run(
            command,
            stdout=output,
            stderr=subprocess.PIPE,
            env=dump_environment,
            check=True,
        )

    with sql_path.open("rb") as source, gzip.open(gzip_path, "wb", compresslevel=9) as target:
        shutil.copyfileobj(source, target)

    encrypt_file(gzip_path, encrypted_path)
    metadata = {
        "created_at": datetime.now().astimezone().isoformat(),
        "database": settings.MYSQL_DB,
        "format": "mysqldump+gzip+aes-256-cbc-pbkdf2",
        "encrypted_file": encrypted_path.name,
        "encrypted_size": encrypted_path.stat().st_size,
        "encrypted_sha256": sha256_file(encrypted_path),
        "sql_size": sql_path.stat().st_size,
    }
    return encrypted_path, metadata


def upload_private_file(
    client: CosS3Client,
    *,
    source: Path,
    key: str,
    content_type: str = "application/octet-stream",
) -> None:
    with source.open("rb") as body:
        client.put_object(
            Bucket=settings.COS_BUCKET,
            Body=body,
            Key=key,
            ContentType=content_type,
        )
    response = client.head_object(Bucket=settings.COS_BUCKET, Key=key)
    remote_size = int(response.get("Content-Length") or 0)
    if remote_size != source.stat().st_size:
        raise RuntimeError(
            f"COS size verification failed for {key}: {remote_size} != {source.stat().st_size}"
        )


def upload_database_backup(
    client: CosS3Client,
    encrypted_path: Path,
    metadata: dict,
    now: datetime,
) -> list[str]:
    daily_key = f"{COS_PREFIX}/daily/{now:%Y-%m-%d}/{encrypted_path.name}"
    keys = [daily_key]
    if now.weekday() == 6:
        keys.append(f"{COS_PREFIX}/weekly/{now:%G-W%V}/{encrypted_path.name}")
    if now.day == 1:
        keys.append(f"{COS_PREFIX}/monthly/{now:%Y-%m}/{encrypted_path.name}")

    metadata_path = encrypted_path.with_suffix(f"{encrypted_path.suffix}.json")
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    try:
        for key in keys:
            upload_private_file(client, source=encrypted_path, key=key)
            upload_private_file(
                client,
                source=metadata_path,
                key=f"{key}.json",
                content_type="application/json",
            )
            log(f"Uploaded and verified private COS object: {key}")
    finally:
        metadata_path.unlink(missing_ok=True)
    return keys


def upload_binlogs(client: CosS3Client, work_dir: Path) -> list[str]:
    uploaded = []
    for binlog_path in sorted(BINLOG_DIR.glob("mysql-bin.[0-9]*")):
        if not binlog_path.is_file():
            continue
        encrypted_path = work_dir / f"{binlog_path.name}.enc"
        encrypt_file(binlog_path, encrypted_path)
        key = f"{COS_PREFIX}/binlog/{binlog_path.name}.enc"
        upload_private_file(client, source=encrypted_path, key=key)
        uploaded.append(key)
        log(f"Uploaded encrypted binlog: {key}")
    return uploaded


def parse_cos_datetime(value: str) -> datetime:
    normalized = str(value or "").strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def delete_expired_cos_objects(
    client: CosS3Client,
    *,
    relative_prefix: str,
    retention_days: int,
) -> int:
    prefix = f"{COS_PREFIX}/{relative_prefix.strip('/')}/"
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    marker = ""
    deleted = 0

    while True:
        response = client.list_objects(
            Bucket=settings.COS_BUCKET,
            Prefix=prefix,
            Marker=marker,
            MaxKeys=1000,
        )
        contents = response.get("Contents") or []
        for item in contents:
            key = str(item.get("Key") or "")
            modified_at = parse_cos_datetime(str(item.get("LastModified") or ""))
            if key and modified_at < cutoff:
                client.delete_object(Bucket=settings.COS_BUCKET, Key=key)
                deleted += 1

        if str(response.get("IsTruncated") or "").lower() != "true":
            break
        marker = str(response.get("NextMarker") or "")
        if not marker:
            break
    return deleted


def delete_expired_local_backups() -> int:
    cutoff = datetime.now().timestamp() - LOCAL_RETENTION_DAYS * 86400
    deleted = 0
    for path in BACKUP_ROOT.glob("*.sql.gz.enc"):
        if path.stat().st_mtime < cutoff:
            path.unlink()
            deleted += 1
    return deleted


def main() -> int:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    os.chmod(BACKUP_ROOT, 0o700)
    lock_path = BACKUP_ROOT / ".backup.lock"

    with lock_path.open("w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log("Another database backup is already running")
            return 0

        require_configuration()
        now = datetime.now().astimezone()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        client = cos_client()

        with tempfile.TemporaryDirectory(prefix="cnp-db-backup-") as temp_dir:
            work_dir = Path(temp_dir)
            encrypted_path, metadata = create_database_dump(work_dir, timestamp)
            database_keys = upload_database_backup(
                client,
                encrypted_path,
                metadata,
                now,
            )
            binlog_keys = upload_binlogs(client, work_dir)

        local_deleted = delete_expired_local_backups()
        cos_deleted = 0
        for prefix, retention in (
            ("daily", DAILY_RETENTION_DAYS),
            ("weekly", WEEKLY_RETENTION_DAYS),
            ("monthly", MONTHLY_RETENTION_DAYS),
            ("binlog", BINLOG_RETENTION_DAYS),
        ):
            cos_deleted += delete_expired_cos_objects(
                client,
                relative_prefix=prefix,
                retention_days=retention,
            )

        log(
            "Backup completed successfully: "
            f"database_objects={len(database_keys)}, binlog_objects={len(binlog_keys)}, "
            f"local_deleted={local_deleted}, cos_deleted={cos_deleted}"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or b"").decode("utf-8", errors="replace").strip()
        log(f"Backup command failed: {stderr or exc}")
        raise
    except Exception as exc:
        log(f"Backup failed: {type(exc).__name__}: {exc}")
        raise
