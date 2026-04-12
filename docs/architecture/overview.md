# Architecture Overview

## Application

**pm-project** — a single-board Kanban application for product managers. Cards are draggable between columns; columns are renameable. Board state is persisted in SQLite and served via a FastAPI backend. An AI chat sidebar lets users create, move, and edit cards through natural language.

## Tech Stack

| Layer     | Technology                                              | Version   |
|-----------|-------------------------------------------------------- |-----------|
| Framework | Next.js (App Router, static export)                     | 16.1.6    |
| UI        | React                                                   | 19.2.3    |
| Language  | TypeScript                                              | ^5        |
| Styling   | Tailwind CSS v4                                         | ^4        |
| DnD       | @dnd-kit/core, @dnd-kit/sortable, @dnd-kit/utilities   | ^6 / ^10  |
| Testing   | Vitest + React Testing Library (unit), Playwright (e2e)| ^3 / ^1   |
| Runtime   | Node.js 20 LTS (build only)                             |           |
| Backend   | FastAPI + uvicorn                                       | latest    |
| Database  | SQLite via SQLAlchemy async + aiosqlite                 |           |
| Auth      | itsdangerous signed HTTP-only session cookie            |           |
| AI        | OpenRouter (openai-compatible) — `openai/gpt-oss-120b` |           |
| Container | Docker (multi-stage: Node builder + Python runtime)     |           |

## Repository Structure

```
pm-project/
├── frontend/            # Next.js application (static export)
│   ├── src/
│   │   ├── app/         # App Router entry (layout, page, login)
│   │   ├── components/  # KanbanBoard, KanbanColumn, KanbanCard, AiChat, …
│   │   └── lib/         # kanban.ts — data types; api.ts — fetch helpers
│   ├── tests/           # Playwright e2e tests
│   │   └── integration/ # Integration tests requiring real API keys (excluded by default)
│   └── package.json
├── backend/             # FastAPI application
│   ├── main.py          # App entry; auth, session, static serving
│   ├── models.py        # SQLAlchemy ORM (User, Board, KanbanColumn, Card)
│   ├── database.py      # Async engine, create_all, get_db
│   ├── crud.py          # DB operations
│   ├── ai.py            # OpenRouter client
│   ├── routes/          # board.py, ai.py
│   └── tests/           # pytest suite (32 tests)
├── docs/
│   ├── architecture/    # This file, database schema
│   └── runbooks/
├── scripts/             # start.sh / stop.sh / start.bat / stop.bat
├── Dockerfile           # Multi-stage build
└── .devcontainer/       # Dev container configuration
```

## Frontend Component Map

```
page.tsx (App Router)
  ├─ KanbanBoard        — root; owns BoardData state, DndContext, API calls
  │    └─ KanbanColumn  — column with droppable zone, rename input, card list
  │         ├─ KanbanCard          — individual draggable card
  │         ├─ KanbanCardPreview   — drag overlay ghost
  │         └─ NewCardForm         — inline form to add a card
  └─ AiChat             — sidebar chat widget; sends board state + history to /api/ai/chat
```

## State Management

Board state lives in a single `useState<BoardData>` in `KanbanBoard`. On mount the board is fetched from `GET /api/board`. All mutations (add, move, rename, delete) call the backend and update local state on success. When the AI returns a `board_updated: true` response, `KanbanBoard` re-fetches the full board.

## Authentication

FastAPI serves the Next.js static export and enforces auth at the file-serving layer. Unauthenticated requests to `/` redirect to `/login`. The login form POSTs to `/api/auth/login`, which sets an HTTP-only signed session cookie. All `/api/` routes except `/api/health` require the session cookie.

## Data Persistence

SQLite database at `./data/kanban.db` inside the container, persisted via a Docker named volume (`pm-project-data`). Schema: `users`, `boards`, `columns`, `cards` — see [database.md](database.md).
