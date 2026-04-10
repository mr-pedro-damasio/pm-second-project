import pytest
from fastapi.testclient import TestClient
import main


@pytest.fixture()
def client(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<h1>Hello</h1>")
    monkeypatch.setattr(main, "STATIC_DIR", tmp_path)
    return TestClient(main.app, follow_redirects=False)


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
    # Login first
    login = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert "session" in login.cookies

    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    # Cookie is cleared (set to empty or deleted)
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
    (client.app_state if hasattr(client, "app_state") else None)
    # Create login/index.html so the page can be served
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
