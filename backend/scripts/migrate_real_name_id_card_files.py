from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import SessionLocal
from app.crud import (
    get_user_real_name_profile,
    set_user_real_name_profile_verified_at,
    upsert_user_real_name_profile,
)
from app.models.user_real_name_profile import UserRealNameProfile
from app.models.user_verification import UserVerification
from app.verification.constants import VerificationStatus, VerificationType
from app.verification.files import (
    ID_CARD_STORAGE_DIR,
    LEGACY_ID_CARD_URL_PREFIX,
    PRIVATE_ID_CARD_URL_PREFIX,
    build_private_id_card_file_ref,
    resolve_id_card_file_path,
)
from app.verification.service import (
    _encrypt_sensitive_text,
    _hash_id_number,
    _mask_id_number,
)


@dataclass
class MigrationStats:
    scanned_records: int = 0
    scanned_orphan_profiles: int = 0
    updated_payloads: int = 0
    created_profiles: int = 0
    updated_profiles: int = 0
    migrated_file_refs: int = 0
    deleted_legacy_files: int = 0
    missing_files: int = 0
    skipped_profile_creation: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class FileMigrationResult:
    file_ref: str | None
    changed: bool = False
    cleanup_path: Path | None = None


class RealNameFileMigrator:
    def __init__(self) -> None:
        self._legacy_to_private: dict[str, str] = {}
        self._cleanup_paths: set[Path] = set()

    def migrate_file_ref(self, file_ref: str | None) -> FileMigrationResult:
        normalized = str(file_ref or "").strip()
        if not normalized:
            return FileMigrationResult(file_ref=None, changed=False)
        if normalized.startswith(PRIVATE_ID_CARD_URL_PREFIX):
            return FileMigrationResult(file_ref=normalized, changed=False)
        if not normalized.startswith(LEGACY_ID_CARD_URL_PREFIX):
            return FileMigrationResult(file_ref=normalized, changed=False)
        if normalized in self._legacy_to_private:
            return FileMigrationResult(file_ref=self._legacy_to_private[normalized], changed=True)

        source_name = Path(normalized).name
        preferred_private_path = ID_CARD_STORAGE_DIR / source_name
        if preferred_private_path.is_file():
            private_ref = build_private_id_card_file_ref(source_name)
            self._legacy_to_private[normalized] = private_ref
            return FileMigrationResult(file_ref=private_ref, changed=True)

        source_path = resolve_id_card_file_path(normalized)
        ID_CARD_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        target_path = self._build_unique_target_path(source_path.name)
        shutil.copy2(source_path, target_path)
        private_ref = build_private_id_card_file_ref(target_path.name)
        self._legacy_to_private[normalized] = private_ref
        self._cleanup_paths.add(source_path)
        return FileMigrationResult(file_ref=private_ref, changed=True, cleanup_path=source_path)

    def cleanup_legacy_files(self) -> int:
        deleted = 0
        for path in sorted(self._cleanup_paths):
            try:
                if path.exists():
                    path.unlink()
                    deleted += 1
            except OSError:
                continue
        return deleted

    @staticmethod
    def _build_unique_target_path(file_name: str) -> Path:
        candidate = ID_CARD_STORAGE_DIR / Path(file_name).name
        if not candidate.exists():
            return candidate

        stem = candidate.stem
        suffix = candidate.suffix
        index = 1
        while True:
            next_candidate = ID_CARD_STORAGE_DIR / f"{stem}_{index}{suffix}"
            if not next_candidate.exists():
                return next_candidate
            index += 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate legacy real-name id-card files from /static to private storage."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect and print migration summary without writing changes.",
    )
    return parser.parse_args()


