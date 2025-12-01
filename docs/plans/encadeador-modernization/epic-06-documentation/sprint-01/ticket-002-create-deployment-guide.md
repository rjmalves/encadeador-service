# [DOCS-002] Create Deployment Guide

> **Epic**: [Epic 06: Documentation](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 3  
> **Priority**: P0

## Context

### Background

The deployment guide provides step-by-step instructions for deploying the service using Docker Compose or systemd. It covers prerequisites, configuration, troubleshooting, and monitoring.

### Relation to Epic

Essential for operations teams to deploy and manage the service.

### Current State

No deployment documentation exists for the v2.0 architecture.

## Specification

### File to Create

**Path**: `docs/DEPLOYMENT.md`

### Deployment Guide Content

```markdown
# Deployment Guide

This guide covers deploying the encadeador-service v2.0 using Docker Compose or systemd.

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| Memory | 2 GB | 4 GB |
| Disk | 20 GB | 50 GB |
| OS | Ubuntu 22.04+ | Ubuntu 22.04 LTS |

### Software Requirements

- Docker 24.0+ and Docker Compose v2
- curl (for health checks)
- AWS CLI (optional, for S3 debugging)

### AWS Requirements

- IAM credentials with S3 access (or IAM role for EC2)
- S3 buckets created for DECOMP and NEWAVE artifacts

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/encadeador-service.git
cd encadeador-service
```

### 2. Configure Environment

```bash
cp .env.example .env
vim .env  # Configure AWS credentials and buckets
```

### 3. Start Service

```bash
docker compose up -d
```

### 4. Verify Health

```bash
curl http://localhost:8001/health
# {"status":"healthy","version":"2.0.0",...}
```

## Docker Compose Deployment

### Production Deployment

#### Step 1: Create Docker Network

```bash
docker network create hpc-network
```

#### Step 2: Configure Environment

Create `.env` file:

```bash
APP_VERSION=2.0.0
LOG_LEVEL=INFO
AWS_REGION=us-east-1
DEFAULT_DECOMP_BUCKET=prod-decomp-bucket
DEFAULT_NEWAVE_BUCKET=prod-newave-bucket
```

#### Step 3: Build and Start

```bash
# Build image
docker compose build

# Start in background
docker compose up -d

# View logs
docker compose logs -f encadeador
```

#### Step 4: Verify Deployment

```bash
# Check container status
docker compose ps

# Check health
curl http://localhost:8001/health

# Check readiness
curl http://localhost:8001/health/ready
```

### Development Deployment (with LocalStack)

```bash
# Start with LocalStack for S3 mocking
docker compose -f docker-compose.dev.yml up -d

# Verify LocalStack
curl http://localhost:4566/_localstack/health

# Verify service
curl http://localhost:8001/health
```

### Stopping the Service

```bash
# Stop containers
docker compose down

# Stop and remove volumes
docker compose down -v
```

## systemd Deployment

### Installation

#### Step 1: Install Service Files

```bash
cd deploy
sudo ./install.sh
```

#### Step 2: Configure Environment

```bash
sudo vim /etc/encadeador/environment
```

Configure:
```bash
APP_VERSION=2.0.0
AWS_REGION=us-east-1
DEFAULT_DECOMP_BUCKET=prod-decomp-bucket
DEFAULT_NEWAVE_BUCKET=prod-newave-bucket
```

#### Step 3: Start Service

```bash
sudo systemctl start encadeador
sudo systemctl status encadeador
```

#### Step 4: Enable Auto-Start

```bash
sudo systemctl enable encadeador
```

### Managing the Service

```bash
# Start
sudo systemctl start encadeador

# Stop
sudo systemctl stop encadeador

# Restart
sudo systemctl restart encadeador

# Status
sudo systemctl status encadeador

# View logs
journalctl -u encadeador -f

# View recent logs
journalctl -u encadeador --since "1 hour ago"
```

### Uninstallation

```bash
cd deploy
sudo ./uninstall.sh
```

## Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `APP_VERSION` | Version identifier | 2.0.0 | No |
| `HOST` | Bind address | 0.0.0.0 | No |
| `PORT` | Listen port | 8000 | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `AWS_REGION` | AWS region | us-east-1 | For S3 |
| `S3_ENDPOINT_URL` | Custom S3 endpoint | - | For LocalStack |
| `DEFAULT_DECOMP_BUCKET` | DECOMP bucket | decomp-bucket | For S3 |
| `DEFAULT_NEWAVE_BUCKET` | NEWAVE bucket | newave-bucket | For S3 |
| `DECOMP_SOURCE` | Source mode | S3 | No |
| `NEWAVE_SOURCE` | Source mode | S3 | No |
| `TEMP_DIR` | Temp directory | /tmp/encadeador | No |
| `MAX_TEMP_DIR_AGE_HOURS` | Temp cleanup | 24 | No |

### Port Configuration

| Service | Internal | External | Purpose |
|---------|----------|----------|---------|
| encadeador | 8000 | 8001 | API |
| localstack | 4566 | 4566 | S3 mock (dev) |

### Resource Limits

Default Docker limits:
- Memory: 2GB limit, 512MB reservation
- CPU: 2 cores limit, 0.5 cores reservation

Adjust in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '4'
```

## Health Checks

### Endpoints

| Endpoint | Purpose | Expected |
|----------|---------|----------|
| `/health` | Overall health | 200 |
| `/health/live` | Liveness probe | 200 |
| `/health/ready` | Readiness probe | 200 or 503 |

### Checking Health

```bash
# Overall health
curl -s http://localhost:8001/health | jq

# Liveness (container alive)
curl -s http://localhost:8001/health/live | jq

# Readiness (dependencies OK)
curl -s http://localhost:8001/health/ready | jq
```

### Readiness Checks

Readiness probe verifies:
- Temp directory is writable
- S3 is accessible (if configured)

```json
{
  "ready": true,
  "checks": {
    "temp_dir": true,
    "s3": true
  }
}
```

## Traefik Integration

### Labels

The service includes Traefik labels for reverse proxy:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.encadeador.rule=PathPrefix(`/encadeador`)"
  - "traefik.http.services.encadeador.loadbalancer.server.port=8000"
```

### Accessing via Traefik

```bash
curl http://traefik-host/encadeador/health
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs encadeador

# Check container status
docker compose ps -a

# Inspect container
docker inspect encadeador-service
```

### Health Check Failing

```bash
# Check readiness
curl http://localhost:8001/health/ready

# Common issues:
# - S3 credentials missing
# - Temp directory not writable
# - Network issues
```

### S3 Connection Issues

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://decomp-bucket/

# Check endpoint URL (for LocalStack)
curl http://localhost:4566/_localstack/health
```

### High Memory Usage

```bash
# Check container stats
docker stats encadeador-service

# Increase memory limit
# Edit docker-compose.yml memory limit
```

### Logs

```bash
# Docker Compose logs
docker compose logs -f --tail=100 encadeador

# systemd logs
journalctl -u encadeador -f

# Filter errors
journalctl -u encadeador -p err
```

## Monitoring

### Log Format

Logs are JSON-formatted for parsing:
```json
{"timestamp": "...", "level": "INFO", "message": "...", "request_id": "..."}
```

### Metrics

Export metrics to Prometheus (future enhancement):
- Request count
- Request latency
- Error rate
- S3 operation duration

### Alerting

Set up alerts for:
- Health check failures
- High error rate
- S3 connectivity issues

## Security

### Non-Root User

Container runs as non-root user `appuser` (UID 1000).

### Network Security

- Internal port 8000 not exposed directly
- Use Traefik for TLS termination
- Restrict network access via Docker networks

### Secrets Management

- Use IAM roles for AWS credentials in production
- Never commit credentials to repository
- Use environment variables for configuration

## Backup and Recovery

### What to Backup

- `/etc/encadeador/environment` - Configuration
- S3 buckets - Artifacts

### Recovery

1. Restore configuration from backup
2. Re-run installation script
3. Start service
```

## Acceptance Criteria

- [x] Deployment guide created at `docs/DEPLOYMENT.md`
- [x] Docker Compose instructions complete
- [x] systemd instructions complete
- [x] Configuration reference complete
- [x] Health check documentation
- [x] Troubleshooting section
- [x] Security considerations

## Implementation Guide

### Step 1: Create DEPLOYMENT.md

Create the file with content above.

### Step 2: Test instructions

Follow the guide on a clean system to verify accuracy.

### Step 3: Add screenshots/diagrams if helpful

Optional: Add architecture diagram.

## Files to Read Before Starting

- `docker-compose.yml` - Production compose
- `docker-compose.dev.yml` - Dev compose
- `deploy/` - systemd files
- `.env.example` - Environment variables

## Definition of Done

- [x] Deployment guide created
- [x] All deployment methods covered
- [x] Troubleshooting section complete
- [x] Instructions tested
- [x] Changes committed

## Blocked By

- [DOCKER-001](../../epic-05-docker/sprint-01/ticket-001-create-dockerfile.md) - Dockerfile ✅
- [DOCKER-002](../../epic-05-docker/sprint-01/ticket-002-create-docker-compose.md) - Docker Compose ✅
- [DOCKER-003](../../epic-05-docker/sprint-01/ticket-003-create-systemd-service.md) - systemd ✅

## Blocks

- [DOCS-003](./ticket-003-update-readme.md) - README references deployment guide
