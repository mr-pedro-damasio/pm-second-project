#!/usr/bin/env bash
set -euo pipefail

CONTAINER=kanban-studio

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  docker rm -f "$CONTAINER"
  echo "Kanban Studio stopped."
else
  echo "No container found."
fi
