#!/usr/bin/env sh
set -e

echo "[entrypoint] Running migrations…"
python manage.py migrate --noinput || true

echo "[entrypoint] Collecting static files…"
python manage.py collectstatic --noinput || true

echo "[entrypoint] Starting gunicorn…"
exec gunicorn my_project.wsgi:application --bind 0.0.0.0:8000 --workers 3
