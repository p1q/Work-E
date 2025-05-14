#!/bin/sh

echo "Loading environment variables from /app/dev.env..."

set -a
. /app/dev.env
set +a

echo "Environment variables loaded:"
env | grep -E 'DJANGO_|DB_|ALLOWED_HOSTS'

echo "Starting Django..."

if [ "$#" -eq 0 ]; then
  exec python manage.py runserver 0.0.0.0:8000
else
  exec "$@"
fi
