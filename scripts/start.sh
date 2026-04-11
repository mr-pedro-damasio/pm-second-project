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
ENV_FILE="$(dirname "$0")/../.env"
ENV_ARG=""
if [ -f "$ENV_FILE" ]; then
  ENV_ARG="--env-file $ENV_FILE"
fi
docker run -d --name "$CONTAINER" -p "${PORT}:8000" -v kanban-studio-data:/app/data $ENV_ARG "$IMAGE"
echo "Kanban Studio running at http://localhost:${PORT}"
