"""Tests for card priority and due_date fields."""
import pytest

from conftest import login as _login


def _get_first_col_id(client, cookies):
    board = client.get("/api/boards", cookies=cookies).json()[0]
    board_id = board["id"]
    full = client.get(f"/api/boards/{board_id}", cookies=cookies).json()
    return full["columns"][0]["id"]


# --- Priority ---

def test_create_card_default_priority_is_medium(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    r = client.post("/api/cards", json={"column_id": col_id, "title": "T"}, cookies=cookies)
    assert r.status_code == 201
    assert r.json()["priority"] == "medium"


def test_create_card_with_high_priority(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    r = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "Urgent", "priority": "high"},
        cookies=cookies,
    )
    assert r.status_code == 201
    assert r.json()["priority"] == "high"


def test_create_card_with_low_priority(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    r = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "Nice to have", "priority": "low"},
        cookies=cookies,
    )
    assert r.status_code == 201
    assert r.json()["priority"] == "low"


def test_create_card_invalid_priority_falls_back_to_medium(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    r = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "T", "priority": "critical"},
        cookies=cookies,
    )
    assert r.status_code == 201
    assert r.json()["priority"] == "medium"


def test_update_card_priority(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    card = client.post(
        "/api/cards", json={"column_id": col_id, "title": "Test"}, cookies=cookies
    ).json()
    r = client.patch(
        f"/api/cards/{card['id']}", json={"priority": "high"}, cookies=cookies
    )
    assert r.status_code == 200
    assert r.json()["priority"] == "high"


def test_priority_persists_after_update(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    card = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "Persist", "priority": "low"},
        cookies=cookies,
    ).json()
    # Update title only — priority should remain
    client.patch(f"/api/cards/{card['id']}", json={"title": "New Title"}, cookies=cookies)
    board_id = client.get("/api/boards", cookies=cookies).json()[0]["id"]
    board = client.get(f"/api/boards/{board_id}", cookies=cookies).json()
    col = next(c for c in board["columns"] if c["id"] == col_id)
    updated = next(c for c in col["cards"] if c["id"] == card["id"])
    assert updated["priority"] == "low"


# --- Due date ---

def test_create_card_default_due_date_is_null(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    r = client.post("/api/cards", json={"column_id": col_id, "title": "T"}, cookies=cookies)
    assert r.json()["due_date"] is None


def test_create_card_with_due_date(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    r = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "Deadline", "due_date": "2026-12-31"},
        cookies=cookies,
    )
    assert r.status_code == 201
    assert r.json()["due_date"] == "2026-12-31"


def test_update_card_due_date(client):
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    card = client.post(
        "/api/cards", json={"column_id": col_id, "title": "T"}, cookies=cookies
    ).json()
    r = client.patch(
        f"/api/cards/{card['id']}", json={"due_date": "2026-06-15"}, cookies=cookies
    )
    assert r.status_code == 200
    assert r.json()["due_date"] == "2026-06-15"


def test_update_card_clears_due_date_with_empty_string(client):
    """Sending due_date: null in the patch body clears the due date.
    Our implementation uses '' (empty string) as the clear sentinel."""
    cookies = _login(client)
    col_id = _get_first_col_id(client, cookies)
    card = client.post(
        "/api/cards",
        json={"column_id": col_id, "title": "T", "due_date": "2026-01-01"},
        cookies=cookies,
    ).json()
    assert card["due_date"] == "2026-01-01"

    # Update with empty string to clear
    r = client.patch(f"/api/cards/{card['id']}", json={"due_date": ""}, cookies=cookies)
    # The server stores empty string mapped to None
    assert r.status_code == 200
    assert r.json()["due_date"] is None
