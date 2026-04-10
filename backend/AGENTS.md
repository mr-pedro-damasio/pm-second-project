# Backend — Agent Reference

## Purpose

FastAPI backend that serves the statically-built Next.js frontend and exposes a REST API. Runs inside Docker via uvicorn.

## Tech stack

| Concern | Library |
|---------|---------|
| Framework | FastAPI |
| Server | uvicorn |
| Package manager | uv |
| Database | SQLite via SQLAlchemy (added in Part 6) |
| Testing | pytest + httpx (via FastAPI TestClient) |

## File map

```
backend/
├── main.py          — FastAPI app entry point; API routes and static file serving
├── pyproject.toml   — uv project definition; runtime and dev dependencies
└── tests/
    ├── __init__.py
    └── test_health.py  — tests for /api/health, /api/hello, and static serving
```

## Running locally (outside Docker)

```bash
cd backend
uv sync
uv run uvicorn main:app --reload --port 8000
```

## Running tests

```bash
cd backend
uv sync
uv run pytest
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `STATIC_DIR` | `<backend_dir>/static` | Path to the directory containing the built frontend files |

## What will be added in later parts

- `auth.py` — session cookie auth (Part 4)
- `models.py` — SQLAlchemy ORM models (Part 6)
- `database.py` — DB engine setup and startup init (Part 6)
- `crud.py` — database operations (Part 6)
- `ai.py` — OpenRouter client (Part 8)
- `routes/` — split route modules as the app grows (Part 6+)
