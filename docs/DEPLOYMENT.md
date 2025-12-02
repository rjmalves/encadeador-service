# Deployment Guide

This guide covers deploying the Encadeador Service in production environments.

## Prerequisites

- Docker 24.0+
- Docker Compose v2
- AWS credentials (or MinIO/LocalStack)
- (Optional) Traefik for reverse proxy

## Quick Start

### Using Docker Compose

```bash
# Clone repository
git clone https://github.com/your-org/encadeador-service
cd encadeador-service

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start service
docker compose up -d
```

### Using Install Script

```bash
cd deploy
sudo ./install.sh
```

## Configuration

### Environment Variables

Create a `.env` file in the installation directory:

```env
# Application
HOST=0.0.0.0
PORT=8000
ROOT_PATH=/api/v1/chain
LOG_LEVEL=INFO
APP_VERSION=2.0.0

# AWS S3
AWS_REGION=us-east-1
S3_ENDPOINT_URL=
DEFAULT_DECOMP_BUCKET=decomp-bucket
DEFAULT_NEWAVE_BUCKET=newave-bucket

# Source Mode (S3 or FS)
DECOMP_SOURCE=S3
NEWAVE_SOURCE=S3

# Processing
TEMP_DIR=/tmp/encadeador
ZIP_COMPRESSION_LEVEL=6
MAX_TEMP_DIR_AGE_HOURS=24
```

### AWS Credentials

The service uses the standard boto3 credential chain:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. AWS credentials file (`~/.aws/credentials`)
3. IAM role (for EC2/ECS)

## Deployment Options

### 1. Docker Compose (Recommended)

```bash
docker compose up -d
```

View logs:

```bash
docker compose logs -f
```

Stop service:

```bash
docker compose down
```

### 2. Docker Standalone

```bash
# Build image
docker build -t encadeador-service:latest .

# Run container
docker run -d \
  --name encadeador \
  --restart unless-stopped \
  -p 8001:8000 \
  -v /tmp/encadeador:/tmp/encadeador \
  --env-file .env \
  encadeador-service:latest
```

### 3. systemd Service

Install:

```bash
cd deploy
sudo ./install.sh
```

Manage service:

```bash
sudo systemctl status encadeador
sudo systemctl start encadeador
sudo systemctl stop encadeador
sudo systemctl restart encadeador
```

View logs:

```bash
sudo journalctl -u encadeador -f
```

Uninstall:

```bash
sudo ./deploy/uninstall.sh --purge
```

### 4. Development Mode (with LocalStack)

```bash
# Start with LocalStack for S3 mocking
docker compose -f docker-compose.dev.yml up -d

# Service available at http://localhost:8001
# LocalStack S3 at http://localhost:4566
```

## Traefik Integration

The Docker Compose configuration includes Traefik labels:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.encadeador.rule=PathPrefix(`/encadeador`)"
  - "traefik.http.routers.encadeador.entrypoints=web"
  - "traefik.http.services.encadeador.loadbalancer.server.port=8000"
```

Ensure the container is on the same Docker network as Traefik:

```bash
docker network create hpc-network
```

## Health Checks

### Endpoints

| Endpoint            | Purpose     | Response                                         |
| ------------------- | ----------- | ------------------------------------------------ |
| `GET /health`       | Full status | `{"status": "healthy", "version": "2.0.0", ...}` |
| `GET /health/live`  | Liveness    | `{"status": "ok"}`                               |
| `GET /health/ready` | Readiness   | `{"ready": true, "checks": {...}}`               |

### Docker Health Check

The Dockerfile includes a built-in health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')"
```

### Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

## Monitoring

### Logs

The service logs to stdout in INFO level by default. Configure with:

```env
LOG_LEVEL=DEBUG  # or INFO, WARNING, ERROR
```

View Docker logs:

```bash
docker compose logs -f encadeador
```

View systemd logs:

```bash
journalctl -u encadeador -f
```

### Metrics

Health endpoint provides basic metrics:

```bash
curl http://localhost:8001/health | jq
```

Response includes:

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2024-12-01T12:00:00Z",
  "checks": {
    "temp_dir": true,
    "s3": true
  }
}
```

## Security

### Container Security

- Runs as non-root user (UID 1000)
- Minimal base image (python:3.12-slim)
- No development dependencies in production image
- Read-only filesystem support (except temp dir)

### Network Security

- Only expose port 8000 internally (mapped to 8001 externally)
- Use Traefik for TLS termination
- Configure AWS credentials via IAM roles when possible

### IAM Policy (Minimum Required)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EncadeadorS3Access",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::decomp-bucket",
        "arn:aws:s3:::decomp-bucket/*",
        "arn:aws:s3:::newave-bucket",
        "arn:aws:s3:::newave-bucket/*"
      ]
    }
  ]
}
```

## Scaling

### Horizontal Scaling

For multiple instances:

```yaml
services:
  encadeador:
    deploy:
      replicas: 3
```

### Resource Limits

```yaml
services:
  encadeador:
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 2G
        reservations:
          cpus: "0.5"
          memory: 512M
```

## Troubleshooting

### Container Won't Start

```bash
docker compose logs encadeador
```

Check for:

- Missing environment variables
- Invalid AWS credentials
- Port already in use

### S3 Connection Issues

```bash
# Test S3 connectivity from container
docker exec encadeador python -c "
import boto3
s3 = boto3.client('s3')
print(s3.list_buckets())
"
```

### Health Check Failing

```bash
curl -v http://localhost:8001/health/live
```

Check:

- Service is running
- Port is exposed correctly
- No firewall blocking

### High Memory Usage

```bash
# Check container stats
docker stats encadeador
```

Increase memory limit if needed in docker-compose.yml.

### Temp Directory Issues

```bash
# Check temp directory permissions
docker exec encadeador ls -la /tmp/encadeador/
```

Ensure the temp directory is writable by the container user.

## Backup & Recovery

### Configuration Backup

```bash
tar -czf encadeador-config.tar.gz .env docker-compose.yml
```

### Quick Recovery

```bash
# Pull latest image
docker compose pull

# Restart with fresh container
docker compose down
docker compose up -d
```

## Port Reference

| Service     | Internal Port | External Port | Purpose       |
| ----------- | ------------- | ------------- | ------------- |
| encadeador  | 8000          | 8001          | API           |
| localstack  | 4566          | 4566          | S3 mock (dev) |

## Directory Structure

```
/etc/encadeador/            # systemd config (if using install.sh)
  environment               # Environment variables
/opt/encadeador/            # Application files (if using install.sh)
/tmp/encadeador/            # Temporary processing directory
```
