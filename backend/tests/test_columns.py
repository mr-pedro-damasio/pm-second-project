"""Tests for column add/delete endpoints."""
import pytest

from conftest import login as _login


def _get_board_id(client, cookies):
    return client.get("/api/boards", cookies=cookies).json()[0]["id"]


# --- POST /api/boards/{board_id}/columns ---

def test_add_column_requires_auth(client):
    r = client.post("/api/boards/1/columns", json={"title": "New"})
    assert r.status_code == 401


def test_add_column(client):
    cookies = _login(client)
    board_id = _get_board_id(client, cookies)
    r = client.post(f"/api/boards/{board_id}/columns", json={"title": "Archived"}, cookies=cookies)
    assert r.status_code == 201
    col = r.json()
    assert col["title"] == "Archived"
    assert col["cards"] == []


def test_add_column_appears_in_board(client):
    cookies = _login(client)
    board_id = _get_board_id(client, cookies)
    client.post(f"/api/boards/{board_id}/columns", json={"title": "QA"}, cookies=cookies)
    board = client.get(f"/api/boards/{board_id}", cookies=cookies).json()
    titles = [c["title"] for c in board["columns"]]
    assert "QA" in titles


def test_add_column_position_is_last(client):
    cookies = _login(client)
    board_id = _get_board_id(client, cookies)
    r = client.post(f"/api/boards/{board_id}/columns", json={"title": "End"}, cookies=cookies)
    board = client.get(f"/api/boards/{board_id}", cookies=cookies).json()
    positions = [c["position"] for c in board["columns"]]
    col_pos = r.json()["position"]
    assert col_pos == max(positions)


def test_add_column_empty_title_rejected(client):
    cookies = _login(client)
    board_id = _get_board_id(client, cookies)
    r = client.post(f"/api/boards/{board_id}/columns", json={"title": ""}, cookies=cookies)
    assert r.status_code == 422


def test_add_column_not_found_board(client):
    cookies = _login(client)
    r = client.post("/api/boards/99999/columns", json={"title": "X"}, cookies=cookies)
    assert r.status_code == 404


def test_add_column_other_user_board(client):
    client.post("/api/auth/register", json={"username": "alice2", "password": "password1"})
    client.post("/api/auth/register", json={"username": "bob2", "password": "password2"})
    alice = client.post("/api/auth/login", json={"username": "alice2", "password": "password1"})
    bob = client.post("/api/auth/login", json={"username": "bob2", "password": "password2"})
    alice_cookies = {"session": alice.cookies["session"]}
    bob_cookies = {"session": bob.cookies["session"]}

    alice_board_id = client.get("/api/boards", cookies=alice_cookies).json()[0]["id"]
    r = client.post(
        f"/api/boards/{alice_board_id}/columns",
        json={"title": "Sneaky"},
        cookies=bob_cookies,
    )
    assert r.status_code == 404


# --- DELETE /api/columns/{column_id} ---

def test_delete_column_requires_auth(client):
    r = client.delete("/api/columns/1")
    assert r.status_code == 401


def test_cannot_delete_last_column(client):
    cookies = _login(client)
    board_id = _get_board_id(client, cookies)
    board = client.get(f"/api/boards/{board_id}", cookies=cookies).json()
    # Delete all but one column
    cols = board["columns"]
    for col in cols[1:]:
        client.delete(f"/api/columns/{col['id']}", cookies=cookies)
    # Attempt to delete the last column
    r = client.delete(f"/api/columns/{cols[0]['id']}", cookies=cookies)
    assert r.status_code == 400


def test_delete_column(client):
    cookies = _login(client)
    board_id = _get_board_id(client, cookies)
    # Add a new column first so we can delete it safely
    new_col = client.post(
        f"/api/boards/{board_id}/columns", json={"title": "Temp"}, cookies=cookies
    ).json()
    r = client.delete(f"/api/columns/{new_col['id']}", cookies=cookies)
    assert r.status_code == 204

    board = client.get(f"/api/boards/{board_id}", cookies=cookies).json()
    ids = [c["id"] for c in board["columns"]]
    assert new_col["id"] not in ids


def test_delete_column_not_found(client):
    cookies = _login(client)
    r = client.delete("/api/columns/99999", cookies=cookies)
    assert r.status_code == 404


def test_delete_column_cascades_cards(client):
    cookies = _login(client)
    board_id = _get_board_id(client, cookies)
    # Add a new column and a card in it
    new_col = client.post(
        f"/api/boards/{board_id}/columns", json={"title": "ToDelete"}, cookies=cookies
    ).json()
    client.post(
        "/api/cards",
        json={"column_id": new_col["id"], "title": "Orphan card"},
        cookies=cookies,
    )
    # Delete the column
    client.delete(f"/api/columns/{new_col['id']}", cookies=cookies)
    # Board should not contain the deleted column's cards
    board = client.get(f"/api/boards/{board_id}", cookies=cookies).json()
    all_cards = [c for col in board["columns"] for c in col["cards"]]
    titles = [c["title"] for c in all_cards]
    assert "Orphan card" not in titles
