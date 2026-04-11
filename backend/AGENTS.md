# Backend — Agent Reference

## Purpose

FastAPI backend that serves the statically-built Next.js frontend and exposes a REST API. Runs inside Docker via uvicorn.

## Tech stack

| Concern | Library |
|---------|---------|
| Framework | FastAPI |
| Server | uvicorn |
| Package manager | uv |
| Database | SQLite via SQLAlchemy async + aiosqlite |
| Auth | itsdangerous signed HTTP-only session cookie |
| AI | openai-compatible client via OpenRouter |
| Testing | pytest + anyio + httpx (via FastAPI TestClient) |

## File map

```
backend/
├── main.py             — FastAPI app entry; auth routes, static serving, session middleware
├── models.py           — SQLAlchemy ORM models (User, Board, KanbanColumn, Card)
├── database.py         — async engine setup, create_all on startup, get_db dependency
├── crud.py             — database operations (get_board, add_card, move_card, rename_column, …)
├── ai.py               — OpenRouter async client (chat_completion, get_api_key)
├── pyproject.toml      — uv project definition; runtime and dev dependencies
├── routes/
│   ├── board.py        — board CRUD routes (/api/board, /api/cards, /api/columns)
│   └── ai.py           — AI routes (/api/ai/ping, /api/ai/chat)
└── tests/
    ├── conftest.py         — shared client fixture and DB setup
    ├── __init__.py
    ├── test_health.py      — /api/health, /api/hello, static serving
    ├── test_auth.py        — login, logout, session redirect behaviour
    ├── test_board.py       — board CRUD routes
    ├── test_ai_ping.py     — /api/ai/ping (mocked OpenRouter)
    └── test_ai_chat.py     — /api/ai/chat with board operations (mocked OpenRouter)
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
uv run pytest
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `STATIC_DIR` | `<backend_dir>/static` | Path to the built frontend files |
| `SECRET_KEY` | `dev-secret-key` | Signs session cookies — **must be set in production** |
| `OPENROUTER_API_KEY` | *(none)* | Required for AI routes; loaded from `.env` or environment |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/kanban.db` | SQLite DB path inside the container |
