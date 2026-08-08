#!/bin/sh
set -e

# Wait for PostgreSQL to be ready if DB_HOST is set
if [ -n "$DB_HOST" ]; then
  echo "Checking PostgreSQL connection ($DB_HOST:${DB_PORT:-5432})..."
  counter=0
  until nc -z $DB_HOST ${DB_PORT:-5432} || [ $counter -gt 30 ]; do
    echo "Waiting for PostgreSQL..."
    sleep 1
    counter=$((counter+1))
  done
  echo "PostgreSQL check complete."
fi

# Wait for Redis to be ready only if REDIS_HOST is explicitly set (e.g. local Docker)
if [ -n "$REDIS_HOST" ]; then
  echo "Checking Redis connection ($REDIS_HOST:${REDIS_PORT:-6379})..."
  counter=0
  until nc -z $REDIS_HOST ${REDIS_PORT:-6379} || [ $counter -gt 30 ]; do
    echo "Waiting for Redis..."
    sleep 1
    counter=$((counter+1))
  done
  echo "Redis check complete."
fi

# Execute database migrations (if enabled for this container)
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Running database migrations..."
  python manage.py migrate --noinput

  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

echo "Starting application..."
exec "$@"
