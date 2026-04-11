# Code Review — Kanban Studio (Post-Fix)

**Date:** 2026-04-11  
**Scope:** Full repository — backend, frontend, tests, configuration  
**Reviewer:** Claude Code (automated review)  
**Context:** Second review, taken after all findings from `docs/code_review.md` were resolved.

---

## Severity legend

| Level | Meaning |
|-------|---------|
| MAJOR | Significant bug or incorrect behaviour |
| MINOR | Quality, maintainability, or UX issue |
| DOC | Documentation inaccuracy or stale content |

---

## MAJOR

### M1 — `board_updated: true` returned even when every AI operation fails
**File:** `backend/routes/ai.py:173–177`  
**Issue:** If the AI returns a non-empty `operations` list but every single operation raises an exception (each logged as a warning), the code still sets `board_updated = True` and calls `await db.commit()`. The frontend re-fetches the board and the user is told the board was modified — but nothing actually changed.

```python
# current
if operations:
    await _apply_operations(db, operations)
    await db.commit()
    board_updated = True
```

**Action:** Track successes inside `_apply_operations` and only set `board_updated = True` if at least one operation was applied. One approach: change `_apply_operations` to return a count of successful operations.

---

### M2 — `get_user_board_id` can return `None`; callers pass it unchecked to ownership helpers
**File:** `backend/crud.py:62–64`, `backend/routes/board.py:119–120, 133–134, 146–147, 159–161, 174–175`  
**Issue:** `get_user_board_id` is typed `-> int | None`. All five board route handlers call it and pass the result directly to `_assert_column_owned` or `_assert_card_owned`, both of which are typed `board_id: int`. If `require_user` authenticates a user who somehow has no board (e.g. the seed didn't run, or data was manually deleted), `board_id` is `None` and the ownership query silently produces wrong results or raises a `TypeError` — a 500 instead of a clean 404.

**Action:** Add a guard after each `get_user_board_id` call:

```python
board_id = await crud.get_user_board_id(db, user.id)
if board_id is None:
    raise HTTPException(status_code=404, detail="Board not found")
```

---

## MINOR

### m1 — Dead code in `kanban.ts`: `initialData` and `createId`
**File:** `frontend/src/lib/kanban.ts:18–72, 164–168`  
**Issue:** `initialData` (the hardcoded demo board, ~55 lines) and `createId` are exported but have no importers. Board state now comes from the API; IDs are assigned by the backend. Both symbols ship in the production bundle for no reason.  
**Action:** Delete both exports and their associated data. Confirm with `grep -r "initialData\|createId" src/` — both return only `kanban.ts` itself.

---

### m2 — Dockerfile pins uv as `latest` — non-reproducible builds
**File:** `Dockerfile:11`  
**Issue:** `COPY --from=ghcr.io/astral-sh/uv:latest` means every `docker build` may use a different uv version. A breaking change in uv would silently fail CI or production builds with no obvious cause.  
**Action:** Pin to a specific version, e.g. `ghcr.io/astral-sh/uv:0.6.x`. Check the current version in the devcontainer with `uv --version` and use that.

---

### m3 — `_login` helper still duplicated across three test files
**Files:** `backend/tests/test_board.py:4–7`, `backend/tests/test_ai_ping.py:5–8`, `backend/tests/test_ai_chat.py:5–8`  
**Issue:** The `client` fixture was successfully moved to `conftest.py`, but each file still defines its own identical `_login(client)` function. Any change (different credentials, assertion) must be made in three places.  
**Action:** Move `_login` into `conftest.py` as a module-level function. Test files can import it: `from conftest import _login`.

---

### m4 — `logger` assignment splits the import block in `routes/ai.py`
**File:** `backend/routes/ai.py:4–8`  
**Issue:** The module currently reads:

```python
from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)
from pydantic import BaseModel
```

The `logger` assignment appears between two `from` import statements, breaking the conventional import grouping and making the file harder to scan.  
**Action:** Move `logger = logging.getLogger(__name__)` to after all imports, matching the style in `main.py`.

---

### m5 — `apiFetch` sends `Content-Type: application/json` on requests with no body
**File:** `frontend/src/lib/api.ts:52–54`  
**Issue:** `apiFetch` sets `Content-Type: application/json` unconditionally. `deleteCard` calls it with method `DELETE` and no body — the header is technically harmless but misleading, and some strict proxies may reject or log it.  
**Action:** Only set the `Content-Type` header when a body is present, or pass headers per-call.

---

### m6 — Board fetch errors silently swallowed; user sees empty board
**File:** `frontend/src/components/KanbanBoard.tsx:41`  
**Issue:** `fetchBoard().catch(() => {}).finally(() => setLoading(false))` discards any network or API error. If the backend is unreachable, the loading state clears and the user sees a blank board with no explanation.  
**Action:** Add a simple error state:

```ts
const [error, setError] = useState<string | null>(null);
// …
fetchBoard().catch(() => setError("Could not load the board. Please refresh.")).finally(…)
```

Render it below the header when set.

---

### m7 — Column rename to empty string rolls back silently
**File:** `frontend/src/components/KanbanColumn.tsx:52–55`  
**Issue:** If a user clears the column title and blurs the input, `onRename` is called with `""`. The backend now rejects this with a 422, the optimistic update is rolled back, and the title snaps back — but no message is shown to the user. The interaction feels broken.  
**Action:** Add a client-side guard in `KanbanColumn.tsx`: if `localTitle.trim() === ""`, restore `column.title` immediately without calling `onRename`.

---

### m8 — Path traversal not explicitly guarded in static file serving
**File:** `backend/main.py:112–121`  
**Issue:** `STATIC_DIR / full_path` is not validated to stay within `STATIC_DIR`. Starlette normalises `..` sequences in URL paths before routing, so standard browser requests cannot escape the directory. However, a crafted request from a tool like `curl` with a manually constructed path could potentially reach files outside the static directory if Starlette's normalisation is ever bypassed.  
**Action:** Add an explicit containment check before serving any file:

```python
candidate = STATIC_DIR / full_path
if not str(candidate.resolve()).startswith(str(STATIC_DIR.resolve())):
    raise HTTPException(status_code=404)
```

---

## DOCUMENTATION

### D1 — `frontend/AGENTS.md` has three stale sections
**File:** `frontend/AGENTS.md`  
**Issues:**
1. **File map** (lines 22–43): Missing `AiChat.tsx`, `AiChat.test.tsx`, `api.ts`, `api.test.ts`. These were added in Parts 7 and 10.
2. **Data model section** (lines 47–55): Still describes `initialData` as the board state source and `createId` as an active utility. Both are now dead code.
3. **"What will change in later parts"** (lines 99–106): Describes future work that has already been implemented (API fetch, login page, backend mutations, AI chat sidebar). The section should be removed or replaced with a brief current-state description.

**Action:** Update the file map, remove or rewrite the data model note about `initialData`, and delete the "What will change" section.

---

## What is working well

- All 32 backend tests and 23 frontend unit tests pass.
- Authentication is correct: HTTP-only signed cookie, ownership enforced on every board route.
- Input validation is now present on all title/details fields (`min_length`, `max_length`).
- CSS variable naming is consistent (`--purple-secondary`) across all components.
- Docker volume mount (`kanban-studio-data`) ensures data survives container restarts.
- Playwright default config now targets the correct port (8000) and excludes integration tests.
- AI operation failures are now logged rather than silently discarded.
- Shared test fixture in `conftest.py` eliminates the majority of fixture duplication.
- CORS middleware added for local dev cross-origin requests.
- SECRET_KEY warning fires at startup when the insecure default is in use.
- `docs/architecture/overview.md` and `backend/AGENTS.md` now reflect the fully implemented state.

---

## Recommended fix order

1. **M1** — `board_updated` flag when all operations fail
2. **M2** — `None` board_id causing potential 500 errors
3. **m1** — Delete dead code (`initialData`, `createId`)
4. **m7** — Client-side guard for empty column rename
5. **m6** — Surface board fetch errors to the user
6. **m8** — Explicit path containment check
7. **m2** — Pin uv version in Dockerfile
8. **m3–m5** — Test helper / style / header cleanup
9. **D1** — Update `frontend/AGENTS.md`
