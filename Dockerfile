FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=my_project.settings \
    PORT=8000

# curl for Coolify healthcheck; build tools & pillow deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libjpeg62-turbo-dev zlib1g-dev curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

# Project files
COPY . /app

# Copy entrypoint and normalize any Windows CRLF/BOM
COPY docker/entrypoint.sh /entrypoint.sh
# 1) strip UTF-8 BOM if present  2) strip CRLF -> LF  3) mark executable
RUN printf 'Fixing entrypoint line-endings & BOM...\n' \
 && sed -i '1s/^\xEF\xBB\xBF//' /entrypoint.sh \
 && sed -i 's/\r$//' /entrypoint.sh \
 && chmod +x /entrypoint.sh

EXPOSE 8000

# Call through sh to avoid exec format surprises on some hosts
ENTRYPOINT ["sh", "/entrypoint.sh"]
