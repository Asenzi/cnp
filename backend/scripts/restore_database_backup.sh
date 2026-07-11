#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: sudo $0 /var/backups/cnp/mysql/<backup>.sql.gz.enc" >&2
  exit 2
fi

BACKUP_FILE="$1"
KEY_FILE="${CNP_BACKUP_KEY_PATH:-/etc/cnp/backup-encryption.key}"
WORK_DIR="$(mktemp -d /tmp/cnp-db-restore.XXXXXX)"
trap 'rm -rf "$WORK_DIR"' EXIT

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

if [[ ! -f "$KEY_FILE" ]]; then
  echo "Encryption key not found: $KEY_FILE" >&2
  exit 1
fi

echo "This command decrypts and validates the backup only."
echo "It will NOT overwrite the production database automatically."

openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
  -pass "file:$KEY_FILE" \
  -in "$BACKUP_FILE" \
  -out "$WORK_DIR/backup.sql.gz"

gzip -t "$WORK_DIR/backup.sql.gz"
gzip -dc "$WORK_DIR/backup.sql.gz" > "$WORK_DIR/backup.sql"

echo "Backup validated successfully."
echo "Decrypted SQL: $WORK_DIR/backup.sql"
echo "Import it into an empty recovery database after reviewing the target."
read -r -p "Press Enter after inspection to securely remove the temporary SQL..."
