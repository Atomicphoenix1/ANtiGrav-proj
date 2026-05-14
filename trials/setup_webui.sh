#!/bin/bash
# Open WebUI Setup Script

echo "------------------------------------------------"
echo "Starting Open WebUI Setup..."
echo "------------------------------------------------"

# 1. Install Docker
echo "[1/3] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo "Docker is already installed."
fi

# 2. Run Open WebUI Container
echo "[2/3] Starting Open WebUI container..."
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main

# 3. Open Firewall
echo "[3/3] Configuring firewall (ufw)..."
if command -v ufw &> /dev/null; then
    ufw allow 3000/tcp
    echo "Port 3000 opened in ufw."
else
    echo "ufw not found, skipping. Ensure port 3000 is open in your Hostinger dashboard."
fi

echo "------------------------------------------------"
echo "Web UI Setup Complete!"
echo "------------------------------------------------"
echo "Access the UI at: http://187.127.224.119:3000"
echo "The first account created will be the Administrator."
