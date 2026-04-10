# Database Architecture

SQLite via SQLAlchemy (async). DB file path is configured via the `DATABASE_URL` env var, defaulting to `./data/kanban.db`.

## Tables

### users
| Column   | Type             | Constraints        |
|----------|------------------|--------------------|
| id       | INTEGER          | PK, autoincrement  |
| username | TEXT             | UNIQUE, NOT NULL   |

### boards
| Column  | Type    | Constraints              |
|---------|---------|--------------------------|
| id      | INTEGER | PK, autoincrement        |
| user_id | INTEGER | FK → users.id, NOT NULL  |
| title   | TEXT    | NOT NULL                 |

One board per user for MVP. The FK enforces ownership.

### columns
| Column   | Type    | Constraints              |
|----------|---------|--------------------------|
| id       | INTEGER | PK, autoincrement        |
| board_id | INTEGER | FK → boards.id, NOT NULL |
| title    | TEXT    | NOT NULL                 |
| position | INTEGER | NOT NULL                 |

`position` is a 0-based integer. Columns are fetched ordered by `position`.

### cards
| Column    | Type    | Constraints               |
|-----------|---------|---------------------------|
| id        | INTEGER | PK, autoincrement         |
| column_id | INTEGER | FK → columns.id, NOT NULL |
| title     | TEXT    | NOT NULL                  |
| details   | TEXT    | NOT NULL, DEFAULT ''      |
| position  | INTEGER | NOT NULL                  |

`position` is 0-based within a column. Cards are fetched ordered by `position`.

## Indexes

- `ix_columns_board_position` on `columns(board_id, position)`
- `ix_cards_column_position` on `cards(column_id, position)`

## Migration strategy

`SQLAlchemy`'s `Base.metadata.create_all()` runs at application startup. This creates all tables if they do not exist and is a no-op on subsequent starts. There is no down-migration for the MVP.

On first run, if the `user` account has no board, the backend seeds one board with five default columns (Backlog, Discovery, In Progress, Review, Done) and no cards.
