set -e
echo "[entrypoint] Waiting for DB (if any)…"
nc -z $DB_HOST $DB_PORT -w 2 || echo "Skipping explicit DB wait."
cho "[entrypoint] Running migrations…"
python manage.py migrate --noinput

echo "[entrypoint] Collecting static files…"
python manage.py collectstatic --noinput

echo "[entrypoint] Starting gunicorn…"
exec gunicorn my_project.wsgi:application --bind 0.0.0.0:8000 --workers 3