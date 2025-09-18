#!/bin/sh
# Cartrita API Gateway Health Check Script
# Used by Docker HEALTHCHECK to verify service availability

# Check if the service is responding
if curl -f -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "Health check passed"
    exit 0
else
    echo "Health check failed"
    exit 1
fi
