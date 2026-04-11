"""Tests for board activity log."""
import pytest

from conftest import login as _login


def _get_board_id(client, cookies):
    return client.get("/api/boards", cookies=cookies).json()[0]["id"]


def _get_col_id(client, cookies, board_id):
    board = client.get(f"/api/boards/{board_id}", cookies=cookies).json()
    return board["columns"][0]["id"]


# --- GET /api/boards/{board_id}/activity ---

def test_activity_requires_auth(client):
    r = client.get("/api/boards/1/activity")
    assert r.status_code == 401


def test_activity_not_found_for_other_user_board(client):
    client.post("/api/auth/register", json={"username": "alice3", "password": "password1"})
    client.post("/api/auth/register", json={"username": "bob3", "password": "password2"})
    alice = client.post("/api/auth/login", json={"username": "alice3", "password": "password1"})
    bob = client.post("/api/auth/login", json={"username": "bob3", "password": "password2"})
    alice_cookies = {"session": alice.cookies["session"]}
    bob_cookies = {"session": bob.cookies["session"]}

    alice_board_id = client.get("/api/boards", cookies=alice_cookies).json()[0]["id"]
    r = client.get(f"/api/boards/{alice_board_id}/activity", cookies=bob_cookies)
    assert r.status_code == 404


def test_create_card_logs_activity(client):
    cookies = _login(client)
    board_id = _get_board_id(client, cookies)
    col_id = _get_col_id(client, cookies, board_id)

    client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "Activity test card"},
        cookies=cookies,
    )

    r = client.get(f"/api/boards/{board_id}/activity", cookies=cookies)
    assert r.status_code == 200
    actions = [e["action"] for e in r.json()]
    assert "card_created" in actions


def test_delete_card_logs_activity(client):
    cookies = _login(client)
    board_id = _get_board_id(client, cookies)
    col_id = _get_col_id(client, cookies, board_id)

    card = client.post(
        "/api/cards", json={"column_id": col_id, "title": "Delete me"}, cookies=cookies
    ).json()
    client.delete(f"/api/cards/{card['id']}", cookies=cookies)

    r = client.get(f"/api/boards/{board_id}/activity", cookies=cookies)
    actions = [e["action"] for e in r.json()]
    assert "card_deleted" in actions


def test_add_column_logs_activity(client):
    cookies = _login(client)
    board_id = _get_board_id(client, cookies)

    client.post(f"/api/boards/{board_id}/columns", json={"title": "New Stage"}, cookies=cookies)

    r = client.get(f"/api/boards/{board_id}/activity", cookies=cookies)
    actions = [e["action"] for e in r.json()]
    assert "column_added" in actions


def test_delete_column_logs_activity(client):
    cookies = _login(client)
    board_id = _get_board_id(client, cookies)

    new_col = client.post(
        f"/api/boards/{board_id}/columns", json={"title": "TempLog"}, cookies=cookies
    ).json()
    client.delete(f"/api/columns/{new_col['id']}", cookies=cookies)

    r = client.get(f"/api/boards/{board_id}/activity", cookies=cookies)
    actions = [e["action"] for e in r.json()]
    assert "column_deleted" in actions


def test_activity_returns_list(client):
    cookies = _login(client)
    board_id = _get_board_id(client, cookies)
    r = client.get(f"/api/boards/{board_id}/activity", cookies=cookies)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_move_card_logs_activity(client):
    cookies = _login(client)
    board_id = _get_board_id(client, cookies)
    board = client.get(f"/api/boards/{board_id}", cookies=cookies).json()
    col1_id = board["columns"][0]["id"]
    col2_id = board["columns"][1]["id"]

    card = client.post(
        "/api/cards", json={"column_id": col1_id, "title": "Move me"}, cookies=cookies
    ).json()
    client.patch(
        f"/api/cards/{card['id']}/move",
        json={"column_id": col2_id, "position": 0},
        cookies=cookies,
    )

    r = client.get(f"/api/boards/{board_id}/activity", cookies=cookies)
    actions = [e["action"] for e in r.json()]
    assert "card_moved" in actions


def test_activity_detail_contains_card_title(client):
    cookies = _login(client)
    board_id = _get_board_id(client, cookies)
    col_id = _get_col_id(client, cookies, board_id)

    client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "My Specific Card"},
        cookies=cookies,
    )

    r = client.get(f"/api/boards/{board_id}/activity", cookies=cookies)
    creation_entries = [e for e in r.json() if e["action"] == "card_created"]
    details = [e["detail"] for e in creation_entries]
    assert "My Specific Card" in details
