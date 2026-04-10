# Project Plan — Kanban Studio MVP

## Status legend
- [ ] not started
- [x] done

---

## Part 1: Plan
Enrich this document and create frontend/AGENTS.md. Get user approval before any implementation.

### Steps
- [x] Read all existing documentation and frontend code
- [x] Write `frontend/AGENTS.md` describing the existing frontend
- [x] Write this enriched PLAN.md with substeps, tests, and success criteria
- [x] User reviews and approves this plan

### Success criteria
- User has approved the plan and given the go-ahead for Part 2.

---

## Part 2: Scaffolding

Set up Docker infrastructure, FastAPI backend serving static HTML, and start/stop scripts. Confirm hello-world works end-to-end.

### Steps
- [x] Create `Dockerfile` in project root:
  - Base image: `python:3.12-slim`
  - Install `uv`, use it to install Python dependencies
  - Copy backend source into image
  - Expose port 8000
- [x] Create `backend/main.py` with FastAPI app:
  - `GET /` — serves static `index.html` (hello world placeholder)
  - `GET /api/health` — returns `{"status": "ok"}`
  - `GET /api/hello` — returns `{"message": "hello world"}`
- [x] Create `backend/pyproject.toml` (uv-managed) with fastapi, uvicorn dependencies
- [x] Create placeholder `frontend/out/index.html` (hello world HTML) for Docker static serving
- [x] Create `scripts/start.sh` (Mac/Linux) — builds and runs the Docker container
- [x] Create `scripts/stop.sh` (Mac/Linux) — stops and removes the container
- [x] Create `scripts/start.bat` (Windows) — same as start.sh for Windows
- [x] Create `scripts/stop.bat` (Windows) — same as stop.sh for Windows
- [x] Update `backend/AGENTS.md` to describe backend structure

### Tests
- `GET /api/health` returns 200 `{"status": "ok"}`
- `GET /api/hello` returns 200 `{"message": "hello world"}`
- `GET /` returns 200 and contains "hello world" text
- Docker container starts and stops cleanly via scripts
- Backend unit test file: `backend/tests/test_health.py`

### Success criteria
- Running `scripts/start.sh` (or `.bat`) builds the image and starts the container.
- Visiting `http://localhost:8000/` in a browser shows hello world HTML.
- `http://localhost:8000/api/health` returns `{"status": "ok"}`.
- `scripts/stop.sh` cleanly stops the container.

---

## Part 3: Add in Frontend

Statically build the Next.js app and serve it from FastAPI. The Kanban board should be live at `/`.

### Steps
- [x] Update `frontend/next.config.ts`: set `output: 'export'` and `distDir: 'out'`
  - Disable image optimization (not supported with static export)
- [x] Update `Dockerfile` to:
  - Stage 1 (node builder): install deps, run `npm run build` in frontend/, produce `frontend/out/`
  - Stage 2 (python runtime): copy `frontend/out/` into image, serve via FastAPI
- [x] Update `backend/main.py` to serve the static Next.js export:
  - File-first lookup, per-page HTML lookup, SPA fallback to `index.html`
- [x] Verify existing Vitest unit tests pass: `npm test` in `frontend/`
- [x] Verify existing Playwright e2e tests pass against the Docker-served app

### Tests
- All existing Vitest unit tests pass (`npm test` in frontend/)
- All existing Playwright e2e tests pass against `http://localhost:8000`
- `GET /` returns 200 and the Kanban board HTML
- `GET /_next/static/...` returns static assets correctly

### Success criteria
- `docker build` completes successfully.
- `http://localhost:8000/` shows the full working Kanban board (drag-drop, rename, add/remove cards).
- All unit and e2e tests pass.

---

## Part 4: Fake user sign-in

Add a login wall. Hardcoded credentials: `user` / `password`. Protected route shows the Kanban. Logout returns to login.

### Steps
- [x] Create `frontend/src/app/login/page.tsx` — full-page login form
  - Fields: username, password
  - On submit: POST to `/api/auth/login`
  - Show error message on failure
- [x] Create `backend` auth routes:
  - `POST /api/auth/login` — validates credentials, sets an HTTP-only session cookie
  - `POST /api/auth/logout` — clears the session cookie
