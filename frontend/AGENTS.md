# Frontend — Agent Reference

## Purpose

A full-stack Kanban board application. The Next.js frontend is statically exported and served by a FastAPI backend. Board state is persisted in SQLite via the backend API. An AI chat sidebar lets users manage the board through natural language.

## Tech stack

| Concern | Library | Version |
|---------|---------|---------|
| Framework | Next.js (App Router, static export) | 16.x |
| UI | React | 19.x |
| Language | TypeScript | ^5 |
| Styling | Tailwind CSS v4 | ^4 |
| Drag and drop | @dnd-kit/core, @dnd-kit/sortable, @dnd-kit/utilities | ^6 / ^10 |
| Unit tests | Vitest + React Testing Library | ^3 |
| E2E tests | Playwright | ^1 |

## File map

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx              — root layout, font imports
│   │   ├── page.tsx                — entry point; renders <KanbanBoard />
│   │   ├── globals.css             — Tailwind base + CSS custom properties
│   │   └── login/
│   │       └── page.tsx            — login form; POSTs to /api/auth/login
│   ├── components/
│   │   ├── KanbanBoard.tsx         — root; owns BoardData state, API calls, DndContext
│   │   ├── KanbanBoard.test.tsx    — Vitest/RTL unit tests for board interactions
│   │   ├── KanbanColumn.tsx        — column with droppable zone, rename input, card list
│   │   ├── KanbanCard.tsx          — individual draggable card with remove button
│   │   ├── KanbanCardPreview.tsx   — ghost overlay shown while dragging
│   │   ├── NewCardForm.tsx         — inline form to add a card to a column
│   │   ├── AiChat.tsx              — sidebar chat widget; sends board state + history to AI
│   │   └── AiChat.test.tsx         — Vitest/RTL unit tests for AI chat interactions
│   ├── lib/
│   │   ├── kanban.ts               — data types (Card, Column, BoardData), moveCard()
│   │   ├── kanban.test.ts          — unit tests for moveCard logic
│   │   ├── api.ts                  — typed fetch helpers for all backend routes
│   │   └── api.test.ts             — unit tests for api.ts (fetch mocks)
│   └── test/
│       ├── setup.ts                — Vitest global setup (jest-dom matchers)
│       └── vitest.d.ts             — type augmentation for custom matchers
└── tests/
    ├── kanban.spec.ts              — Playwright e2e tests (board, auth, persistence)
    └── integration/
        └── ai.spec.ts              — AI chat e2e test (requires OPENROUTER_API_KEY)
```

## Data model

Defined in `src/lib/kanban.ts`:

```ts
type Card     = { id: string; title: string; details: string }
type Column   = { id: string; title: string; cardIds: string[] }
type BoardData = { columns: Column[]; cards: Record<string, Card> }
```

Columns hold only an ordered list of card ID strings. Cards are stored in a flat map keyed by ID (normalised structure). IDs are assigned by the backend (`card-{n}`, `col-{n}`) via the helpers in `api.ts`.

Board state is fetched from `GET /api/board` on mount. All mutations call the backend and update local state on success. On API error, state is rolled back to the previous value.

## Key logic

- `moveCard(columns, activeId, overId)` — pure function; handles same-column reorder and cross-column moves. Returns a new columns array. Used for optimistic drag-drop updates before the backend confirms.
- `api.ts` — `toBoardData(ApiBoard)` converts the API response to `BoardData`. `toColId` / `toCardId` / `fromColId` / `fromCardId` translate between numeric backend IDs and string frontend IDs.

## Component responsibilities

| Component | State owned | Events emitted |
|-----------|-------------|----------------|
| `KanbanBoard` | `BoardData`, `loading`, `fetchError`, `busy`, `activeCardId` | none (root) |
| `KanbanColumn` | `localTitle` (rename input) | `onRename`, `onAddCard`, `onDeleteCard` |
| `KanbanCard` | none | `onDelete` |
| `KanbanCardPreview` | none | none |
| `NewCardForm` | local form fields | `onAdd` |
| `AiChat` | `messages`, `input`, `sending` | `onBoardUpdate` callback |

## CSS / design system

CSS custom properties are set in `globals.css` and map to the project colour scheme:

```
--accent-yellow:    #ecad0a   — accent lines, highlights
--primary-blue:     #209dd7   — links, key sections
--purple-secondary: #753991   — submit buttons, important actions
--navy-dark:        #032147   — main headings
--gray-text:        #888888   — supporting text, labels
```

Tailwind v4 is used for layout and spacing. All component styles use Tailwind utility classes referencing these variables via `var(--name)`.

## Running locally (with Docker)

```bash
# From project root
bash scripts/start.sh       # build image and run container at http://localhost:8000
bash scripts/stop.sh        # stop and remove container
```

## Running tests

```bash
cd frontend
npm test                    # Vitest unit tests (23 tests)
npm run test:e2e            # Playwright e2e tests against http://localhost:8000
npx playwright test --config=playwright.integration.config.ts  # AI integration tests
```

## Coding conventions

- Components are named exports (not default exports), except `page.tsx` which uses a default export per Next.js convention.
- No global state library — all state lives in `KanbanBoard` and is passed down via props.
- `data-testid` attributes are present on columns (`column-col-{id}`) and cards (`card-card-{id}`) for test targeting.
- Optimistic updates: local state is updated immediately; on API failure, the previous state is restored.
