#!/bin/bash
# Cleanup and Fresh Setup Script for Ollama on Ubuntu 24.04

echo "------------------------------------------------"
echo "Starting Cleanup and Setup of Ollama..."
echo "------------------------------------------------"

# 1. Stop and Disable Services
echo "[1/6] Stopping existing services..."
systemctl stop ollama 2>/dev/null || true
systemctl disable ollama 2>/dev/null || true
systemctl stop openclaw 2>/dev/null || true
systemctl disable openclaw 2>/dev/null || true

# 2. Remove Binary and Service Files
echo "[2/6] Removing binaries and service definitions..."
rm -f /usr/local/bin/ollama
rm -f /etc/systemd/system/ollama.service
systemctl daemon-reload

# 3. Clean up Data Directories
echo "[3/6] Cleaning up data directories..."
rm -rf ~/.ollama
rm -rf /usr/share/ollama

# 4. Remove OpenClaw
echo "[4/6] Removing OpenClaw directories..."
# Check common locations
rm -rf ~/openclaw 2>/dev/null || true
rm -rf /opt/openclaw 2>/dev/null || true
# Deep search and remove if anything left (cautious)
find /root /home -name "openclaw" -type d -exec rm -rf {} + 2>/dev/null || true

# 5. Fresh Installation of Ollama
echo "[5/6] Installing Ollama via official script..."
curl -fsSL https://ollama.com/install.sh | sh

# 6. Pull Qwen 3.5 4B Model
echo "[6/6] Pulling qwen3.5:4b model..."
ollama pull qwen3.5:4b

echo "------------------------------------------------"
echo "Cleanup and Setup Complete!"
echo "------------------------------------------------"
echo "Verifying installation:"
ollama list
echo ""
echo "Running a quick test..."
ollama run qwen3.5:4b "Hello, tell me a short joke."
