# X-IDS Production Dockerfile
# Multi-stage build for optimized image size

FROM python:3.10-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Create wheels for faster installation
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt


# Final stage
FROM python:3.10-slim

LABEL maintainer="X-IDS Team"
LABEL description="X-IDS: Explainable Deep Learning Framework for Real-Time Zero-Day Threat Discovery"
LABEL version="1.0.0"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    libffi7 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 xids && \
    mkdir -p /app /data/models /data/logs && \
    chown -R xids:xids /app /data

WORKDIR /app

# Copy wheels from builder
COPY --from=builder /wheels /wheels

# Install Python packages from wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --no-index --find-links /wheels -r requirements.txt && \
    rm -rf /wheels

# Copy application
COPY --chown=xids:xids xids ./xids
COPY --chown=xids:xids setup.py .
COPY --chown=xids:xids training/config.yaml ./training/

# Install package in production mode
RUN pip install --no-cache-dir -e .

# Switch to non-root user
USER xids

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO \
    MODEL_DIR=/data/models \
    LOG_DIR=/data/logs

# Expose API port
EXPOSE 8080

# Default command: run API server
CMD ["python", "-m", "xids.inference.api_server"]
