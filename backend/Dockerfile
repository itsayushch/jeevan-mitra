# ==============================================================================
# JEEVAN-MITRA 2.0 - PRODUCTION MULTI-STAGE DOCKERFILE
# Optimized for Microsoft Azure (Container Apps, App Service, AKS)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Stage
# ------------------------------------------------------------------------------
FROM node:22-bookworm-slim AS builder

WORKDIR /app

# Install native compilation dependencies for better-sqlite3
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy package manifests first to leverage Docker layer caching
COPY package.json package-lock.json* ./

# Install dependencies including devDependencies for build
RUN npm install

# Copy source code and TypeScript config
COPY tsconfig.json ./
COPY src/ ./src/

# Compile TypeScript to dist/ and copy schema.sql
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Production Runtime Stage
# ------------------------------------------------------------------------------
FROM node:22-bookworm-slim AS runner

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    make \
    g++ \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy package manifests
COPY package.json package-lock.json* ./

# Install only production dependencies
RUN npm install --omit=dev && \
    apt-get purge -y python3 make g++ && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy compiled artifacts from builder stage
COPY --from=builder /app/dist ./dist

# Copy SQL schema into both dist and src fallback locations
COPY src/database/schema.sql ./dist/database/schema.sql
COPY src/database/schema.sql ./src/database/schema.sql

# Copy entrypoint script
COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh

# Create persistent data directory and assign ownership to node user
RUN mkdir -p /app/data && chown -R node:node /app

# Azure enterprise security compliance: Run as non-root user
USER node

# Production Environment Variables
ENV NODE_ENV=production \
    PORT=4000 \
    HOST=0.0.0.0 \
    DATABASE_PATH=/app/data/jeevanmitra.db \
    DEFAULT_DISTRICT=Moradabad \
    DEFAULT_STATE="Uttar Pradesh" \
    AI_PROVIDER=mock \
    CONFIDENCE_THRESHOLD=0.75

# Expose HTTP port (Azure App Service / Container Apps standard)
EXPOSE 4000

# Azure Health Probe & Container Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:4000/api/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["node", "dist/index.js"]
