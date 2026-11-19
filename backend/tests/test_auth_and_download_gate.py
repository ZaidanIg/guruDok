import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings


@pytest.fixture
def client():
    return TestClient(app)


def test_google_login_success_and_me_endpoint(client, monkeypatch):
    """TDD: Valid Google ID token creates/logs in user and returns signed JWT."""
    monkeypatch.setattr(settings, "google_client_id", "test-google-client-id.apps.googleusercontent.com")

    mock_tokeninfo = {
        "aud": "test-google-client-id.apps.googleusercontent.com",
        "sub": "google-sub-123456",
        "email": "guru.hebat@sekolah.sch.id",
        "email_verified": "true",
        "name": "Budi Santoso, S.Pd.",
        "picture": "https://example.com/avatar.png",
    }

    with patch("app.services.auth_service.AuthService._fetch_google_tokeninfo", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_tokeninfo
        res = client.post("/api/v1/auth/google", json={"credential": "valid-google-id-token"})

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert body["data"]["user"]["email"] == "guru.hebat@sekolah.sch.id"
    assert body["data"]["user"]["full_name"] == "Budi Santoso, S.Pd."

    token = body["data"]["access_token"]
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == "guru.hebat@sekolah.sch.id"


def test_google_login_invalid_token_returns_401(client, monkeypatch):
    """TDD: Invalid Google token must return HTTP 401."""
    monkeypatch.setattr(settings, "google_client_id", "test-google-client-id.apps.googleusercontent.com")

    with patch("app.services.auth_service.AuthService._fetch_google_tokeninfo", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = None
        res = client.post("/api/v1/auth/google", json={"credential": "bad-token"})

    assert res.status_code == 401


def test_auth_me_requires_valid_bearer_token(client):
    """TDD: /auth/me without or with invalid token must return HTTP 401."""
    res_no_token = client.get("/api/v1/auth/me")
    assert res_no_token.status_code == 401

    res_bad_token = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert res_bad_token.status_code == 401


def test_download_requires_auth_when_gate_enabled(client, monkeypatch):
    """TDD: Download endpoint rejects unauthenticated requests when auth_required_for_download=True."""
    monkeypatch.setattr(settings, "auth_required_for_download", True)

    res = client.get("/api/v1/documents/sample-file.docx/download")
    assert res.status_code == 401


def test_generate_and_download_with_authenticated_user(client, monkeypatch):
    """TDD: Authenticated user can generate and download document, and history is isolated."""
    monkeypatch.setattr(settings, "google_client_id", "test-google-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "auth_required_for_download", True)

    mock_tokeninfo = {
        "aud": "test-google-client-id.apps.googleusercontent.com",
        "sub": "google-sub-999",
        "email": "rini.guru@sekolah.sch.id",
        "email_verified": "true",
        "name": "Rini Hartati, S.Pd.",
    }

    with patch("app.services.auth_service.AuthService._fetch_google_tokeninfo", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_tokeninfo
        login_res = client.post("/api/v1/auth/google", json={"credential": "valid-google-token-2"})

    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Generate document with optional/empty teacher profile
    gen_res = client.post(
        "/api/v1/documents/generate",
        headers=headers,
        json={
            "service_id": "03_cp_tp",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "F4",
            "output_format": "docx",
        },
    )
    assert gen_res.status_code in (200, 201)
    filename = gen_res.json()["data"]["filename"]

    # Unauthenticated download -> 401
    dl_unauth = client.get(f"/api/v1/documents/{filename}/download")
    assert dl_unauth.status_code == 401

    # Authenticated download via Bearer header -> 200
    dl_auth = client.get(f"/api/v1/documents/{filename}/download", headers=headers)
    assert dl_auth.status_code == 200
    assert dl_auth.content[:4] == b"PK\x03\x04"

    # History for this user includes the generated filename
    hist_res = client.get("/api/v1/documents/history", headers=headers)
    assert hist_res.status_code == 200
    filenames = [item["filename"] for item in hist_res.json()["data"]]
    assert filename in filenames
