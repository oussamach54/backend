# backend/Dockerfile
-FROM python:3.11-slim
+FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# runtime libs
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 curl wget \
 && rm -rf /var/lib/apt/lists/*

# deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app
COPY . .

# Gunicorn (WSGI lives in my_project.wsgi)
CMD ["gunicorn", "my_project.wsgi:application", "--bind", "0.0.0.0:8000"]
