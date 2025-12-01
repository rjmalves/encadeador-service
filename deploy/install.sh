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
