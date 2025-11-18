#!/usr/bin/env bash
set -euo pipefail

# Если DATABASE_URL имеет префикс postgresql+asyncpg:// — заменим его на postgresql://
DB_URL="${DATABASE_URL:-}"
if [[ "$DB_URL" == postgresql+asyncpg://* ]]; then
  MIGRATE_DB_URL="${DB_URL/postgresql+asyncpg:/postgresql:}"
else
  MIGRATE_DB_URL="$DB_URL"
fi

echo "Running yoyo migrations on $MIGRATE_DB_URL"
yoyo apply -b --database "$MIGRATE_DB_URL" /app/migrations || {
  echo "Migrations failed"
  exit 1
}

exec uvicorn app.main:app --host 0.0.0.0 --port 8000