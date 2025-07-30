#!/bin/bash
# Script for running the application stack locally.
# It loads the local .env file and then hands off to the main start.sh.
set -e

cd "$(dirname "$0")/.." # Move to project root

echo "🟡 Loading environment variables from .env file..."
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
  echo "✅ Environment loaded."
else
  echo "⚠️ .env file not found. Please ensure it exists in the project root."
  exit 1
fi

echo "--- ✅ Local environment ready. Handing off to main start script... ---"

# Execute the main start script to launch all services
exec bash scripts/start.sh