#!/bin/sh
set -e

if [ "${RUN_DB_MIGRATIONS:-true}" = "true" ]; then
  echo "Running database migrations: alembic upgrade head"
  alembic upgrade head
  echo "Database migrations complete."
else
  echo "Skipping database migrations because RUN_DB_MIGRATIONS=false"
fi

exec "$@"
