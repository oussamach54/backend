# Use a slim Python base
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# OS deps (build tools + libpq for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Install Python deps first (better cache)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . /app

# (Optional) show Django version for debug
RUN python -c "import django,sys; print('Django:', django.get_version())"

# Expose the app port
EXPOSE 8000

# Entrypoint (runs migrate, collectstatic, then gunicorn)
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
