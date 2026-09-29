# ==============================================================================
# JEEVAN-MITRA 2.0 - PYTHON FASTAPI DOCKERFILE
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install native compilation dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt ./

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY app/ ./app/
COPY run.py ./

# Create persistent data directory and assign ownership
RUN mkdir -p /app/data && groupadd -r jeevanmitra && useradd -r -g jeevanmitra jeevanmitra && chown -R jeevanmitra:jeevanmitra /app

USER jeevanmitra

# Production Environment Variables
ENV NODE_ENV=production \
    PORT=4000 \
    HOST=0.0.0.0 \
    DATABASE_PATH=/app/data/jeevanmitra.db \
    DEFAULT_DISTRICT=Moradabad \
    DEFAULT_STATE="Uttar Pradesh" \
    AI_PROVIDER=mock \
    CONFIDENCE_THRESHOLD=0.75 \
    API_PREFIX=/api/v1 \
    PYTHONPATH=/app

EXPOSE 4000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:4000/api/v1/health || exit 1

CMD ["python", "run.py"]
