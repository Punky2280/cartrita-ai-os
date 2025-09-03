#!/bin/bash
set -e

echo "🚀 Deploying Cartrita AI OS with Production Configuration..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Stop existing containers
docker compose down 2>/dev/null || true

# Build and start services
docker compose up -d --build

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until docker compose exec -T postgres pg_isready -U robbie -d cartrita_db &>/dev/null; do
    sleep 2
done

echo "✅ PostgreSQL is ready!"

# Run database initialization
docker compose exec -T postgres psql -U robbie -d cartrita_db < infrastructure/docker/init-production.sql

echo "✅ Database initialized!"

# Show service URLs
echo ""
echo "🎉 Cartrita AI OS is running!"
echo ""
echo "📌 Services:"
echo "  • Frontend:        http://localhost:3001"
echo "  • API Gateway:     http://localhost:3000"
echo "  • AI Orchestrator: http://localhost:8000"
echo "  • API Docs:        http://localhost:8000/docs"
echo ""
echo "🔑 API Keys:"
echo "  • Development:  dev-api-key-123"
echo "  • Production:   prod-api-key-robbie"
echo ""
echo "📊 Logs: docker compose logs -f"
echo ""
