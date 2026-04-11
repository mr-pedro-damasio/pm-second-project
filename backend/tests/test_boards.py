"""Tests for multi-board management endpoints."""
import pytest

from conftest import login as _login


# --- GET /api/boards ---

def test_list_boards_requires_auth(client):
    r = client.get("/api/boards")
    assert r.status_code == 401


def test_list_boards_returns_default_board(client):
    cookies = _login(client)
    r = client.get("/api/boards", cookies=cookies)
    assert r.status_code == 200
    boards = r.json()
    assert len(boards) == 1
    assert boards[0]["title"] == "My Board"


# --- POST /api/boards ---

def test_create_board_requires_auth(client):
    r = client.post("/api/boards", json={"title": "New"})
    assert r.status_code == 401


def test_create_board(client):
    cookies = _login(client)
    r = client.post("/api/boards", json={"title": "Sprint Board"}, cookies=cookies)
    assert r.status_code == 201
    board = r.json()
    assert board["title"] == "Sprint Board"
    assert len(board["columns"]) == 5


def test_create_board_appears_in_list(client):
    cookies = _login(client)
    client.post("/api/boards", json={"title": "Second Board"}, cookies=cookies)
    r = client.get("/api/boards", cookies=cookies)
    titles = [b["title"] for b in r.json()]
    assert "Second Board" in titles
    assert "My Board" in titles


def test_create_board_empty_title_rejected(client):
    cookies = _login(client)
    r = client.post("/api/boards", json={"title": ""}, cookies=cookies)
    assert r.status_code == 422


# --- GET /api/boards/{board_id} ---

def test_get_board_by_id(client):
    cookies = _login(client)
    boards = client.get("/api/boards", cookies=cookies).json()
    board_id = boards[0]["id"]

    r = client.get(f"/api/boards/{board_id}", cookies=cookies)
    assert r.status_code == 200
    assert r.json()["id"] == board_id
    assert r.json()["title"] == "My Board"
    assert len(r.json()["columns"]) == 5


def test_get_board_not_found(client):
    cookies = _login(client)
    r = client.get("/api/boards/99999", cookies=cookies)
    assert r.status_code == 404


def test_get_board_requires_auth(client):
    r = client.get("/api/boards/1")
    assert r.status_code == 401


# --- PATCH /api/boards/{board_id} ---

def test_rename_board(client):
    cookies = _login(client)
    boards = client.get("/api/boards", cookies=cookies).json()
    board_id = boards[0]["id"]

    r = client.patch(f"/api/boards/{board_id}", json={"title": "Renamed Board"}, cookies=cookies)
    assert r.status_code == 200
    assert r.json()["title"] == "Renamed Board"


def test_rename_board_persists(client):
    cookies = _login(client)
    boards = client.get("/api/boards", cookies=cookies).json()
    board_id = boards[0]["id"]
    client.patch(f"/api/boards/{board_id}", json={"title": "Persistent Name"}, cookies=cookies)

    r = client.get("/api/boards", cookies=cookies)
    titles = [b["title"] for b in r.json()]
    assert "Persistent Name" in titles


def test_rename_board_requires_auth(client):
    r = client.patch("/api/boards/1", json={"title": "x"})
    assert r.status_code == 401


# --- DELETE /api/boards/{board_id} ---

def test_delete_board_requires_auth(client):
    r = client.delete("/api/boards/1")
    assert r.status_code == 401


def test_cannot_delete_last_board(client):
    cookies = _login(client)
    boards = client.get("/api/boards", cookies=cookies).json()
    board_id = boards[0]["id"]
    r = client.delete(f"/api/boards/{board_id}", cookies=cookies)
    assert r.status_code == 400


def test_delete_second_board(client):
    cookies = _login(client)
    new_board = client.post("/api/boards", json={"title": "Temp Board"}, cookies=cookies).json()
    r = client.delete(f"/api/boards/{new_board['id']}", cookies=cookies)
    assert r.status_code == 204

    boards = client.get("/api/boards", cookies=cookies).json()
    assert not any(b["id"] == new_board["id"] for b in boards)


def test_delete_board_not_found(client):
    cookies = _login(client)
    # Create a second board so deletion is allowed
    client.post("/api/boards", json={"title": "Extra"}, cookies=cookies)
    r = client.delete("/api/boards/99999", cookies=cookies)
    assert r.status_code == 404


# --- Multi-user isolation ---

def test_boards_are_user_isolated(client):
    """One user cannot access another user's boards."""
    # Register a second user
    client.post("/api/auth/register", json={"username": "alice", "password": "password1"})
    client.post("/api/auth/register", json={"username": "bob", "password": "password2"})

    alice_login = client.post("/api/auth/login", json={"username": "alice", "password": "password1"})
    bob_login = client.post("/api/auth/login", json={"username": "bob", "password": "password2"})
    alice_cookies = {"session": alice_login.cookies["session"]}
    bob_cookies = {"session": bob_login.cookies["session"]}

    # Alice creates a board
    alice_board = client.post(
        "/api/boards", json={"title": "Alice's Board"}, cookies=alice_cookies
    ).json()

    # Bob cannot access Alice's board by ID
    r = client.get(f"/api/boards/{alice_board['id']}", cookies=bob_cookies)
    assert r.status_code == 404


def test_cards_scoped_to_user_boards(client):
    """A user cannot create cards in another user's column."""
    client.post("/api/auth/register", json={"username": "user1", "password": "password1"})
    client.post("/api/auth/register", json={"username": "user2", "password": "password2"})

    login1 = client.post("/api/auth/login", json={"username": "user1", "password": "password1"})
    login2 = client.post("/api/auth/login", json={"username": "user2", "password": "password2"})
    cookies1 = {"session": login1.cookies["session"]}
    cookies2 = {"session": login2.cookies["session"]}

    # Get user1's column
    boards1 = client.get("/api/boards", cookies=cookies1).json()
    board1_id = boards1[0]["id"]
    board1 = client.get(f"/api/boards/{board1_id}", cookies=cookies1).json()
    col_id = board1["columns"][0]["id"]

    # user2 tries to create a card in user1's column — should fail
    r = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "Sneaky card"},
        cookies=cookies2,
    )
    assert r.status_code == 404
