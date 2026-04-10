from unittest.mock import AsyncMock, patch

import anyio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import crud
import database
import main
from models import Base


async def _setup(url: str):
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sf = async_sessionmaker(engine, expire_on_commit=False)
    async with sf() as db:
        await crud.seed_default_user(db)
    return engine, sf


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "STATIC_DIR", tmp_path)
    (tmp_path / "index.html").write_text("<h1>Hello</h1>")
    engine, sf = anyio.run(_setup, f"sqlite+aiosqlite:///{tmp_path}/test.db")
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", sf)
    async def override():
        async with sf() as s:
            yield s
    main.app.dependency_overrides[database.get_db] = override
    with TestClient(main.app, follow_redirects=False) as c:
        yield c
    main.app.dependency_overrides.clear()
    anyio.run(engine.dispose)


def _login(client):
    r = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    return {"session": r.cookies["session"]}


def test_ping_returns_result(client):
    cookies = _login(client)
    with (
        patch("routes.ai.ai_module.get_api_key", return_value="test-key"),
        patch("routes.ai.ai_module.chat_completion", new=AsyncMock(return_value="4")),
    ):
        r = client.get("/api/ai/ping", cookies=cookies)
    assert r.status_code == 200
    assert r.json() == {"result": "4"}


def test_ping_requires_auth(client):
    r = client.get("/api/ai/ping")
    assert r.status_code == 401


def test_ping_missing_key(client):
    cookies = _login(client)
    with patch("routes.ai.ai_module.get_api_key", side_effect=ValueError("OPENROUTER_API_KEY is not set")):
        r = client.get("/api/ai/ping", cookies=cookies)
    assert r.status_code == 500
    assert "OPENROUTER_API_KEY" in r.json()["detail"]
