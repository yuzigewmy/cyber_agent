from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def auth_headers() -> dict[str, str]:
    login = client.post(
        "/v1/auth/login",
        json={"username": "security-admin", "password": "ChangeMe123!"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_api_root_available() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "Cyber Agent Guarded API"


def test_login_and_authenticated_chat_persists_messages() -> None:
    headers = auth_headers()

    me = client.get("/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["username"] == "security-admin"

    chat = client.post(
        "/v1/chat",
        headers=headers,
        json={
            "mode": "defense",
            "question": "Analyze suspicious logs",
            "assets": ["api-gateway"],
            "evidence": ["GET /.env 404 nuclei"],
        },
    )
    assert chat.status_code == 200
    body = chat.json()
    assert body["blocked"] is False
    assert body["session_id"]

    messages = client.get(f"/v1/chat/sessions/{body['session_id']}/messages", headers=headers)
    assert messages.status_code == 200
    assert [m["role"] for m in messages.json()] == ["user", "assistant"]


def test_chat_requires_authentication() -> None:
    response = client.post(
        "/v1/chat",
        json={"mode": "defense", "question": "Analyze logs"},
    )
    assert response.status_code == 401


def test_create_and_list_chat_sessions() -> None:
    headers = auth_headers()
    created = client.post(
        "/v1/chat/sessions",
        headers=headers,
        json={"title": "演练会话", "mode": "defense", "tenant_id": "default"},
    )
    assert created.status_code == 200
    session_id = created.json()["id"]

    listed = client.get("/v1/chat/sessions", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == session_id for item in listed.json())
