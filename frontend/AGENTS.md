# Frontend — Agent Reference

## Purpose

This is a complete, working Next.js Kanban board application. It is frontend-only (no backend, no persistence). It serves as the starting point for the full-stack integration described in the project PLAN.md.

## Tech stack

| Concern | Library | Version |
|---------|---------|---------|
| Framework | Next.js (App Router) | 15.x |
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
│   │   ├── layout.tsx          — root layout, font imports, CSS variables
│   │   ├── page.tsx            — entry point; renders <KanbanBoard />
│   │   └── globals.css         — Tailwind base + CSS custom properties
│   ├── components/
│   │   ├── KanbanBoard.tsx     — root component; owns BoardData state and DndContext
│   │   ├── KanbanColumn.tsx    — column with droppable zone, rename input, card list
│   │   ├── KanbanCard.tsx      — individual draggable card with remove button
│   │   ├── KanbanCardPreview.tsx — ghost overlay shown while dragging
│   │   ├── NewCardForm.tsx     — inline form to add a card to a column
│   │   └── KanbanBoard.test.tsx — Vitest/RTL unit tests for board interactions
│   ├── lib/
│   │   ├── kanban.ts           — data types, initialData, moveCard(), createId()
│   │   └── kanban.test.ts      — unit tests for moveCard logic
│   └── test/
│       ├── setup.ts            — Vitest global setup (jest-dom matchers)
│       └── vitest.d.ts         — type augmentation for custom matchers
└── tests/
    └── kanban.spec.ts          — Playwright e2e tests
```

## Data model

Defined in `src/lib/kanban.ts`:

```ts
type Card   = { id: string; title: string; details: string }
type Column = { id: string; title: string; cardIds: string[] }
type BoardData = { columns: Column[]; cards: Record<string, Card> }
```

Columns hold only an ordered list of card IDs. Cards are stored in a flat map keyed by ID (normalized structure). This makes reordering cheap and avoids duplication.

`initialData` in `kanban.ts` is hardcoded demo data. In later parts this will be replaced by an API fetch.

## Key logic

- `moveCard(columns, activeId, overId)` — pure function; handles same-column reorder and cross-column moves. Returns a new columns array.
- `createId(prefix)` — generates a collision-resistant ID using `Math.random()` + `Date.now()`.

## Component responsibilities

| Component | State owned | Events emitted |
|-----------|-------------|----------------|
| `KanbanBoard` | `BoardData`, `activeCardId` | none (root) |
| `KanbanColumn` | none | `onRename`, `onAddCard`, `onDeleteCard` |
| `KanbanCard` | none | `onDelete` |
| `KanbanCardPreview` | none | none |
| `NewCardForm` | local form fields | `onAdd` |

## CSS / design system

CSS custom properties are set in `globals.css` and map to the project color scheme:

```
--accent-yellow:  #ecad0a
--primary-blue:   #209dd7
--purple-secondary: #753991
--navy-dark:      #032147
--gray-text:      #888888
```

Tailwind v4 is used for layout and spacing. Component-level styles use Tailwind utility classes referencing these variables.

## Running locally (standalone, no Docker)

```bash
cd frontend
npm install
npm run dev       # dev server at http://localhost:3000
npm test          # Vitest unit tests
npm run build     # production static export (once output: 'export' is configured)
npx playwright test  # e2e tests (requires dev or preview server running)
```

## What will change in later parts

- `initialData` in `kanban.ts` will be replaced by an API fetch (`/api/board`).
- A login page/redirect will wrap the board (Part 4).
- All board mutations (add, move, rename, delete) will POST/PATCH to the backend (Part 7).
- An AI chat sidebar will be added alongside `KanbanBoard` (Part 10).
- `next.config.ts` will be updated to `output: 'export'` for static build serving via FastAPI (Part 3).

## Coding conventions

- Components are named exports (not default exports), except `page.tsx` which uses a default export per Next.js convention.
- No global state library — all state lives in `KanbanBoard` and is passed down via props.
- `data-testid` attributes are present on columns (`column-{id}`) and cards (`card-{id}`) for test targeting.
