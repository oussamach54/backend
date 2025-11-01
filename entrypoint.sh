#!/bin/sh
set -e

# Migrations DB (PostgreSQL via DATABASE_URL)
python manage.py migrate --noinput || true

# Fichiers statiques (WhiteNoise)
python manage.py collectstatic --noinput || true

# Lancer Gunicorn sur le bon module WSGI : my_project.wsgi
exec gunicorn my_project.wsgi:application --bind 0.0.0.0:8000 --workers 3
