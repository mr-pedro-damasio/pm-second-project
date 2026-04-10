import pytest
from fastapi.testclient import TestClient
import main


@pytest.fixture()
def client(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<h1>Hello World</h1>")
    monkeypatch.setattr(main, "STATIC_DIR", tmp_path)
    return TestClient(main.app, follow_redirects=False)


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
