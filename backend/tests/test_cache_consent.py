import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import AuthService


@pytest.fixture
def client():
    return TestClient(app)


def test_cache_consent_requires_auth(client):
    """TDD Sprint 44: Saving cache consent without Bearer JWT must return 401."""
    res = client.post("/api/v1/auth/cache-consent", json={"allowed": True})
    assert res.status_code == 401


def test_cache_consent_persists_per_user_account(client):
    """TDD Sprint 44: Authenticated user can persist cache_allowed=True and retrieve it via /auth/me."""
    auth_svc = AuthService()
    test_user = {
        "id": "00000000-0000-0000-0000-000000000444",
        "email": "guru.cache44@gurudok.id",
        "full_name": "Guru Cache Tester",
        "avatar_url": None,
        "role": "teacher",
        "cache_allowed": False,
    }
    token = auth_svc.create_access_token(test_user)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Initially false on /auth/me
    me_before = client.get("/api/v1/auth/me", headers=headers)
    assert me_before.status_code == 200
    assert me_before.json()["data"]["cache_allowed"] is False

    # 2. User grants cache consent
    save_res = client.post(
        "/api/v1/auth/cache-consent",
        json={"allowed": True},
        headers=headers,
    )
    assert save_res.status_code == 200
    assert save_res.json()["data"]["cache_allowed"] is True

    # 3. Subsequent /auth/me returns cache_allowed=True so badge never asks again
    me_after = client.get("/api/v1/auth/me", headers=headers)
    assert me_after.status_code == 200
    assert me_after.json()["data"]["cache_allowed"] is True
