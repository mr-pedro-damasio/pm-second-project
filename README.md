# project-template-devcontainer

This repository is a minimal project template focused on a reproducible VS Code Dev Container setup.

It gives you a ready-to-use Ubuntu-based development environment with common utilities, Node.js, useful editor extensions, and post-create bootstrapping.

## What this template contains

- `.devcontainer/devcontainer.json`: Main Dev Container configuration.
- `.devcontainer/Dockerfile`: Base image and OS-level packages.
- `.devcontainer/postCreateCommand.sh`: One-time setup that runs after container creation.
- `AGENTS.md`: Agent workflow and contribution guardrails.
- `CLAUDE.md`: Claude-specific quick start that references `@AGENTS.md` and `PLAN.md`.
- `PLAN.md`: Living implementation plan/checklist template.

## Project scaffolding

This template now includes a practical default structure:

```text
.
|-- .devcontainer/
|-- .github/workflows/
|-- .vscode/
|-- config/
|-- docs/
|   |-- architecture/
|   `-- runbooks/
|-- scripts/
|-- src/
|-- tests/
|-- AGENTS.md
|-- CLAUDE.md
|-- PLAN.md
`-- README.md
```

Use this as a starting point and trim/expand to match your stack.

## Quick start

1. Open this folder in VS Code.
2. Run the command: `Dev Containers: Reopen in Container`.
3. Wait for the build and post-create setup to complete.

When setup finishes, the script prints:

`Dev container is ready.`

## Environment details

The container is built from:

- `mcr.microsoft.com/devcontainers/base:ubuntu`

During image build, these packages are installed:

- `build-essential`
- `curl`
- `ca-certificates`

Dev Container features enabled:

- `common-utils` (with Zsh installed and configured as default shell, package upgrades enabled)
- `node` (Node.js tooling)

## VS Code customization included

The template auto-installs these extensions in the container:

- `ms-azuretools.vscode-docker`
- `eamodio.gitlens`
- `esbenp.prettier-vscode`
- `google.geminicodeassist`
- `anthropic.claude-code`

## Post-create automation

After the container is created, VS Code runs:

- `bash .devcontainer/postCreateCommand.sh`

This script does the following:

1. Marks the mounted workspace as a safe Git directory.
2. Installs the Claude Code CLI globally:
   - `npm install -g @anthropic-ai/claude-code`
3. Ensures the official Claude plugin marketplace is configured.
4. Installs the plugin:
   - `ralph-loop@claude-plugins-official`

If marketplace setup commands report "already exists" style errors, the script continues safely.

## How to customize this template

## 1) Add more language/tool features

Edit `.devcontainer/devcontainer.json` and add entries under `features`.

## 2) Add apt packages

Edit `.devcontainer/Dockerfile` and extend the `apt-get install` list.

## 3) Add bootstrap steps

Edit `.devcontainer/postCreateCommand.sh` for tools that should be installed after container creation.

Tips:

- Keep `set -euo pipefail` in shell scripts for safer execution.
- Use idempotent commands where possible so rebuilds do not fail.

## Rebuild and troubleshoot

- Rebuild container after Dockerfile or feature changes:
  - `Dev Containers: Rebuild Container`
- If post-create setup fails, inspect terminal output and rerun manually:
  - `bash .devcontainer/postCreateCommand.sh`

## Template intent

Use this template as a base for any repository where you want:

- Consistent local development environments
- Fast onboarding for new contributors
- Reduced "works on my machine" drift

Add your project code and project-specific docs on top of this foundation.