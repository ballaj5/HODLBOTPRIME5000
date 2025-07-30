#!/bin/bash
set -e

# CORRECTED PATH
MODEL_DIR="/workspace/models"
MODEL_FILE="llama-model.gguf"
MODEL_PATH="${MODEL_DIR}/${MODEL_FILE}"

# Primary: Hugging Face
PRIMARY_URL="https://huggingface.co/TheBloke/Llama-3-8B-Instruct-GGUF/resolve/main/llama-3-8b-instruct-q4_K_M.gguf"

# Fallback: Alternative mirror
FALLBACK_URL="https://huggingface.co/quant-fallbacks/llama-3-8B-instruct-gguf/resolve/main/llama-3-8b-instruct-q4_K_M.gguf"

echo "🧠 Checking for LLaMA model at: $MODEL_PATH"
mkdir -p "$MODEL_DIR"

if [ -f "$MODEL_PATH" ]; then
    echo "✅ LLaMA model already exists. Skipping download."
    exit 0
fi

echo "📥 LLaMA model not found. Starting download..."
echo "➡️ Attempting download from Hugging Face..."

# Attempt download from primary
if curl -L --connect-timeout 15 --max-time 300 -C - "$PRIMARY_URL" -o "$MODEL_PATH"; then
    echo "✅ Downloaded from Hugging Face."
else
    echo "⚠️ Hugging Face download failed. Trying fallback..."
    rm -f "$MODEL_PATH"
    if curl -L --connect-timeout 15 --max-time 300 -C - "$FALLBACK_URL" -o "$MODEL_PATH"; then
        echo "✅ Downloaded from fallback mirror."
    else
        echo "❌ Both primary and fallback downloads failed. Exiting."
        rm -f "$MODEL_PATH"
        exit 1
    fi
fi

# Final check
if [ -f "$MODEL_PATH" ]; then
    echo "🧠 LLaMA model is ready at: $MODEL_PATH"
else
    echo "❌ Model file missing after both attempts."
    exit 1
fi