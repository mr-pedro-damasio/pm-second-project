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
    (tmp_path / "index.html").write_text("<h1>Hello World</h1>")
    monkeypatch.setattr(main, "STATIC_DIR", tmp_path)

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


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_hello(client):
    response = client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "hello world"}


def test_root_serves_html_when_authenticated(client):
    login = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    session_cookie = login.cookies["session"]
    response = client.get("/", cookies={"session": session_cookie})
    assert response.status_code == 200
    assert "hello world" in response.text.lower()
