# =========================
# Base image (Python 3.10)
# =========================
FROM python:3.10-slim

# Core env
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Runtime defaults (can be overridden by Coolify env)
ENV DJANGO_SETTINGS_MODULE=my_project.settings \
    PORT=8000

# System deps (psycopg2 / pillow / healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    curl \
    netcat-traditional \
  && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Install python deps first to leverage cache
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

# Copy project
COPY . /app

# Copy entrypoint and make it executable
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose (informational)
EXPOSE 8000

# Health endpoint will be checked by Coolify with curl
# ENTRYPOINT will run migrations & collectstatic, then exec CMD
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "my_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
