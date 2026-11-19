# Backend Dockerfile for GuruDok API (Coolify Staging)
# Build context must be repository root (.) so document/dataset is included.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=staging \
    DATASET_PATH=/app/backend/dataset \
    GENERATED_DIR=/app/backend/generated_docs

WORKDIR /app

# Install system dependencies for PostgreSQL driver & healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (for layer caching)
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend source (includes backend/dataset/)
COPY backend/ /app/backend/

WORKDIR /app/backend

RUN mkdir -p /app/backend/generated_docs

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