def _load_payload(payload_json: str | None) -> dict | None:
    if not payload_json:
        return None
    try:
        payload = json.loads(payload_json)
    except (TypeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _dump_payload(payload: dict | None) -> str | None:
    if not payload:
        return None
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _normalize_text(value: str | None, max_len: int) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return text[:max_len]


def _migrate_record(
    *,
    db,
    record: UserVerification,
    migrator: RealNameFileMigrator,
    stats: MigrationStats,
    dry_run: bool,
) -> None:
    stats.scanned_records += 1
    payload = _load_payload(record.submit_payload_json) or {}
    profile = get_user_real_name_profile(db=db, user_pk=int(record.user_pk))

    active_front_ref = str((profile.id_front_url if profile else payload.get("id_front_url")) or "").strip()
    active_back_ref = str((profile.id_back_url if profile else payload.get("id_back_url")) or "").strip()

    front_result = FileMigrationResult(file_ref=active_front_ref or None)
    back_result = FileMigrationResult(file_ref=active_back_ref or None)

    try:
        if active_front_ref:
            front_result = migrator.migrate_file_ref(active_front_ref)
            if front_result.changed:
                stats.migrated_file_refs += 1
        if active_back_ref:
            back_result = migrator.migrate_file_ref(active_back_ref)
            if back_result.changed:
                stats.migrated_file_refs += 1
    except Exception as exc:
        stats.missing_files += 1
        stats.errors.append(f"verification_id={record.id}: file migration failed: {exc}")

    payload_changed = False
    new_payload = dict(payload)
    raw_id_number = _normalize_text(new_payload.get("id_number"), 18)
    id_number_masked = _normalize_text(new_payload.get("id_number_masked"), 32)
    if raw_id_number:
        if not id_number_masked:
            id_number_masked = _mask_id_number(raw_id_number)
        new_payload.pop("id_number", None)
        payload_changed = True
    if id_number_masked and new_payload.get("id_number_masked") != id_number_masked:
        new_payload["id_number_masked"] = id_number_masked
        payload_changed = True
    if front_result.file_ref and new_payload.get("id_front_url") != front_result.file_ref:
        new_payload["id_front_url"] = front_result.file_ref
        payload_changed = True
    if back_result.file_ref and new_payload.get("id_back_url") != back_result.file_ref:
        new_payload["id_back_url"] = back_result.file_ref
        payload_changed = True

    profile_changed = False
    if profile is None:
        real_name = _normalize_text(new_payload.get("real_name"), 32)
        if real_name and raw_id_number and front_result.file_ref and back_result.file_ref:
            if not dry_run:
                upsert_user_real_name_profile(
                    db=db,
                    user_pk=int(record.user_pk),
                    real_name=real_name,
                    id_number_masked=id_number_masked or "",
                    id_number_hash=_hash_id_number(raw_id_number) or "",
                    id_number_encrypted=_encrypt_sensitive_text(raw_id_number),
                    id_front_url=front_result.file_ref,
                    id_back_url=back_result.file_ref,
                )
                if record.status == VerificationStatus.APPROVED.value:
                    set_user_real_name_profile_verified_at(
                        db=db,
                        user_pk=int(record.user_pk),
                        verified_at=record.reviewed_at,
                    )
            stats.created_profiles += 1
        else:
            stats.skipped_profile_creation += 1
    else:
        if front_result.file_ref and profile.id_front_url != front_result.file_ref:
            profile.id_front_url = front_result.file_ref
            profile_changed = True
        if back_result.file_ref and profile.id_back_url != back_result.file_ref:
            profile.id_back_url = back_result.file_ref
            profile_changed = True
        if profile_changed:
            if record.status == VerificationStatus.APPROVED.value and profile.verified_at != record.reviewed_at:
                profile.verified_at = record.reviewed_at
            if not dry_run:
                db.add(profile)
            stats.updated_profiles += 1

    if payload_changed:
        if not dry_run:
            record.submit_payload_json = _dump_payload(new_payload)
            db.add(record)
        stats.updated_payloads += 1


def _migrate_profile_only(
    *,
    db,
    profile: UserRealNameProfile,
    migrator: RealNameFileMigrator,
    stats: MigrationStats,
    dry_run: bool,
) -> None:
    stats.scanned_orphan_profiles += 1

    profile_changed = False
    try:
        front_result = migrator.migrate_file_ref(profile.id_front_url)
        back_result = migrator.migrate_file_ref(profile.id_back_url)
    except Exception as exc:
        stats.missing_files += 1
        stats.errors.append(f"profile_user_pk={profile.user_pk}: file migration failed: {exc}")
        return

    if front_result.changed:
        stats.migrated_file_refs += 1
    if back_result.changed:
        stats.migrated_file_refs += 1

    if front_result.file_ref and profile.id_front_url != front_result.file_ref:
        profile.id_front_url = front_result.file_ref
        profile_changed = True
    if back_result.file_ref and profile.id_back_url != back_result.file_ref:
        profile.id_back_url = back_result.file_ref
        profile_changed = True

    if profile_changed:
        if not dry_run:
            db.add(profile)
        stats.updated_profiles += 1


def main() -> int:
    args = parse_args()
    migrator = RealNameFileMigrator()
    stats = MigrationStats()

    with SessionLocal() as db:
        records = list(
            db.execute(
                select(UserVerification)
                .where(UserVerification.verify_type == VerificationType.REAL_NAME.value)
                .order_by(UserVerification.id.asc())
            ).scalars()
        )
        migrated_user_pks = {int(record.user_pk) for record in records}

        for record in records:
            try:
                _migrate_record(
                    db=db,
                    record=record,
                    migrator=migrator,
                    stats=stats,
                    dry_run=bool(args.dry_run),
                )
                if not args.dry_run:
                    db.commit()
            except Exception as exc:
                db.rollback()
                stats.errors.append(f"verification_id={record.id}: {exc}")

        orphan_profiles = list(
            db.execute(
                select(UserRealNameProfile)
                .where(UserRealNameProfile.user_pk.not_in(migrated_user_pks))
                .order_by(UserRealNameProfile.id.asc())
            ).scalars()
        )
        for profile in orphan_profiles:
            try:
                _migrate_profile_only(
                    db=db,
                    profile=profile,
                    migrator=migrator,
                    stats=stats,
                    dry_run=bool(args.dry_run),
                )
                if not args.dry_run:
                    db.commit()
            except Exception as exc:
                db.rollback()
                stats.errors.append(f"profile_user_pk={profile.user_pk}: {exc}")

    if not args.dry_run:
        stats.deleted_legacy_files = migrator.cleanup_legacy_files()

    print(f"scanned_records={stats.scanned_records}")
    print(f"scanned_orphan_profiles={stats.scanned_orphan_profiles}")
    print(f"updated_payloads={stats.updated_payloads}")
    print(f"created_profiles={stats.created_profiles}")
    print(f"updated_profiles={stats.updated_profiles}")
    print(f"migrated_file_refs={stats.migrated_file_refs}")
    print(f"deleted_legacy_files={stats.deleted_legacy_files}")
    print(f"missing_files={stats.missing_files}")
    print(f"skipped_profile_creation={stats.skipped_profile_creation}")
    if stats.errors:
        print("errors:")
        for item in stats.errors:
            print(f"  - {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
