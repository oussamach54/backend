# backend/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# only runtime libs are fine because we're using psycopg2-binary
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl wget \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# run migrations + collectstatic before starting gunicorn (like your old file)
ENV DJANGO_SETTINGS_MODULE=my_project.settings
ENV STATIC_ROOT=/app/staticfiles
ENV MEDIA_ROOT=/app/media

CMD sh -c "python manage.py migrate --noinput && \
           python manage.py collectstatic --noinput && \
           gunicorn my_project.wsgi:application --bind 0.0.0.0:8000"
