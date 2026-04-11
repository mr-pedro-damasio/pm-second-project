# PLAN

## Current status: Active development

## Completed milestones

### MVP (v0.1)
- [x] FastAPI backend with SQLite database
- [x] NextJS frontend served as static files
- [x] Single Kanban board per user
- [x] Drag-and-drop card movement
- [x] Column renaming
- [x] Card create / delete
- [x] AI chat sidebar (OpenRouter)
- [x] Session cookie authentication (hardcoded user)
- [x] Docker-ready setup
- [x] Basic test suite (auth, health, board CRUD)

### v0.2 — User management + multiple boards
- [x] Password hashing with bcrypt (direct, no passlib)
- [x] User registration endpoint (`POST /api/auth/register`)
- [x] Login validates against hashed passwords in database
- [x] Multiple boards per user (create, rename, delete)
- [x] `GET /api/boards` — list all boards for authenticated user
- [x] `POST /api/boards` — create a board (seeded with default 5 columns)
- [x] `GET /api/boards/{id}` — fetch specific board
- [x] `PATCH /api/boards/{id}` — rename board
- [x] `DELETE /api/boards/{id}` — delete board (not allowed if last board)
- [x] Cascade delete: removing a board deletes its columns and cards
- [x] Ownership isolation: users cannot access each other's boards/columns/cards
- [x] Board selector UI (dropdown with create/rename/delete)
- [x] Registration form on login page (toggle between login and register)
- [x] Updated backend integration tests (47 tests passing)
- [x] Updated frontend unit tests (23 tests passing)

### v0.3 — Card enhancements
- [x] Card priority field (low / medium / high)
- [x] Card due date field
- [x] Card detail modal / expanded view
- [x] Card labels / tags (up to 10 per card, stored as JSON)
- [x] 94 backend tests passing, 53 frontend tests passing

### v0.4 — Board management
- [x] Column management: add new columns, delete columns (with last-column guard)
- [x] Activity log per board (card created/deleted/moved, column added/deleted)
- [x] GET /api/boards/{board_id}/activity — last 50 entries, most recent first
- [x] POST /api/boards/{board_id}/columns — add column
- [x] DELETE /api/columns/{column_id} — delete column (cascade deletes cards)
- [x] Activity panel togglable in UI

## Backlog / next iterations

### v0.5 — Board collaboration
- [ ] Board sharing (read or write access)
- [ ] User profile / password change endpoint

### v0.6 — UI polish
- [ ] Mobile-responsive layout
- [ ] Dark mode
- [ ] Keyboard shortcuts

## Architecture

- **Backend**: FastAPI + SQLAlchemy (async) + SQLite
- **Frontend**: Next.js (static export) served by FastAPI
- **Auth**: Signed cookie sessions (itsdangerous), bcrypt password hashing
- **AI**: OpenRouter via `/api/ai/chat` and `/api/ai/ping`
- **Tests**: pytest (backend), vitest + testing-library (frontend)
