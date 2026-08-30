# =================================
# Build Stage
# =================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies (needed for some python packages)
RUN apt-get update && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/*

# RUN apt-get update && apt-get install -y ffmpeg

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt

# =================================
# Runtime Stage
# =================================
FROM python:3.12-slim AS runtime

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy deps
COPY --from=builder /install /usr/local

# Copy the rest of the application code
COPY . .

# Create non-root user
RUN adduser --disabled-password appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

USER appuser

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", \
    "0.0.0.0:8000", "--workers", "4"]
    