# Code Review — Kanban Studio MVP

**Date:** 2026-04-11  
**Scope:** Full repository — backend, frontend, tests, configuration, documentation  
**Reviewer:** Claude Code (automated review)

---

## Severity legend

| Level | Meaning |
|-------|---------|
| CRITICAL | Must fix immediately — security or data loss risk |
| MAJOR | Significant bug or broken feature |
| MINOR | Quality or maintainability issue |
| DOC | Documentation inaccuracy or stale content |

---

## CRITICAL

### C1 — AI model name does not match specification
**File:** `backend/ai.py:6`  
**Issue:** The model is hardcoded as `"deepseek/deepseek-chat-v3"`. `AGENTS.md` and `docs/PLAN.md` (Part 8) specify `"openai/gpt-oss-120b"`. If the intention was to change the model, none of the documentation reflects it. If the intention was to use the specified model, the code is wrong.  
**Action:** Align code and docs — either update `ai.py` to use `"openai/gpt-oss-120b"` or update `AGENTS.md` and `PLAN.md` to document the actual model choice.

---

## MAJOR

### M1 — CSS variable name split causes broken styling
**Files:** `frontend/src/app/globals.css:6`, `frontend/src/app/login/page.tsx:83`, `frontend/src/components/AiChat.tsx:78,108`, `frontend/src/components/NewCardForm.tsx:48`  
**Issue:** Two different variable names are in use for the same purple colour:
- `globals.css` defines `--secondary-purple`
- `login/page.tsx` and `AiChat.tsx` reference `var(--purple-secondary)` — **undefined**, so the purple button colour silently falls back and renders incorrectly
- `NewCardForm.tsx` correctly uses `var(--secondary-purple)`

**Action:** Pick one name. `--purple-secondary` matches the `AGENTS.md` colour-scheme table naming convention. Rename the definition in `globals.css` line 6 from `--secondary-purple` to `--purple-secondary` and update `NewCardForm.tsx` to match.

### M2 — Docker container loses database on restart (no volume mount)
**Files:** `scripts/start.sh:19`, `scripts/start.bat:17`  
**Issue:** `docker run` does not mount a volume for the SQLite database. All data is lost when the container is removed or recreated. `docs/PLAN.md` Part 6 success criteria explicitly states "A Docker restart preserves data (DB file persisted via a volume)" — this is not implemented.  
**Action:** Add `-v kanban-studio-data:/app/data` to the `docker run` command in both `start.sh` and `start.bat`.

### M3 — Playwright default config points to wrong port
**Files:** `frontend/playwright.config.ts:10`, `frontend/playwright.docker.config.ts:10`  
**Issue:** `playwright.config.ts` sets `baseURL: "http://127.0.0.1:3000"` (Next.js dev server), but the app runs on FastAPI at port 8000. Running `npm run test:e2e` without specifying the docker config will target a server that is not running in normal usage.  
**Action:** Change `playwright.config.ts` `baseURL` to `http://localhost:8000` so the default is the deployed app. Keep the docker config as-is or remove the duplication.

### M4 — Silent exception swallow in AI operation application
**File:** `backend/routes/ai.py:114-116`  
**Issue:** `_apply_operations()` catches all exceptions with a bare `except Exception: pass`. If the AI returns a valid operation structure but with an invalid `card_id` or `column_id`, the operation silently does nothing. The user sees the AI claim it made a change; the board does not change; there is no error or log entry.  
**Action:** Replace `pass` with `logger.warning("Failed to apply operation %s: %s", op, e)` at minimum. Consider returning a list of failed operations so the chat response can reflect partial failures.

---

## MINOR

### m1 — Duplicate test fixture setup across backend test files
**Files:** `backend/tests/test_board.py:23-44`, `backend/tests/test_ai_ping.py:25-38`, `backend/tests/test_ai_chat.py:25-39`  
**Issue:** Each test file independently re-declares the same async database setup, engine creation, and seeding logic. Any change to the fixture must be made in three places.  
**Action:** Extract shared fixtures into `backend/tests/conftest.py`.

