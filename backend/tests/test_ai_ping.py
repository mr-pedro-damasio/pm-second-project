from unittest.mock import AsyncMock, patch

import pytest

from conftest import login as _login


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
