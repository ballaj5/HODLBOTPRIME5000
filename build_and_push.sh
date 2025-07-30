#!/bin/bash
#
# This script builds the Docker image, tags it with a unique version and 'latest',
# and pushes both tags to Docker Hub.
#
set -e

# --- Configuration ---
# IMPORTANT: Replace these with your Docker Hub username and the desired image name.
DOCKER_HUB_USERNAME="ballaj5"
IMAGE_NAME="hodlbotv1.f"

# --- Versioning ---
# Generates a unique version tag based on the current timestamp (e.g., 20230915-224501)
VERSION_TAG=$(date +%Y%m%d-%H%M%S)

# --- Script Start ---
echo "--------------------------------------------------"
echo "🚀 Starting Docker build and push process..."
echo "--------------------------------------------------"
echo "Image: ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}"
echo "Tags:  latest, ${VERSION_TAG}"
echo "--------------------------------------------------"

# --- 1. Docker Login ---
# Prompts for your Docker Hub credentials to ensure you are authenticated.
echo "🔐 Please log in to Docker Hub..."
docker login -u "$DOCKER_HUB_USERNAME"

# --- 2. Build the Docker Image ---
# Builds the image from the Dockerfile in the current directory.
# It applies both the 'latest' tag and the unique version tag simultaneously.
echo "🛠️ Building Docker image..."
docker build -t "${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${VERSION_TAG}" -t "${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest" .

# --- 3. Push the Docker Image ---
# Pushes both the 'latest' and the version-specific tag to Docker Hub.
echo "⬆️ Pushing 'latest' tag to Docker Hub..."
docker push "${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest"

echo "⬆️ Pushing version tag '${VERSION_TAG}' to Docker Hub..."
docker push "${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${VERSION_TAG}"

echo "--------------------------------------------------"
echo "✅ Success! Image has been built and pushed."
echo "--------------------------------------------------"
