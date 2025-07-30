#!/bin/bash
set -e

echo "🚀 Starting local test (GPU)..."

# Step 1: Prepare host data folders
mkdir -p models
mkdir -p data
mkdir -p logs

# Step 2: Ensure LLaMA model exists by calling the main download script
# This removes redundant download logic and standardizes the process.
echo "🧠 Checking for LLaMA model..."
bash ./scripts/download_llama_model.sh

# Step 3: Build Docker image
echo "🐳 Building Docker image..."
docker build -t llama-crypto-bot .

# Step 4: Run container with GPU and correctly mounted volumes
echo "▶️ Running container..."
docker run --rm \
  --gpus all \
  -v "$(pwd)/models:/workspace/models" \
  -v "$(pwd)/data:/workspace/data" \
  -v "$(pwd)/logs:/workspace/logs" \
  --env-file .env \
  llama-crypto-bot