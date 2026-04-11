"""Tests for card labels field."""
import pytest

from conftest import login as _login


def _get_first_col_id(client, cookies):
    board = client.get("/api/boards", cookies=cookies).json()[0]
    board_id = board["id"]
    full = client.get(f"/api/boards/{board_id}", cookies=cookies).json()
    return full["columns"][0]["id"]


# --- Creating cards with labels ---

def test_create_card_default_labels_empty(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    r = client.post("/api/cards", json={"column_id": col_id, "title": "T"}, cookies=cookies)
    assert r.status_code == 201
    assert r.json()["labels"] == []


def test_create_card_with_labels(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    r = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "T", "labels": ["bug", "frontend"]},
        cookies=cookies,
    )
    assert r.status_code == 201
    assert r.json()["labels"] == ["bug", "frontend"]


def test_create_card_labels_stripped(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    r = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "T", "labels": ["  bug  ", "  "]},
        cookies=cookies,
    )
    assert r.status_code == 201
    assert r.json()["labels"] == ["bug"]


def test_create_card_labels_capped_at_ten(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    r = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "T", "labels": [str(i) for i in range(15)]},
        cookies=cookies,
    )
    assert r.status_code == 201
    assert len(r.json()["labels"]) == 10


# --- Updating labels ---

def test_update_card_labels(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    card = client.post(
        "/api/cards", json={"column_id": col_id, "title": "T"}, cookies=cookies
    ).json()
    r = client.patch(
        f"/api/cards/{card['id']}", json={"labels": ["backend", "api"]}, cookies=cookies
    )
    assert r.status_code == 200
    assert r.json()["labels"] == ["backend", "api"]


def test_update_card_clear_labels(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    card = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "T", "labels": ["tag"]},
        cookies=cookies,
    ).json()
    r = client.patch(f"/api/cards/{card['id']}", json={"labels": []}, cookies=cookies)
    assert r.status_code == 200
    assert r.json()["labels"] == []


def test_labels_not_affected_by_other_updates(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    card = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "T", "labels": ["important"]},
        cookies=cookies,
    ).json()
    # Update title only — labels should remain
    r = client.patch(f"/api/cards/{card['id']}", json={"title": "New Title"}, cookies=cookies)
    assert r.status_code == 200
    assert r.json()["labels"] == ["important"]


def test_labels_visible_in_board_response(client):
    cookies = _login(client)
    boards = client.get("/api/boards", cookies=cookies).json()
    board_id = boards[0]["id"]
    full = client.get(f"/api/boards/{board_id}", cookies=cookies).json()
    col_id = full["columns"][0]["id"]

    card = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "Labeled", "labels": ["release"]},
        cookies=cookies,
    ).json()

    board = client.get(f"/api/boards/{board_id}", cookies=cookies).json()
    col = next(c for c in board["columns"] if c["id"] == col_id)
    found = next((c for c in col["cards"] if c["id"] == card["id"]), None)
    assert found is not None
    assert found["labels"] == ["release"]
