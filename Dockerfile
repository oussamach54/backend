FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=my_project.settings

# System deps for Pillow/Postgres + curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libjpeg62-turbo-dev zlib1g-dev curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps first (cache)
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

# App code
COPY . /app

# Entrypoint: fix CRLF on Windows and make executable
COPY docker/entrypoint.sh /entrypoint.sh
RUN sed -i '1s/^\xEF\xBB\xBF//' /entrypoint.sh \
 && sed -i 's/\r$//' /entrypoint.sh \
 && chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["sh","/entrypoint.sh"]
