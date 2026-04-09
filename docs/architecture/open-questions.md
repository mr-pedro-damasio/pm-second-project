# Open Questions & Technical Debt

## Open questions

| # | Question | Impact |
|---|----------|--------|
| 1 | What is the backend tech stack? The `backend/` folder is a placeholder with no implementation. | Blocks persistence, auth, and any multi-user features. |
| 2 | Should board state be persisted? Currently resets on every page reload. | Core UX — likely needs a backend or localStorage fallback. |
| 3 | Is multi-user / real-time collaboration in scope? | Affects whether a REST API or WebSocket/CRDT approach is needed. |
| 4 | What deployment target is planned (Vercel, Docker, other)? | May affect Next.js config (`output: 'standalone'`, etc.). |

## Technical debt inherited from imported code

| # | Item | Location |
|---|------|----------|
| 1 | No persistence layer — all state is ephemeral `useState`. | `frontend/src/components/KanbanBoard.tsx` |
| 2 | `initialData` is hardcoded in `lib/kanban.ts`; should eventually come from an API. | `frontend/src/lib/kanban.ts:18` |
| 3 | No authentication or authorization. | Whole app. |
| 4 | `next.config.ts` not reviewed yet — may need tuning for production. | `frontend/next.config.ts` |
| 5 | Playwright tests likely need a base URL configured for CI. | `frontend/playwright.config.ts` |
