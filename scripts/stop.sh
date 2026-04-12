#!/usr/bin/env bash
set -euo pipefail

CONTAINER=pm-project

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  docker rm -f "$CONTAINER"
  echo "pm-project stopped."
else
  echo "No container found."
fi
