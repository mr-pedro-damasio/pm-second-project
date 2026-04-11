import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/kanban.db")

engine = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


_MIGRATIONS = [
    "ALTER TABLE users ADD COLUMN password_hash TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE cards ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'",
    "ALTER TABLE cards ADD COLUMN due_date TEXT",
    "ALTER TABLE cards ADD COLUMN labels TEXT NOT NULL DEFAULT '[]'",
]


async def init_db() -> None:
    # Ensure data directory exists for file-based SQLite
    if "///" in DATABASE_URL and ":memory:" not in DATABASE_URL:
        db_path = DATABASE_URL.split("///", 1)[1]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Apply additive column migrations — safe to run every startup;
        # SQLite raises OperationalError if the column already exists, which we ignore.
        for sql in _MIGRATIONS:
            try:
                await conn.exec_driver_sql(sql)
            except Exception:
                pass


async def get_db():
    async with SessionLocal() as session:
        yield session
