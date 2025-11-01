#!/bin/sh
set -e

# Migrate DB
python manage.py migrate --noinput

# Collect static (won’t fail if nothing to collect)
python manage.py collectstatic --noinput || true

# Start gunicorn
exec gunicorn my_project.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 120
