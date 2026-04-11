import anyio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import crud
import database
import main
from models import Base


async def _setup_db(url: str):
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db:
        await crud.seed_default_user(db)
    return engine, session_factory


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "STATIC_DIR", tmp_path)
    (tmp_path / "index.html").write_text("<h1>Hello</h1>")

    db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
    engine, session_factory = anyio.run(_setup_db, db_url)

    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", session_factory)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    main.app.dependency_overrides[database.get_db] = override_get_db

    with TestClient(main.app, follow_redirects=False) as c:
        yield c

    main.app.dependency_overrides.clear()
    anyio.run(engine.dispose)


def login(client: TestClient) -> dict:
    r = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert r.status_code == 200
    return {"session": r.cookies["session"]}
