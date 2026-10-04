#!/usr/bin/env bash
# Еженедельный бэкап БД на сервере: pg_dump (custom, сжатие 9) -> docker -> ротация 60 дней -> лог.
# Настройки можно переопределить переменными окружения. Запускается по cron (см. docs/backups/deploy.md).
set -euo pipefail
umask 077

CONTAINER=${CONTAINER:-meat_db}
DB_USER=${DB_USER:-meat}
DB_NAME=${DB_NAME:-meat}
BACKUP_DIR=${BACKUP_DIR:-/var/backups/meat}
RETENTION_DAYS=${RETENTION_DAYS:-60}
LOG_FILE="$BACKUP_DIR/backup.log"

mkdir -p "$BACKUP_DIR"
STAMP=$(date +%Y-%m-%d_%H%M)
DUMP_FILE="$BACKUP_DIR/meat_$STAMP.dump"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" >> "$LOG_FILE"; }

log "Backup start (db=$DB_NAME user=$DB_USER container=$CONTAINER)"

# Контейнер должен быть запущен
if ! docker inspect --format '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -qx true; then
  log "ERROR: container $CONTAINER not running"
  exit 1
fi

# Дамп custom-формата прямо в контейнере, затем копирование на хост
docker exec "$CONTAINER" pg_dump -U "$DB_USER" -Fc -Z 9 -f "/tmp/meat_$STAMP.dump" "$DB_NAME"
if ! docker exec "$CONTAINER" pg_restore -l "/tmp/meat_$STAMP.dump" >/dev/null 2>&1; then
  log "ERROR: pg_restore rejected dump inside database container"
  docker exec "$CONTAINER" rm -f "/tmp/meat_$STAMP.dump" >/dev/null 2>&1 || true
  exit 1
fi
if ! docker cp "$CONTAINER:/tmp/meat_$STAMP.dump" "$DUMP_FILE"; then
  log "ERROR: docker cp failed"
  docker exec "$CONTAINER" rm -f "/tmp/meat_$STAMP.dump" >/dev/null 2>&1 || true
  exit 1
fi
chmod 600 "$DUMP_FILE"
docker exec "$CONTAINER" rm -f "/tmp/meat_$STAMP.dump" >/dev/null 2>&1 || true

# Проверка целостности
SIZE=$(stat -c%s "$DUMP_FILE")
if [ "$SIZE" -lt 1024 ]; then
  log "ERROR: dump too small ($SIZE bytes): $DUMP_FILE"
  rm -f "$DUMP_FILE"
  exit 1
fi
if ! head -c 5 "$DUMP_FILE" | grep -q '^PGDMP'; then
  log "ERROR: dump has no PGDMP header: $DUMP_FILE"
  rm -f "$DUMP_FILE"
  exit 1
fi
# Ротация: файлы старше RETENTION_DAYS (2 месяца) удаляем
KEPT=0
for f in "$BACKUP_DIR"/meat_*.dump; do
  [ -e "$f" ] || continue
  if [ -n "$(find "$f" -mtime "+$RETENTION_DAYS")" ]; then
    rm -f "$f"
    log "removed old backup: $(basename "$f")"
  else
    KEPT=$((KEPT + 1))
  fi
done

log "OK: $DUMP_FILE ($SIZE bytes), backups kept: $KEPT"
echo "OK: $DUMP_FILE ($SIZE bytes)"