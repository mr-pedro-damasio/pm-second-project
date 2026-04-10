import anyio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import crud
import database
import main
from models import Base


async def _setup_test_db(url: str):
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
    engine, session_factory = anyio.run(_setup_test_db, db_url)

    # Point the app at the test DB so lifespan reuses it
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


def _login(client: TestClient) -> dict:
    r = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert r.status_code == 200
    return {"session": r.cookies["session"]}


# --- GET /api/board ---

def test_board_requires_auth(client):
    r = client.get("/api/board")
    assert r.status_code == 401


def test_get_board_returns_five_columns(client):
    cookies = _login(client)
    r = client.get("/api/board", cookies=cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "My Board"
    assert len(data["columns"]) == 5
    assert data["columns"][0]["title"] == "Backlog"


# --- POST /api/cards ---

def test_create_card(client):
    cookies = _login(client)
    board = client.get("/api/board", cookies=cookies).json()
    col_id = board["columns"][0]["id"]

    r = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "New card", "details": "Some details"},
        cookies=cookies,
    )
    assert r.status_code == 201
    card = r.json()
    assert card["title"] == "New card"
    assert card["details"] == "Some details"


def test_create_card_requires_auth(client):
    r = client.post("/api/cards", json={"column_id": 1, "title": "x"})
    assert r.status_code == 401


def test_create_card_wrong_column(client):
    cookies = _login(client)
    r = client.post(
        "/api/cards",
        json={"column_id": 9999, "title": "x"},
        cookies=cookies,
    )
    assert r.status_code == 404


# --- PATCH /api/cards/{id} ---

def test_update_card(client):
    cookies = _login(client)
    board = client.get("/api/board", cookies=cookies).json()
    col_id = board["columns"][0]["id"]
    card = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "Original"},
        cookies=cookies,
    ).json()

    r = client.patch(
        f"/api/cards/{card['id']}",
        json={"title": "Updated", "details": "New details"},
        cookies=cookies,
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Updated"
    assert r.json()["details"] == "New details"


# --- DELETE /api/cards/{id} ---

def test_delete_card(client):
    cookies = _login(client)
    board = client.get("/api/board", cookies=cookies).json()
    col_id = board["columns"][0]["id"]
    card = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "To delete"},
        cookies=cookies,
    ).json()

    r = client.delete(f"/api/cards/{card['id']}", cookies=cookies)
    assert r.status_code == 204

    board = client.get("/api/board", cookies=cookies).json()
    col_cards = next(c for c in board["columns"] if c["id"] == col_id)["cards"]
    assert not any(c["id"] == card["id"] for c in col_cards)


def test_delete_card_requires_auth(client):
    r = client.delete("/api/cards/1")
    assert r.status_code == 401


# --- PATCH /api/cards/{id}/move ---

def test_move_card_to_different_column(client):
    cookies = _login(client)
    board = client.get("/api/board", cookies=cookies).json()
    src_col_id = board["columns"][0]["id"]
    dst_col_id = board["columns"][1]["id"]

    card = client.post(
        "/api/cards",
        json={"column_id": src_col_id, "title": "Moving card"},
        cookies=cookies,
    ).json()

    r = client.patch(
        f"/api/cards/{card['id']}/move",
        json={"column_id": dst_col_id, "position": 0},
        cookies=cookies,
    )
    assert r.status_code == 200
    assert r.json()["column_id"] == dst_col_id

    board = client.get("/api/board", cookies=cookies).json()
    dst_cards = next(c for c in board["columns"] if c["id"] == dst_col_id)["cards"]
    assert any(c["id"] == card["id"] for c in dst_cards)


def test_move_card_persists(client):
    cookies = _login(client)
    board = client.get("/api/board", cookies=cookies).json()
    src_id = board["columns"][0]["id"]
    dst_id = board["columns"][4]["id"]

    card = client.post(
        "/api/cards", json={"column_id": src_id, "title": "Persist test"}, cookies=cookies
    ).json()
    client.patch(
        f"/api/cards/{card['id']}/move",
        json={"column_id": dst_id, "position": 0},
        cookies=cookies,
    )

    board = client.get("/api/board", cookies=cookies).json()
    dst_cards = next(c for c in board["columns"] if c["id"] == dst_id)["cards"]
    assert any(c["id"] == card["id"] for c in dst_cards)


# --- PATCH /api/columns/{id} ---

def test_rename_column(client):
    cookies = _login(client)
    board = client.get("/api/board", cookies=cookies).json()
    col_id = board["columns"][0]["id"]

    r = client.patch(
        f"/api/columns/{col_id}",
        json={"title": "Renamed"},
        cookies=cookies,
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Renamed"


def test_rename_column_persists(client):
    cookies = _login(client)
    board = client.get("/api/board", cookies=cookies).json()
    col_id = board["columns"][2]["id"]

    client.patch(f"/api/columns/{col_id}", json={"title": "New Name"}, cookies=cookies)

    board = client.get("/api/board", cookies=cookies).json()
    col = next(c for c in board["columns"] if c["id"] == col_id)
    assert col["title"] == "New Name"


def test_rename_column_requires_auth(client):
    r = client.patch("/api/columns/1", json={"title": "x"})
    assert r.status_code == 401
