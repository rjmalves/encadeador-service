# Encadeador Service Deployment

This directory contains deployment files for the encadeador-service.

## Files

- `encadeador.service` - systemd service unit file
- `environment.template` - Environment configuration template
- `install.sh` - Installation script
- `uninstall.sh` - Uninstallation script

## Quick Start

### Install

```bash
# Run the install script
./install.sh

# Configure environment
sudo vim /etc/encadeador/environment

# Start the service
sudo systemctl start encadeador

# Check status
sudo systemctl status encadeador
```

### View Logs

```bash
# Follow logs
journalctl -u encadeador -f

# View recent logs
journalctl -u encadeador --since "1 hour ago"
```

### Manage Service

```bash
# Stop
sudo systemctl stop encadeador

# Restart
sudo systemctl restart encadeador

# Disable auto-start
sudo systemctl disable encadeador
```

### Uninstall

```bash
./uninstall.sh
```

## Prerequisites

- Docker installed and running
- Docker network `hpc-network` (created by install script)
- Docker image `encadeador-service:2.0.0` built or pulled

## Building the Image

```bash
# From repository root
docker build -t encadeador-service:2.0.0 .
```

## Configuration

Edit `/etc/encadeador/environment` to configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_VERSION` | Image version tag | 2.0.0 |
| `LOG_LEVEL` | Logging verbosity | INFO |
| `AWS_REGION` | AWS region for S3 | us-east-1 |
| `DEFAULT_DECOMP_BUCKET` | DECOMP S3 bucket | decomp-bucket |
| `DEFAULT_NEWAVE_BUCKET` | NEWAVE S3 bucket | newave-bucket |
| `DECOMP_SOURCE` | Data source mode | S3 |
| `NEWAVE_SOURCE` | Data source mode | S3 |

## Troubleshooting

### Service won't start

1. Check Docker is running: `sudo systemctl status docker`
2. Check image exists: `docker images | grep encadeador`
3. Check network exists: `docker network ls | grep hpc-network`
4. View startup logs: `journalctl -u encadeador -n 50`

### Health check failing

1. Check container is running: `docker ps | grep encadeador`
2. Test health endpoint: `curl http://localhost:8001/health`
3. Check container logs: `docker logs encadeador-service`
