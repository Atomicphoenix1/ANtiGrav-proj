#!/bin/bash
# OpenClaw Setup Script for Ubuntu 24.04

echo "------------------------------------------------"
echo "Starting OpenClaw Setup..."
echo "------------------------------------------------"

# 1. Ensure Prerequisites (Node.js)
echo "[1/4] Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "Node.js not found. Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
else
    echo "Node.js is already installed ($(node -v))."
fi

# 2. Install OpenClaw CLI
echo "[2/4] Installing OpenClaw CLI..."
curl -fsSL https://openclaw.ai/install-cli.sh | bash

# 3. Onboard and Install Daemon
echo "[3/4] Initializing OpenClaw Daemon..."
# Note: onboard might be interactive, but --install-daemon often helps automate
openclaw onboard --install-daemon

# 4. Verification
echo "[4/4] Verifying setup..."
openclaw --version
openclaw doctor

echo "------------------------------------------------"
echo "OpenClaw Setup Complete!"
echo "------------------------------------------------"
echo "You can now run 'openclaw gateway status' to configure your connection."
