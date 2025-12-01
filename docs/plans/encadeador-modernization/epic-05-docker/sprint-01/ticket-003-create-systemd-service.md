# [DOCKER-003] Create systemd Service Files

> **Epic**: [Epic 05: Docker & Deployment](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 2  
> **Priority**: P0

## Context

### Background

systemd service files enable the Docker container to start automatically on boot and restart on failure. This provides production-grade service management without Kubernetes.

### Relation to Epic

Enables production deployment on standard Linux servers.

### Current State

Service is managed by PM2. No systemd integration.

## Specification

### Service File

**Path**: `deploy/encadeador.service`

```ini
[Unit]
Description=Encadeador Service (Docker)
Documentation=https://github.com/your-org/encadeador-service
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=simple
User=root
Group=docker

# Environment file for configuration
EnvironmentFile=-/etc/encadeador/environment

# Working directory
WorkingDirectory=/opt/encadeador

# Pre-start: Pull latest image and stop existing container
ExecStartPre=-/usr/bin/docker stop encadeador-service
ExecStartPre=-/usr/bin/docker rm encadeador-service
ExecStartPre=/usr/bin/docker pull encadeador-service:${APP_VERSION:-2.0.0}

# Start command
ExecStart=/usr/bin/docker run --rm \
    --name encadeador-service \
    --env-file /etc/encadeador/environment \
    -p 8001:8000 \
    --health-cmd="curl -f http://localhost:8000/health/live || exit 1" \
    --health-interval=30s \
    --health-timeout=10s \
    --health-retries=3 \
    --memory=2g \
    --cpus=2 \
    --label "traefik.enable=true" \
    --label "traefik.http.routers.encadeador.rule=PathPrefix(\`/encadeador\`)" \
    --label "traefik.http.services.encadeador.loadbalancer.server.port=8000" \
    --network hpc-network \
    encadeador-service:${APP_VERSION:-2.0.0}

# Stop command
ExecStop=/usr/bin/docker stop encadeador-service

# Restart policy
Restart=always
RestartSec=10s

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=encadeador

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Environment File Template

**Path**: `deploy/environment.template`

```bash
# Encadeador Service Environment Configuration
# Copy to /etc/encadeador/environment and customize

# Application version
APP_VERSION=2.0.0

# Logging
LOG_LEVEL=INFO

# AWS Configuration
AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID=  # Use IAM roles in production
# AWS_SECRET_ACCESS_KEY=  # Use IAM roles in production

# S3 Configuration
DEFAULT_DECOMP_BUCKET=decomp-bucket
DEFAULT_NEWAVE_BUCKET=newave-bucket
# S3_ENDPOINT_URL=  # Only for LocalStack/MinIO

# Source mode (S3 or FS)
DECOMP_SOURCE=S3
NEWAVE_SOURCE=S3

# Processing
TEMP_DIR=/tmp/encadeador
MAX_TEMP_DIR_AGE_HOURS=24
ZIP_COMPRESSION_LEVEL=6
```

### Installation Script

**Path**: `deploy/install.sh`

```bash
#!/bin/bash
# Install encadeador-service systemd unit

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing encadeador-service..."

# Create configuration directory
sudo mkdir -p /etc/encadeador
sudo mkdir -p /opt/encadeador

# Copy service file
sudo cp "${SCRIPT_DIR}/encadeador.service" /etc/systemd/system/

# Copy environment template if not exists
if [ ! -f /etc/encadeador/environment ]; then
    sudo cp "${SCRIPT_DIR}/environment.template" /etc/encadeador/environment
    echo "Created /etc/encadeador/environment - please configure before starting"
fi

# Set permissions
sudo chmod 600 /etc/encadeador/environment
sudo chown root:root /etc/encadeador/environment

# Create Docker network if not exists
docker network create hpc-network 2>/dev/null || true

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable encadeador.service

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Edit /etc/encadeador/environment with your configuration"
echo "  2. Start the service: sudo systemctl start encadeador"
echo "  3. Check status: sudo systemctl status encadeador"
echo "  4. View logs: journalctl -u encadeador -f"
```

### Uninstall Script

**Path**: `deploy/uninstall.sh`

```bash
#!/bin/bash
# Uninstall encadeador-service systemd unit

set -euo pipefail

echo "Uninstalling encadeador-service..."

# Stop and disable service
sudo systemctl stop encadeador.service 2>/dev/null || true
sudo systemctl disable encadeador.service 2>/dev/null || true

# Remove service file
sudo rm -f /etc/systemd/system/encadeador.service

# Reload systemd
sudo systemctl daemon-reload

echo ""
echo "Uninstallation complete!"
echo "Configuration at /etc/encadeador/ was preserved."
echo "Remove manually if no longer needed."
```

### Management Commands

| Command | Purpose |
|---------|---------|
| `sudo systemctl start encadeador` | Start service |
| `sudo systemctl stop encadeador` | Stop service |
| `sudo systemctl restart encadeador` | Restart service |
| `sudo systemctl status encadeador` | Check status |
| `journalctl -u encadeador -f` | View logs |
| `journalctl -u encadeador --since "1 hour ago"` | Recent logs |

## Acceptance Criteria

- [x] Service file created with all configurations
- [x] Environment template with all variables
- [x] Installation script created
- [x] Uninstall script created
- [x] Service starts via systemctl
- [x] Service restarts on failure
- [x] Logs available via journalctl
- [x] Docker network handling

## Implementation Guide

### Step 1: Create deploy directory

```bash
mkdir -p deploy
```

### Step 2: Create service files

Create all files in the `deploy/` directory as specified.

### Step 3: Make scripts executable

```bash
chmod +x deploy/install.sh deploy/uninstall.sh
```

### Step 4: Test on target system

```bash
# Copy files to server
scp -r deploy/ user@server:/tmp/encadeador-deploy/

# SSH to server
ssh user@server

# Run installation
cd /tmp/encadeador-deploy
sudo ./install.sh

# Configure environment
sudo vim /etc/encadeador/environment

# Start service
sudo systemctl start encadeador

# Check status
sudo systemctl status encadeador
journalctl -u encadeador -f
```

### Step 5: Verify restart behavior

```bash
# Kill container to test restart
docker kill encadeador-service

# Service should restart automatically within 10s
sleep 15
docker ps | grep encadeador
```

## Files to Read Before Starting

- `/home/rogerio/git/flexibilizador-service/deploy/` - Reference implementation
- systemd documentation
- Docker systemd integration guides

## Testing Requirements

### Installation Tests

- [ ] install.sh runs without errors
- [ ] Service file copied correctly
- [ ] Environment file created
- [ ] Service enabled in systemd

### Runtime Tests

- [x] Service starts via systemctl
- [x] Health check passes
- [x] Logs visible in journalctl
- [x] Restart on container crash

## Definition of Done

- [x] Service file created
- [x] Environment template created
- [x] Install script created
- [x] Uninstall script created
- [x] Tested on target system
- [x] Documentation in deploy/README.md
- [x] Changes committed

## Blocked By

- [DOCKER-001](./ticket-001-create-dockerfile.md) - Dockerfile
- [DOCKER-002](./ticket-002-create-docker-compose.md) - Docker Compose

## Blocks

- [DOCS-002](../../epic-06-documentation/sprint-01/ticket-002-create-deployment-guide.md) - Deployment guide