- [x] Add session middleware in FastAPI (use `itsdangerous` signed cookie, or simple token in cookie)
- [x] Protect the board: unauthenticated requests to `/` redirect to `/login`
  - Implemented in FastAPI static serving (static export has no Next.js server, so middleware.ts not used)
- [x] Add a logout button to the board header in `KanbanBoard.tsx`
- [x] Update Dockerfile dependencies if needed

### Tests
- `POST /api/auth/login` with correct credentials returns 200 and sets cookie
- `POST /api/auth/login` with wrong credentials returns 401
- `POST /api/auth/logout` clears the session cookie
- Visiting `/` without a session redirects to `/login`
- Visiting `/login` when already logged in redirects to `/`
- Playwright e2e: full login → see board → logout → see login page flow
- Backend unit tests: `backend/tests/test_auth.py`

### Success criteria
- Unauthenticated users cannot reach the board.
- Login with `user` / `password` works and lands on the Kanban board.
- Logout returns to the login page.
- All tests pass.

---

## Part 5: Database modeling

Propose and document a SQLite schema for persistent Kanban state. Get user sign-off before implementing.

### Steps
- [x] Draft schema covering: `users`, `boards`, `columns`, `cards` tables
- [x] Document schema in `docs/architecture/database.md`
  - Include table definitions, column types, relationships, indexes
  - Include reasoning for any non-obvious choices
- [x] Document any migration strategy (how tables are created on first run)
- [x] User reviews and approves the schema

### Success criteria
- `docs/architecture/database.md` exists and is clear.
- User has explicitly approved the schema before any implementation begins.

---

## Part 6: Backend

Implement the database layer and full CRUD API for board state.

### Steps
- [x] Add SQLAlchemy (async) + aiosqlite to backend dependencies
- [x] Create `backend/models.py` — SQLAlchemy ORM models matching approved schema
- [x] Create `backend/database.py` — engine setup, `create_all()` on startup, DB path from env var (default `./data/kanban.db`)
- [x] Create `backend/crud.py` — database operations (get board, update card, move card, rename column, add card, delete card)
- [x] Add API routes in `backend/routes/board.py`:
  - `GET /api/board` — returns full board state for authenticated user
  - `POST /api/cards` — create a card
  - `PATCH /api/cards/{card_id}` — update card title/details
  - `DELETE /api/cards/{card_id}` — delete a card
  - `PATCH /api/cards/{card_id}/move` — move card to column/position
  - `PATCH /api/columns/{column_id}` — rename column
- [x] On first run, seed one default board for the `user` account with 5 default columns (no cards)
- [x] Backend unit tests for every route in `backend/tests/test_board.py` using a temp file SQLite test DB

### Tests
- Each route returns correct status codes and response shapes
- Moving a card persists correctly in DB
- Renaming a column persists correctly
- Adding and deleting cards updates DB state
- Unauthenticated requests to board routes return 401
- DB is created on startup if it doesn't exist

### Success criteria
- All backend routes tested and passing.
- SQLite file is created on first run at the configured path.
- A Docker restart preserves data (DB file persisted via a volume).

---

## Part 7: Frontend + Backend integration

Replace hardcoded frontend state with live API calls. The board is now persistent.

### Steps
- [x] Create `frontend/src/lib/api.ts` — typed fetch helpers for all board API routes
- [x] Update `KanbanBoard.tsx`:
  - On mount: fetch board state from `GET /api/board`
  - Card add: call `POST /api/cards`, update local state on success
  - Card delete: call `DELETE /api/cards/{id}`, update local state on success
  - Card move (drag end): call `PATCH /api/cards/{id}/move`, update local state optimistically
  - Column rename: call `PATCH /api/columns/{id}` on blur (not on every keystroke)
- [x] Handle loading and error states simply (no spinners — just disable interactions during fetch)
- [x] Remove `initialData` import from `KanbanBoard.tsx`
- [x] Update Playwright e2e tests to cover persistence (reload page, verify state is preserved)
- [x] Add Vitest tests for `api.ts` fetch helpers using simple fetch mocks

### Tests
- Drag-drop persists after page reload
- Column rename persists after page reload
- Add card persists after page reload
- Delete card persists after page reload
- Network error on move does not corrupt local state
- All existing unit tests continue to pass

