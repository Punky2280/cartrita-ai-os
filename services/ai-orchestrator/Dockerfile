# Cartrita AI OS - AI Orchestrator Service
# Deterministic dependency build (pip-tools constraints) - Python 3.13

FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PYTHON_ENV=production \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    redis-tools \
    curl \
    git \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r cartrita && useradd -r -g cartrita cartrita

# Set work directory
WORKDIR /app

# Copy locked dependency constraints (hash-locked)
COPY constraints.txt ./

# Install dependencies deterministically using constraints with hashes
RUN python -m pip install --no-cache-dir --upgrade pip wheel --root-user-action=ignore && \
    pip install --no-cache-dir --require-hashes -r constraints.txt --root-user-action=ignore && \
    pip check

# Copy source code (service context)
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/uploads /app/temp && \
    chown -R cartrita:cartrita /app

# Switch to non-root user
USER cartrita

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start application with proper configuration
CMD ["uvicorn", "cartrita.orchestrator.main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--workers", "4", \
    "--loop", "uvloop", \
    "--http", "httptools", \
    "--access-log", \
    "--log-level", "info"]
