#!/bin/bash
# Runpod-specific bootstrap script.
# This script sets up the environment and then hands off to the main start.sh.
set -e

# Set the working directory correctly
cd /workspace

echo "--- ✅ Runpod environment ready. Handing off to main start script... ---"

# Launch the main application using your primary start script
exec bash scripts/start.sh