### m2 — No input validation on card/column title fields
**Files:** `backend/routes/board.py` (rename column, update card routes)  
**Issue:** A client can rename a column or card to an empty string `""` via the API. The database schema allows it (`NOT NULL` but not `NOT EMPTY`). Pydantic models accept any string.  
**Action:** Add `Field(..., min_length=1, max_length=200)` to `title` and `details` fields on the relevant request models.

### m3 — Default `SECRET_KEY` is obvious and insecure
**File:** `backend/main.py:19`  
**Issue:** `SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")`. If `SECRET_KEY` is not set in the environment, session cookies are signed with a well-known key that can be forged.  
**Action:** Add a startup warning when the default is used:
```python
if SECRET_KEY == "dev-secret-key":
    logger.warning("Using insecure default SECRET_KEY — set SECRET_KEY env var in production")
```

### m4 — No CORS middleware configured
**File:** `backend/main.py`  
**Issue:** No `CORSMiddleware` is added. This is fine for the current setup (Next.js built output served by FastAPI on the same origin), but it will cause silent failures the moment a developer tries to run the frontend dev server (`localhost:3000`) against the API (`localhost:8000`).  
**Action:** Add `CORSMiddleware` for local development origins, or at minimum document that cross-origin dev setups are not supported.

### m5 — AI e2e test makes real API calls
**File:** `frontend/tests/kanban.spec.ts` (AI chat test block)  
**Issue:** The Playwright AI chat test sends a real request to OpenRouter. It is slow, costs money, requires the key to be set, and is flaky on network issues. The test does have a graceful skip when the key is absent, but it's not marked as an integration test.  
**Action:** Move to a separate `tests/integration/` file so it is excluded from the default `npm run test:e2e` run and only run explicitly.

---

## DOCUMENTATION

### D1 — `docs/architecture/overview.md` describes pre-implementation state
**File:** `docs/architecture/overview.md:31`  
**Issue:** The backend section reads `# Placeholder — no implementation yet`. The backend is now fully implemented with models, database, CRUD, auth, AI routes, and tests.  
**Action:** Update the repository structure section and "State Management" section to reflect the current full-stack architecture.

### D2 — `frontend/AGENTS.md` states wrong Next.js version
**File:** `frontend/AGENTS.md:11`  
**Issue:** Table shows `Next.js 15.x`. `frontend/package.json:21` shows `"next": "16.1.6"`.  
**Action:** Update version to `16.x`.

### D3 — `backend/AGENTS.md` lists only initial scaffolding files
**File:** `backend/AGENTS.md`  
**Issue:** The file map only shows `main.py` and `pyproject.toml`. The implemented backend also includes `models.py`, `database.py`, `crud.py`, `ai.py`, `routes/board.py`, and `routes/ai.py`. The note "more files will be added" is now stale.  
**Action:** Update the file map to reflect the current structure.

### D4 — `AGENTS.md` specifies model `openai/gpt-oss-120b`; code uses different model
**File:** `AGENTS.md:28`  
**Issue:** This is the documentation side of issue C1 above. `AGENTS.md` explicitly specifies the model to use. Either the spec or the code is wrong.  
**Action:** Resolve in conjunction with C1.

---

## What is working well

- All 32 backend tests pass; all 23 frontend unit tests pass.
- Authentication uses HTTP-only session cookies — correct and secure.
- Board API enforces ownership — authenticated users can only access their own board.
- Database schema is well-designed with appropriate indexes.
- Code is clean and modular — no unnecessary abstractions.
- `.env` is in `.gitignore` and not tracked by git.
- `postCreateCommand.sh` has been updated to install `uv` and backend dependencies.

---

## Recommended fix order

1. **C1** — Align AI model between code and docs  
2. **M1** — Fix broken CSS variable (visually broken login/chat buttons)  
3. **M2** — Add Docker volume mount (data loss on restart)  
4. **M3** — Fix Playwright base URL  
5. **M4** — Log silent AI operation failures  
6. **D1–D4** — Update stale documentation  
7. **m1–m5** — Minor quality improvements  
