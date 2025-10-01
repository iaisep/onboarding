# Dockerfile para Coolify - Optimizado con QR Code Support
# Updated: 2025-10-01 - Added QR code dependencies (libzbar, pyzbar, opencv)
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# Set work directory
WORKDIR /app

# Install system dependencies with retry logic
RUN set -ex && \
    for i in 1 2 3; do \
        apt-get update && \
        apt-get install -y --no-install-recommends \
            postgresql-client \
            build-essential \
            libpq-dev \
            curl \
            libzbar0 \
            libzbar-dev \
            libgl1-mesa-glx \
            libglib2.0-0 \
            libsm6 \
            libxext6 \
            libxrender-dev && \
        break || \
        { echo "Retry $i failed"; sleep 5; }; \
    done && \
    rm -rf /var/lib/apt/lists/*

# Configure libzbar for pyzbar
RUN ldconfig && \
    echo "Verifying libzbar installation..." && \
    find /usr -name "libzbar.so*" && \
    ls -la /usr/lib/x86_64-linux-gnu/libzbar.so* || true && \
    ldconfig -p | grep zbar || true

# Install Python dependencies
COPY requirements-docker.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-docker.txt

# Verify pyzbar can find libzbar
RUN python3 -c "import pyzbar; print('✅ pyzbar imported successfully')" || \
    { echo "❌ pyzbar import failed - debugging..."; \
      echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"; \
      ldconfig -p | grep zbar; \
      find /usr -name "libzbar.so*"; \
      python3 -c "from pyzbar import pyzbar" 2>&1 || true; \
      exit 1; }

# Copy project
COPY . .

# Create directories
RUN mkdir -p /app/static /app/logs

# Copy entrypoint
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Create user
RUN addgroup --system django && \
    adduser --system --group django && \
    chown -R django:django /app

USER django

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/admin/login/ || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "apibase.wsgi:application"]
