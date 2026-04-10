#!/usr/bin/env bash
set -euo pipefail

IMAGE=kanban-studio
CONTAINER=kanban-studio
PORT=8000

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "Removing existing container..."
  docker rm -f "$CONTAINER"
fi

docker build -t "$IMAGE" "$(dirname "$0")/.."
docker run -d --name "$CONTAINER" -p "${PORT}:8000" "$IMAGE"
echo "Kanban Studio running at http://localhost:${PORT}"
