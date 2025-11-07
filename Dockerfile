FROM python:3.9-slim


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential libpq-dev curl wget && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV DJANGO_SETTINGS_MODULE=my_project.settings
ENV STATIC_ROOT=/app/staticfiles
ENV MEDIA_ROOT=/app/media

# Add a proper healthcheck to let Coolify wait until Django is ready
HEALTHCHECK --interval=15s --timeout=10s --retries=5 CMD curl -fs http://localhost:8000/health/ || exit 1


CMD sh -c "python manage.py migrate --noinput && \
           python manage.py collectstatic --noinput && \
           gunicorn my_project.wsgi:application -c gunicorn.conf.py"
