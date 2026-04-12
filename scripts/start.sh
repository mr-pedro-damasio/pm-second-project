#!/usr/bin/env bash
set -euo pipefail

IMAGE=pm-project
CONTAINER=pm-project
PORT=8000
VOLUME=pm-project-data
OLD_VOLUME=kanban-studio-data

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is not installed or not on PATH."
  echo "Install Docker, start it, then rerun ./scripts/start.sh."
  exit 1
fi

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "Removing existing container..."
  docker rm -f "$CONTAINER"
fi

docker build -t "$IMAGE" "$(dirname "$0")/.."

if docker volume ls --format '{{.Name}}' | grep -q "^${OLD_VOLUME}$" && \
   ! docker volume ls --format '{{.Name}}' | grep -q "^${VOLUME}$"; then
  echo "Migrating Docker volume ${OLD_VOLUME} -> ${VOLUME}..."
  docker volume create "$VOLUME" >/dev/null
  docker run --rm -v "${OLD_VOLUME}:/from" -v "${VOLUME}:/to" alpine sh -c 'cp -a /from/. /to/'
fi

ENV_FILE="$(dirname "$0")/../.env"
ENV_ARG=""
if [ -f "$ENV_FILE" ]; then
  ENV_ARG="--env-file $ENV_FILE"
fi
docker run -d --name "$CONTAINER" -p "${PORT}:8000" -v "${VOLUME}:/app/data" $ENV_ARG "$IMAGE"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "Error: container failed to start."
  docker logs "$CONTAINER" || true
  exit 1
fi

echo "pm-project running at http://localhost:${PORT}"
