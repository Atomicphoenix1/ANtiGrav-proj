#!/bin/bash
# Optimization Script: Add Swap and Test Models

echo "------------------------------------------------"
echo "Starting VPS Optimization..."
echo "------------------------------------------------"

# 1. Remove Unwanted Models
echo "[1/5] Removing old models..."
ollama rm llama3.2:1b || true
ollama rm llama3.2:3b || true

# 2. Create Swap File (4GB)
echo "[2/5] Creating 4GB swap file..."
if [ -f /swapfile ]; then
    echo "Swap file already exists, skipping creation."
else
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
    echo "Swap file created and enabled."
fi

# 3. Verify Swap
echo "[3/5] Verifying memory..."
free -h

# 4. Try Qwen 3.5 4B again
echo "[4/5] Testing Qwen 3.5 4B (with swap)..."
echo "(This might be slow due to swap usage)"
ollama run qwen3.5:4b "Hello, tell me a 1-sentence joke."

# 5. Pull and Test Qwen 2.5 1.5B (The faster RAM-friendly alternative)
echo "[5/5] Setting up Qwen 2.5 1.5B (Recommended for 4GB RAM)..."
ollama pull qwen2.5:1.5b
ollama run qwen2.5:1.5b "Hello, tell me a 1-sentence joke."

echo "------------------------------------------------"
echo "Optimization Complete!"
echo "------------------------------------------------"
