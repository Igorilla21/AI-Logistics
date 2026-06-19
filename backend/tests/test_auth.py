from fastapi.testclient import TestClient

from dynno_customs_api.api.routes import auth as auth_routes
from dynno_customs_api.main import app


def _register_first_user(client: TestClient) -> dict:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "admin@example.com",
            "password": "StrongPass123",
            "full_name": "Admin User",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_bootstrap_registration_creates_first_admin_and_returns_token() -> None:
    client = TestClient(app)

    response_body = _register_first_user(client)

    assert response_body["token_type"] == "bearer"
    assert response_body["user"]["email"] == "admin@example.com"
    assert response_body["user"]["role"] == "admin"
    assert response_body["user"]["last_login_at"] is not None

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {response_body['access_token']}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["full_name"] == "Admin User"

    bootstrap_response = client.get("/api/auth/bootstrap-status")
    assert bootstrap_response.status_code == 200
    assert bootstrap_response.json() == {"has_users": True, "registration_open": True}


def test_open_registration_allows_second_user_as_operator() -> None:
    client = TestClient(app)
    _register_first_user(client)

    response = client.post(
        "/api/auth/register",
        json={
            "email": "second@example.com",
            "password": "AnotherPass123",
            "full_name": "Second User",
        },
    )

    assert response.status_code == 201
    assert response.json()["user"]["email"] == "second@example.com"
    assert response.json()["user"]["role"] == "operator"


def test_bootstrap_status_is_open_before_first_user() -> None:
    client = TestClient(app)

    response = client.get("/api/auth/bootstrap-status")

    assert response.status_code == 200
    assert response.json() == {"has_users": False, "registration_open": True}


def test_registration_can_be_closed_after_first_user_via_config(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.setattr(auth_routes.settings, "auth_open_registration", False)

    _register_first_user(client)

    bootstrap_response = client.get("/api/auth/bootstrap-status")
    assert bootstrap_response.status_code == 200
    assert bootstrap_response.json() == {"has_users": True, "registration_open": False}

    response = client.post(
        "/api/auth/register",
        json={
            "email": "second@example.com",
            "password": "AnotherPass123",
            "full_name": "Second User",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Open registration is disabled for this workspace."


def test_login_accepts_normalized_email_and_logout_revokes_session() -> None:
    client = TestClient(app)
    _register_first_user(client)

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "  ADMIN@EXAMPLE.COM ",
            "password": "StrongPass123",
        },
    )

    assert login_response.status_code == 200
    login_body = login_response.json()
    token = login_body["access_token"]

    logout_response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert logout_response.status_code == 200
    assert logout_response.json() == {"status": "logged_out"}

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 401
    assert me_response.json()["detail"] == "Invalid or expired authentication token."
