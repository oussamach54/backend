# =========================
# Base image (Python 3.10)
# =========================
FROM python:3.10-slim

# Base env
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=my_project.settings \
    PORT=8000

# System deps (Pillow, Postgres, healthcheck curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Install requirements first (better cache)
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

# Copy project
COPY . /app

# Entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
# Fix CRLF if created on Windows + ensure executable
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

# Static port
EXPOSE 8000

# Start via entrypoint (migrate, collectstatic, gunicorn)
ENTRYPOINT ["/entrypoint.sh"]
