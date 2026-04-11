# Kanban Studio

A focused project management application with multiple Kanban boards, AI assistance, and user management.

## Features

- Multi-user support with registration and bcrypt password hashing
- Multiple Kanban boards per user (create, rename, delete)
- Column management: add and delete columns per board
- Drag-and-drop card movement across columns
- Card fields: title, details, priority (low/medium/high), due date, labels/tags
- Card edit modal with label editor
- Activity log per board (card and column events, last 50 entries)
- Column renaming
- AI chat sidebar powered by OpenRouter
- Secure session cookies

## Stack

- **Backend**: FastAPI + SQLAlchemy (async) + SQLite + aiosqlite
- **Frontend**: Next.js (static build) served by FastAPI
- **Auth**: Signed session cookies (itsdangerous), bcrypt password hashing
- **AI**: OpenRouter (`openai/gpt-oss-120b` model)
- **Package manager**: `uv` (Python)

## Project structure

```
backend/       FastAPI app, models, routes, tests
frontend/      Next.js app source
scripts/       Start/stop scripts
docs/          Architecture notes and runbooks
```

## Running locally

```bash
# Backend (from backend/)
uv run uvicorn main:app --reload

# Frontend dev server (from frontend/)
npm run dev
```

The backend serves the built Next.js static files at `/`. For development, run both servers and the frontend dev server proxies `/api/*` to the backend.

## Tests

```bash
# Backend
cd backend && uv run pytest

# Frontend
cd frontend && npm run test
```

## Default credentials

On first run, a default user is seeded:

- Username: `user`
- Password: `password`

Use the registration page to create additional accounts.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-key` | Session signing key (set in production) |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/kanban.db` | SQLite path |
| `STATIC_DIR` | `./static` | Built Next.js output directory |
| `OPENROUTER_API_KEY` | (required for AI) | OpenRouter API key |