### Success criteria
- All board interactions are backed by the API.
- Data survives page reloads and container restarts.
- All tests pass.

---

## Part 8: AI connectivity

Wire up OpenRouter. Verify the backend can make an AI call.

### Steps
- [ ] Add `openai` Python package to backend dependencies (OpenRouter is OpenAI-compatible)
- [ ] Create `backend/ai.py` — OpenRouter client using `OPENROUTER_API_KEY` from environment
  - Model: `openai/gpt-oss-120b`
  - Base URL: `https://openrouter.ai/api/v1`
- [ ] Add `GET /api/ai/ping` route — calls the AI with "What is 2+2? Reply with just the number." and returns the response
- [ ] Load `OPENROUTER_API_KEY` from `.env` via `python-dotenv` in backend startup
- [ ] Backend test: `backend/tests/test_ai_ping.py` — mocks the OpenRouter call, verifies the route returns a response

### Tests
- `GET /api/ai/ping` returns 200 with `{"result": "4"}` (or similar)
- If `OPENROUTER_API_KEY` is missing, the route returns a clear 500 error
- Unit test mocks the OpenRouter HTTP call — no real API key needed for tests

### Success criteria
- `GET /api/ai/ping` returns the AI's answer when called with a real API key.
- Tests pass without requiring a real API key (mock-based).

---

## Part 9: AI chat backend

Extend the AI endpoint to accept a user message + conversation history, include the Kanban board state as context, and return structured output (text response + optional board update).

### Steps
- [ ] Define Pydantic response schema `AiResponse`:
  - `message: str` — the AI's reply to the user
  - `board_update: BoardUpdate | None` — optional: list of card create/move/edit/delete operations
- [ ] Define `BoardUpdate` schema with typed operations (create_card, move_card, edit_card, delete_card, rename_column)
- [ ] Create `POST /api/ai/chat` route:
  - Request body: `{ messages: [{role, content}], board: BoardData }`
  - Builds system prompt including current board state as JSON
  - Calls OpenRouter with structured output (JSON schema enforcement)
  - Applies any `board_update` operations to the database
  - Returns `AiResponse`
- [ ] Write a clear system prompt that instructs the AI on the board JSON format and the update operations
- [ ] Backend tests: `backend/tests/test_ai_chat.py`
  - Test with mocked AI response that includes a board update — verify DB is updated
  - Test with mocked AI response with no board update — verify DB is unchanged
  - Test invalid AI response is handled gracefully

### Tests
- Chat endpoint with mocked AI that returns a create_card op → card appears in board
- Chat endpoint with mocked AI that returns a move_card op → card moves in board
- Chat endpoint with no board_update → board unchanged
- Conversation history is passed through correctly to AI

### Success criteria
- `POST /api/ai/chat` correctly interprets AI structured output and applies board mutations.
- All tests pass with mocked AI.

---

## Part 10: AI chat sidebar

Add the chat UI to the frontend. When the AI updates the board, the UI refreshes automatically.

### Steps
- [ ] Create `frontend/src/components/AiChat.tsx` — sidebar chat widget
  - Message list (user + assistant bubbles)
  - Text input + send button
  - Styled using project color scheme (purple submit button, navy headings, etc.)
- [ ] Update `frontend/src/app/page.tsx` (or `KanbanBoard.tsx` layout) to render the sidebar alongside the board
- [ ] Wire `AiChat` to `POST /api/ai/chat`:
  - Send current board state + conversation history with each message
  - On response, update local message list
  - If `board_update` is present in response, re-fetch the full board from `GET /api/board` and update `KanbanBoard` state
- [ ] Pass a `onBoardUpdate` callback or shared state mechanism from `KanbanBoard` to `AiChat` to trigger re-fetch
- [ ] Show a loading indicator in the chat input while waiting for AI response
- [ ] Playwright e2e test: send a chat message asking to create a card, verify the card appears on the board

### Tests
- Sending a message updates the chat message list
- AI response that includes a board update causes the Kanban to re-render with new state
- Send button is disabled while a request is in flight
- Playwright e2e: ask AI to add a card → card appears in correct column

### Success criteria
- The sidebar is visible and functional alongside the Kanban board.
- AI-driven board updates are reflected on the board without a page reload.
- All tests pass.
