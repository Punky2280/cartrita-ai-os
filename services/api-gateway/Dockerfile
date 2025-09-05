# Cartrita AI OS - API Gateway Service
# Node.js 22 + Fastify with Security Hardening (2025)

FROM node:22-alpine AS base

# Install security updates and required tools
RUN apk update && apk upgrade && \
    apk add --no-cache dumb-init curl && \
    rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S -u 1001 -G nodejs nodejs

FROM base AS dependencies
WORKDIR /app
COPY package*.json ./
RUN npm install --only=production && \
    npm cache clean --force && \
    chown -R nodejs:nodejs node_modules

FROM base AS runtime
WORKDIR /app

# Copy dependencies and application code with proper ownership
COPY --from=dependencies --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --chown=nodejs:nodejs . .

# Create health check script
RUN echo '#!/bin/sh\ncurl -f http://localhost:3000/health || exit 1' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh && \
    chown nodejs:nodejs /app/healthcheck.sh

# Create necessary directories
RUN mkdir -p /app/logs /app/temp && \
    chown -R nodejs:nodejs /app

# Switch to non-root user
USER nodejs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD ./healthcheck.sh

# Security labels
LABEL security.non-root=true \
      maintainer="Cartrita AI Team" \
      version="2.0.0"

# Expose port
EXPOSE 3000

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "src/index.js"]
