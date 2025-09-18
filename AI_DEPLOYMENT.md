# AI Instructions: Docker & Deployment

## Architecture Overview

**Multi-Service Architecture:**
- Backend: Port 8000 (FastAPI/Python)
- Frontend: Port 3000 (Next.js)
- PostgreSQL: Port 5432 (with pgvector extension)
- Redis: Port 6379 (caching and sessions)

## Development Setup

**Start Core Services:**
```bash
# Start database and cache services
docker-compose up -d postgres redis

# Verify services are running
docker-compose ps
```

**Backend Development:**
```bash
cd services/ai-orchestrator

# Install dependencies with hash verification
pip install -r constraints.txt --require-hashes

# Run development server
python enhanced_main.py

# Or with auto-reload
uvicorn cartrita.orchestrator.main:app --reload --port 8000
```

**Frontend Development:**
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## Container Security

**All containers implement security hardening:**

- **Non-root users:** All services run as unprivileged users
- **Read-only filesystems:** Containers use read-only root filesystems
- **Minimal attack surface:** No unnecessary packages or tools
- **Resource limits:** Memory and CPU constraints defined
- **Security contexts:** AppArmor/SELinux profiles applied

**PostgreSQL Security:**
```yaml
# docker-compose.yml excerpt
postgres:
  user: "999:999"  # postgres user
  read_only: true
  security_opt:
    - no-new-privileges:true
    - apparmor:unconfined  # Required for PostgreSQL
  tmpfs:
    - /tmp:size=100M,mode=1777
    - /var/run/postgresql:size=10M,mode=0755
```

## Environment Configuration

**Backend Environment (.env):**
```bash
# Database
POSTGRES_USER=robbie
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://robbie:password@postgres:5432/cartrita

# Cache
REDIS_URL=redis://redis:6379/0

# AI Services
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
DEEPGRAM_API_KEY=your-deepgram-key

# Security
JWT_SECRET_KEY=your-jwt-secret-32-chars-minimum
CARTRITA_API_KEY=your-api-key-2025

# Environment
CARTRITA_ENV=development
TESTING=false
```

**Frontend Environment (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Production Deployment

**Docker Build Commands:**
```bash
# Backend production build
docker build -t cartrita-backend:latest -f services/ai-orchestrator/Dockerfile services/ai-orchestrator/

# Frontend production build
docker build -t cartrita-frontend:latest -f frontend/Dockerfile frontend/

# Full stack deployment
docker-compose -f docker-compose.prod.yml up -d
```

**Production Environment Variables:**
```bash
# Use secure random values in production
POSTGRES_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -base64 32)
CARTRITA_API_KEY=$(openssl rand -base64 32)

# Production URLs
NEXT_PUBLIC_API_URL=https://api.cartrita.com
DATABASE_URL=postgresql://user:pass@prod-db:5432/cartrita
```

## Health Checks

**Service Health Endpoints:**
- Backend: `GET http://localhost:8000/health`
- Frontend: `GET http://localhost:3000/api/health`
- PostgreSQL: Built-in Docker health check
- Redis: Built-in Docker health check

**Monitoring Commands:**
```bash
# Check all service status
docker-compose ps

# View service logs
docker-compose logs backend
docker-compose logs frontend

# Monitor resource usage
docker stats
```

## Database Operations

**PostgreSQL with pgvector:**
```bash
# Connect to database
docker-compose exec postgres psql -U robbie -d cartrita

# Create extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;

# Backup database
docker-compose exec postgres pg_dump -U robbie cartrita > backup.sql

# Restore database
docker-compose exec -T postgres psql -U robbie cartrita < backup.sql
```

**Migration Commands:**
```bash
cd services/ai-orchestrator

# Run database migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"
```

## Scaling Considerations

**Horizontal Scaling:**
- Backend: Scale behind load balancer
- Frontend: Scale as static assets + API proxy
- Database: Use read replicas for queries
- Redis: Use Redis Cluster for high availability

**Resource Allocation:**
```yaml
# Production resource limits
backend:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: "1.0"
      reservations:
        memory: 1G
        cpus: "0.5"

frontend:
  deploy:
    resources:
      limits:
        memory: 512M
        cpus: "0.5"
```

## Security Best Practices

**Network Security:**
```yaml
# Use custom networks
networks:
  cartrita-internal:
    driver: bridge
    internal: true  # No external access
  cartrita-external:
    driver: bridge
```

**Secrets Management:**
```bash
# Use Docker secrets in production
docker secret create postgres_password /path/to/password/file
docker secret create jwt_secret /path/to/jwt/file

# Reference in compose file
secrets:
  - postgres_password
  - jwt_secret
```

## Backup Strategy

**Automated Backups:**
```bash
# Database backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec postgres pg_dump -U robbie cartrita > "backup_${DATE}.sql"
gzip "backup_${DATE}.sql"

# Upload to secure storage
aws s3 cp "backup_${DATE}.sql.gz" s3://your-backup-bucket/
```

## Troubleshooting

**Common Issues:**

1. **Port conflicts:**
   ```bash
   # Check what's using ports
   lsof -i :8000
   lsof -i :3000
   ```

2. **Database connection issues:**
   ```bash
   # Check PostgreSQL logs
   docker-compose logs postgres

   # Test connection
   docker-compose exec postgres psql -U robbie -d cartrita -c "SELECT 1;"
   ```

3. **Memory issues:**
   ```bash
   # Check container resource usage
   docker stats

   # Increase Docker memory limits if needed
   ```

**Log Analysis:**
```bash
# Follow all service logs
docker-compose logs -f

# Filter specific service logs
docker-compose logs backend | grep ERROR

# Export logs for analysis
docker-compose logs --no-color > cartrita.log
```

## Development Workflows

**Quick Development Restart:**
```bash
# Restart just the backend
docker-compose restart backend

# Rebuild and restart after code changes
docker-compose up -d --build backend

# Reset database (development only)
docker-compose down -v
docker-compose up -d postgres
# Run migrations
```

**Production Deployment Checklist:**

1. ✅ Update environment variables
2. ✅ Run database migrations
3. ✅ Build production images
4. ✅ Run security scan on images
5. ✅ Deploy with zero downtime
6. ✅ Verify health checks
7. ✅ Monitor logs and metrics
8. ✅ Test critical user flows

## CI/CD Integration

**GitHub Actions Example:**
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and test
        run: |
          docker-compose -f docker-compose.ci.yml up --abort-on-container-exit

      - name: Deploy to production
        run: |
          docker-compose -f docker-compose.prod.yml up -d
```
