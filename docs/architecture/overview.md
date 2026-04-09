# Architecture Overview

## Application

**Kanban Studio** — a single-board Kanban application for product managers. Cards are draggable between columns; columns are renameable. State is client-side only (no backend persistence yet).

## Tech Stack

| Layer     | Technology                                              | Version   |
|-----------|-------------------------------------------------------- |-----------|
| Framework | Next.js (App Router)                                    | 16.1.6    |
| UI        | React                                                   | 19.2.3    |
| Language  | TypeScript                                              | ^5        |
| Styling   | Tailwind CSS v4                                         | ^4        |
| DnD       | @dnd-kit/core, @dnd-kit/sortable, @dnd-kit/utilities   | ^6 / ^10  |
| Testing   | Vitest + React Testing Library (unit), Playwright (e2e)| ^3 / ^1   |
| Runtime   | Node.js 20 LTS                                          |           |

## Repository Structure

```
pm-second-project/
├── frontend/            # Next.js application
│   ├── src/
│   │   ├── app/         # App Router entry (layout, page)
│   │   ├── components/  # KanbanBoard, KanbanColumn, KanbanCard*
│   │   └── lib/         # kanban.ts — pure data model and moveCard logic
│   ├── tests/           # Playwright e2e tests
│   └── package.json
├── backend/             # Placeholder — no implementation yet
├── docs/
│   ├── architecture/    # This file
│   └── runbooks/
├── scripts/
└── .devcontainer/       # Dev container configuration
```

## Frontend Component Map

```
KanbanBoard          — root; owns BoardData state, DndContext
  └─ KanbanColumn    — renders a column; owns rename/add-card UI
       ├─ KanbanCard          — individual draggable card
       ├─ KanbanCardPreview   — drag overlay ghost
       └─ NewCardForm         — inline form to add a card
```

**Data model** (`src/lib/kanban.ts`):
- `BoardData { columns: Column[], cards: Record<string, Card> }`
- Columns store only `cardIds[]`; cards are looked up by id — a normalized structure.
- `moveCard()` handles same-column reorder and cross-column moves.
- `createId(prefix)` generates collision-resistant ids using random + timestamp.

## State Management

All board state lives in a single `useState<BoardData>` in `KanbanBoard`. No global store, no server state. Data resets on page reload.

## Open Questions / Technical Debt

See [open-questions.md](open-questions.md).
