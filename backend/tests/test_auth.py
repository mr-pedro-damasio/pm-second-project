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
    (tmp_path / "index.html").write_text("<h1>Hello</h1>")
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


def test_login_success(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert "session" in response.cookies


def test_login_wrong_password(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "wrong"},
    )
    assert response.status_code == 401


def test_login_wrong_username(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "password"},
    )
    assert response.status_code == 401


def test_logout_clears_cookie(client):
    login = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert "session" in login.cookies

    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.cookies.get("session", "") == ""


def test_unauthenticated_root_redirects_to_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_authenticated_root_serves_page(client):
    login = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    session_cookie = login.cookies["session"]
    response = client.get("/", cookies={"session": session_cookie})
    assert response.status_code == 200


def test_login_page_accessible_without_session(client):
    import main as m
    (m.STATIC_DIR / "login").mkdir(exist_ok=True)
    (m.STATIC_DIR / "login" / "index.html").write_text("<h1>Login</h1>")
    response = client.get("/login")
    assert response.status_code == 200


def test_login_page_redirects_when_authenticated(client):
    login = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    session_cookie = login.cookies["session"]
    response = client.get("/login", cookies={"session": session_cookie})
    assert response.status_code == 302
    assert response.headers["location"] == "/"


def test_register_creates_user_and_logs_in(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "newuser", "password": "securepass"},
    )
    assert response.status_code == 201
    assert response.json() == {"ok": True}
    assert "session" in response.cookies


def test_register_duplicate_username_returns_409(client):
    client.post("/api/auth/register", json={"username": "alice", "password": "pass123"})
    response = client.post("/api/auth/register", json={"username": "alice", "password": "pass123"})
    assert response.status_code == 409


def test_register_too_short_password_returns_422(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "bob", "password": "123"},
    )
    assert response.status_code == 422


def test_register_invalid_username_chars_returns_422(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "bad user!", "password": "longpassword"},
    )
    assert response.status_code == 422


def test_registered_user_can_login(client):
    client.post("/api/auth/register", json={"username": "charlie", "password": "mypassword"})
    response = client.post("/api/auth/login", json={"username": "charlie", "password": "mypassword"})
    assert response.status_code == 200
    assert "session" in response.cookies
