#!/usr/bin/env bash
set -e

# Print env hints (optional)
echo "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-my_project.settings}"
echo "DEBUG=${DJANGO_DEBUG:-true}"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start gunicorn (exec to forward signals)
echo "Starting Gunicorn..."
exec "$@"
