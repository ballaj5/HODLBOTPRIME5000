#!/bin/bash
# A robust startup script for the crypto bot container.
set -euo pipefail

LOG_FILE="/workspace/logs/startup.log"
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

# --- Logging Function ---
log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') | $1" | tee -a "$LOG_FILE"
}

log "--- 🚀 Bootstrapping Container ---"

# --- 1. Validate Environment Variables ---
log "Validating environment variables..."
missing_vars=()
# CORRECTED: Added all required variables for the application to function.
required_vars=(
    "TELEGRAM_BOT_TOKEN"
    "TELEGRAM_CHAT_ID"
    "OPENAI_API_KEY"
    "BYBIT_API_KEY"
    "BYBIT_API_SECRET"
    "DB_HOST"
    "DB_USER"
    "DB_PASS"
    "DB_NAME"
    "LLAMA_MODEL_PATH"
)

for var in "${required_vars[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        missing_vars+=("$var")
    fi
done

if (( ${#missing_vars[@]} > 0 )); then
    log "❌ Missing required environment variables: ${missing_vars[*]}"
    exit 1
else
    log "✅ All critical environment variables are set."
fi


# --- 2. Validate Model Path ---
log "Validating LLaMA model path..."
# CORRECTED: Fallback path now points to the correct, expected model file.
if [[ ! -f "$LLAMA_MODEL_PATH" ]]; then
    log "⚠️ LLaMA model not found at $LLAMA_MODEL_PATH."
    log "Attempting to run download script..."
    bash /workspace/scripts/download_llama_model.sh
    if [[ ! -f "$LLAMA_MODEL_PATH" ]]; then
        log "❌ No model available after download attempt. Startup cannot continue."
        exit 1
    fi
fi
log "✅ LLaMA model is ready at $LLAMA_MODEL_PATH"


# --- 3. Check GPU Availability ---
log "Checking for GPU..."
if command -v nvidia-smi &> /dev/null && nvidia-smi --list-gpus | grep -q "GPU"; then
    log "✅ GPU detected: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
else
    log "⚠️ GPU not detected — running in CPU-only mode."
fi


# --- 4. Launch Background Services ---
log "--- Launching Application Services ---"

# Launch the scheduler for retraining and sending alerts
log "🚀 Launching background scheduler..."
python -m src.scheduler.retrain_scheduler &

# Launch the real-time feature manager
log "🚀 Launching real-time feature manager..."
python -m src.data_fetch.realtime_manager &

# Launch the main Streamlit dashboard
# CORRECTED: Path now points to the correct dashboard application file.
log "🚀 Launching main dashboard via Streamlit..."
streamlit run /workspace/src/dashboard/app.py --server.port 8050 &

log "--- ✅ All systems are go. Container is running. ---"

# --- 5. Wait for all background processes ---
# This keeps the script running and allows for graceful shutdown.
wait -n
exit $?