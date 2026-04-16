#!/usr/bin/env bash
set -euo pipefail

# Keep git happy when the workspace is mounted from the host.
git config --global --add safe.directory "$(pwd)"

# Install Claude Code CLI
curl -fsSL https://claude.ai/install.sh | bash

# Remove legacy npm installation if it exists.
# npm uninstall -g @anthropic-ai/claude-code || true

# Install uv (Python package manager).
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Install backend dependencies.
(cd backend && uv sync)

# Install project dependencies.
(cd frontend && npm install)

# Install Playwright browser for e2e tests.
(cd frontend && npx playwright install chromium --with-deps)

echo "Dev container is ready."
