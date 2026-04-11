#!/usr/bin/env bash
set -euo pipefail

# Keep git happy when the workspace is mounted from the host.
git config --global --add safe.directory "$(pwd)"

# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Ensure the official Claude plugin marketplace is configured.
# Ignore "already exists" style errors.
claude plugins marketplace add anthropics/claude-plugins-official --scope user || true
claude plugins marketplace update claude-plugins-official || true

# Install required plugin from the explicit marketplace.
claude plugins install ralph-loop@claude-plugins-official

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
