#!/bin/bash
# A more robust script to clean up Docker containers, images, and volumes.

# --- Configuration ---
# Add any Docker IMAGE names you want to KEEP running containers of.
# This is more reliable than container names. Example: "postgres" for your db.
KEEP_IMAGES=("postgres")

echo "🧹 Cleaning up Docker containers..."

# --- Stop and Remove Containers ---
# Temporarily store container IDs to be removed
containers_to_remove=()

# Get all container IDs and their image names
while read -r line; do
  ID=$(echo "$line" | awk '{print $1}')
  IMAGE=$(echo "$line" | awk '{print $2}')
  
  # Check if the container's image is in the keep list
  if [[ ! " ${KEEP_IMAGES[@]} " =~ " ${IMAGE%%:*} " ]]; then
    echo "❌ Marking container for removal: $ID (Image: $IMAGE)"
    containers_to_remove+=("$ID")
  else
    echo "✅ Keeping container from image: $IMAGE"
  fi
done < <(docker ps -a --format "{{.ID}} {{.Image}}")

# Now, stop and remove the marked containers if any exist
if [ ${#containers_to_remove[@]} -gt 0 ]; then
    echo "--- Stopping and removing marked containers ---"
    docker stop "${containers_to_remove[@]}"
    docker rm "${containers_to_remove[@]}"
else
    echo "--- No containers marked for removal ---"
fi

# --- Prune System ---
# This safely removes dangling images, build cache, and unused volumes.
echo "🧹 Pruning dangling images, build cache, and unused volumes..."
docker system prune -f

echo "✅ Docker cleanup complete."