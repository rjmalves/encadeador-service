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
