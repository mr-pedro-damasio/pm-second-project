import json
from unittest.mock import AsyncMock, patch

import pytest

from conftest import login as _login


def _board_payload(client, cookies):
    board = client.get("/api/board", cookies=cookies).json()
    return {
        "columns": [
            {"id": col["id"], "title": col["title"], "cards": col["cards"]}
            for col in board["columns"]
        ]
    }


def test_chat_requires_auth(client):
    r = client.post(
        "/api/ai/chat",
        json={"messages": [{"role": "user", "content": "hi"}], "board": {"columns": []}},
    )
    assert r.status_code == 401


def test_chat_no_operations(client):
    cookies = _login(client)
    board = _board_payload(client, cookies)
    ai_reply = json.dumps({"message": "Looking good!", "operations": None})

    with (
        patch("routes.ai.ai_module.get_api_key", return_value="test-key"),
        patch("routes.ai.ai_module.chat_completion", new=AsyncMock(return_value=ai_reply)),
    ):
        r = client.post(
            "/api/ai/chat",
            json={"messages": [{"role": "user", "content": "How is the board?"}], "board": board},
            cookies=cookies,
        )

    assert r.status_code == 200
    data = r.json()
    assert data["message"] == "Looking good!"
    assert data["board_updated"] is False


def test_chat_create_card_op(client):
    cookies = _login(client)
    board_data = _board_payload(client, cookies)
    col_id = board_data["columns"][0]["id"]

    ai_reply = json.dumps({
        "message": "Done! I added a card.",
        "operations": [{"op": "create_card", "column_id": col_id, "title": "AI card", "details": "from AI"}],
    })

    with (
        patch("routes.ai.ai_module.get_api_key", return_value="test-key"),
        patch("routes.ai.ai_module.chat_completion", new=AsyncMock(return_value=ai_reply)),
    ):
        r = client.post(
            "/api/ai/chat",
            json={"messages": [{"role": "user", "content": "Add a card"}], "board": board_data},
            cookies=cookies,
        )

    assert r.status_code == 200
    data = r.json()
    assert data["board_updated"] is True

    board = client.get("/api/board", cookies=cookies).json()
    all_cards = [c for col in board["columns"] for c in col["cards"]]
    assert any(c["title"] == "AI card" for c in all_cards)


def test_chat_move_card_op(client):
    cookies = _login(client)
    board = client.get("/api/board", cookies=cookies).json()
    src_col = board["columns"][0]
    dst_col_id = board["columns"][4]["id"]
    card_id = src_col["cards"][0]["id"]

    ai_reply = json.dumps({
        "message": "Moved it.",
        "operations": [{"op": "move_card", "card_id": card_id, "column_id": dst_col_id, "position": 0}],
    })
    board_payload = _board_payload(client, cookies)

    with (
        patch("routes.ai.ai_module.get_api_key", return_value="test-key"),
        patch("routes.ai.ai_module.chat_completion", new=AsyncMock(return_value=ai_reply)),
    ):
        r = client.post(
            "/api/ai/chat",
            json={"messages": [{"role": "user", "content": "Move it"}], "board": board_payload},
            cookies=cookies,
        )

    assert r.status_code == 200
    assert r.json()["board_updated"] is True

    board = client.get("/api/board", cookies=cookies).json()
    dst_cards = next(c for c in board["columns"] if c["id"] == dst_col_id)["cards"]
    assert any(c["id"] == card_id for c in dst_cards)


def test_chat_invalid_json_from_ai(client):
    cookies = _login(client)
    board_payload = _board_payload(client, cookies)

    with (
        patch("routes.ai.ai_module.get_api_key", return_value="test-key"),
        patch("routes.ai.ai_module.chat_completion", new=AsyncMock(return_value="not json at all")),
    ):
        r = client.post(
            "/api/ai/chat",
            json={"messages": [{"role": "user", "content": "hi"}], "board": board_payload},
            cookies=cookies,
        )

    assert r.status_code == 200
    data = r.json()
    assert data["message"] == "not json at all"
    assert data["board_updated"] is False
