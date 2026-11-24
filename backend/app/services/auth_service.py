import base64
import hashlib
import hmac
import json
import time
import uuid
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.database import DatabaseManager, get_db_manager

# Fallback store for unit tests / offline DB mode
_IN_MEMORY_CACHE_CONSENT: Dict[str, bool] = {}


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


class AuthService:
    """Handles Google ID Token verification, user upsert in GuruDocDB, and HMAC-SHA256 JWT sessions."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or get_db_manager()
        self._ensure_auth_columns()

    def _ensure_auth_columns(self) -> None:
        """Ensures google_sub, avatar_url, and cache consent columns exist on users table."""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        ALTER TABLE users
                            ADD COLUMN IF NOT EXISTS google_sub VARCHAR(128) UNIQUE,
                            ADD COLUMN IF NOT EXISTS avatar_url TEXT,
                            ADD COLUMN IF NOT EXISTS cache_allowed BOOLEAN NOT NULL DEFAULT FALSE,
                            ADD COLUMN IF NOT EXISTS cache_allowed_at TIMESTAMPTZ;
                        """
                    )
        except Exception:
            pass

    async def _fetch_google_tokeninfo(self, credential: str) -> Optional[Dict[str, Any]]:
        """Verifies a Google ID Token against Google's tokeninfo endpoint."""
        if not credential or len(credential) > 8192:
            return None
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    "https://oauth2.googleapis.com/tokeninfo",
                    params={"id_token": credential},
                )
                if resp.status_code != 200:
                    return None
                return resp.json()
        except Exception:
            return None

    def _upsert_google_user(
        self,
        google_sub: str,
        email: str,
        full_name: str,
        avatar_url: Optional[str],
    ) -> Dict[str, Any]:
        """Upserts Google authenticated user into GuruDocDB users table."""
        fallback_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"gurudok:{email.lower()}"))
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO users (google_sub, email, full_name, avatar_url, role, updated_at)
                        VALUES (%s, %s, %s, %s, 'teacher', NOW())
                        ON CONFLICT (email) DO UPDATE SET
                            google_sub = COALESCE(EXCLUDED.google_sub, users.google_sub),
                            full_name = EXCLUDED.full_name,
                            avatar_url = COALESCE(EXCLUDED.avatar_url, users.avatar_url),
                            updated_at = NOW()
                        RETURNING id, email, full_name, avatar_url, role, COALESCE(cache_allowed, FALSE) AS cache_allowed;
                        """,
                        (google_sub, email.lower(), full_name, avatar_url),
                    )
                    row = cur.fetchone()
                    if row:
                        uid = str(row["id"])
                        return {
                            "id": uid,
                            "email": row["email"],
                            "full_name": row["full_name"],
                            "avatar_url": row.get("avatar_url"),
                            "role": row.get("role") or "teacher",
                            "cache_allowed": bool(row.get("cache_allowed", False) or _IN_MEMORY_CACHE_CONSENT.get(uid, False)),
                        }
        except Exception:
            pass

        return {
            "id": fallback_id,
            "email": email.lower(),
            "full_name": full_name,
            "avatar_url": avatar_url,
            "role": "teacher",
            "cache_allowed": bool(_IN_MEMORY_CACHE_CONSENT.get(fallback_id, False)),
        }

    def get_user_with_preferences(self, user_claims: Dict[str, Any]) -> Dict[str, Any]:
        """Resolves latest persisted user preferences (including cache_allowed) from GuruDocDB."""
        uid = str(user_claims["id"])
        cache_allowed = bool(user_claims.get("cache_allowed", False) or _IN_MEMORY_CACHE_CONSENT.get(uid, False))
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, email, full_name, avatar_url, role, COALESCE(cache_allowed, FALSE) AS cache_allowed
                        FROM users
                        WHERE id::text = %s OR email = %s
                        LIMIT 1;
                        """,
                        (uid, str(user_claims.get("email", "")).lower()),
                    )
                    row = cur.fetchone()
                    if row:
                        return {
                            "id": str(row["id"]),
                            "email": row["email"],
                            "full_name": row["full_name"],
                            "avatar_url": row.get("avatar_url"),
                            "role": row.get("role") or "teacher",
                            "cache_allowed": bool(row.get("cache_allowed", False) or cache_allowed),
                        }
        except Exception:
            pass

        return {
            "id": uid,
            "email": user_claims["email"],
            "full_name": user_claims.get("full_name") or user_claims["email"],
            "avatar_url": user_claims.get("avatar_url"),
            "role": user_claims.get("role", "teacher"),
            "cache_allowed": cache_allowed,
        }

    def save_cache_consent(self, user_claims: Dict[str, Any], allowed: bool) -> Dict[str, Any]:
        """Persists cache_allowed preference for the user account in GuruDocDB."""
        uid = str(user_claims["id"])
        email = str(user_claims.get("email", "")).lower()
        _IN_MEMORY_CACHE_CONSENT[uid] = bool(allowed)
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE users
                        SET cache_allowed = %s,
                            cache_allowed_at = CASE WHEN %s THEN NOW() ELSE cache_allowed_at END,
                            updated_at = NOW()
                        WHERE id::text = %s OR email = %s
                        RETURNING id, email, full_name, avatar_url, role, COALESCE(cache_allowed, FALSE) AS cache_allowed;
                        """,
                        (bool(allowed), bool(allowed), uid, email),
                    )
                    row = cur.fetchone()
                    if row:
                        return {
                            "id": str(row["id"]),
                            "email": row["email"],
                            "full_name": row["full_name"],
                            "avatar_url": row.get("avatar_url"),
                            "role": row.get("role") or "teacher",
                            "cache_allowed": bool(row.get("cache_allowed", allowed)),
                        }
        except Exception:
            pass

        return {
            "id": uid,
            "email": user_claims["email"],
            "full_name": user_claims.get("full_name") or user_claims["email"],
            "avatar_url": user_claims.get("avatar_url"),
            "role": user_claims.get("role", "teacher"),
            "cache_allowed": bool(allowed),
        }

    def create_access_token(self, user: Dict[str, Any]) -> str:
        """Creates an HMAC-SHA256 signed JWT for the authenticated user."""
        now = int(time.time())
        exp = now + (settings.jwt_expire_minutes * 60)
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": user["id"],
            "email": user["email"],
            "name": user["full_name"],
            "avatar_url": user.get("avatar_url"),
            "role": user.get("role", "teacher"),
            "cache_allowed": bool(user.get("cache_allowed", False)),
            "iat": now,
            "exp": exp,
        }
        segments = [
            _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
        signing_input = ".".join(segments).encode("ascii")
        signature = hmac.new(
            settings.jwt_secret_key.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        segments.append(_b64url_encode(signature))
        return ".".join(segments)

    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifies JWT signature and expiration, returning user claims or None."""
        try:
            parts = token.strip().split(".")
            if len(parts) != 3:
                return None
            signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
            expected_sig = hmac.new(
                settings.jwt_secret_key.encode("utf-8"),
                signing_input,
                hashlib.sha256,
            ).digest()
            actual_sig = _b64url_decode(parts[2])
            if not hmac.compare_digest(expected_sig, actual_sig):
                return None

            payload = json.loads(_b64url_decode(parts[1]).decode("utf-8"))
            if int(payload.get("exp", 0)) < int(time.time()):
                return None
            return {
                "id": payload["sub"],
                "email": payload["email"],
                "full_name": payload.get("name") or payload["email"],
                "avatar_url": payload.get("avatar_url"),
                "role": payload.get("role", "teacher"),
                "cache_allowed": bool(payload.get("cache_allowed", False)),
            }
        except Exception:
            return None

    async def login_with_google(self, credential: str) -> Dict[str, Any]:
        """Validates Google ID Token, upserts user, and returns JWT + user profile."""
        info = await self._fetch_google_tokeninfo(credential)
        if not info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token Google tidak valid atau sudah kedaluwarsa.",
            )

        if settings.google_client_id and info.get("aud") != settings.google_client_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token Google tidak cocok dengan Client ID aplikasi.",
            )

        email_verified = str(info.get("email_verified", "")).lower() == "true"
        email = info.get("email")
        if not email or not email_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email Google belum terverifikasi.",
            )

        google_sub = str(info.get("sub") or email)
        full_name = str(info.get("name") or email.split("@")[0])
        avatar_url = info.get("picture")

        user = self._upsert_google_user(
            google_sub=google_sub,
            email=email,
            full_name=full_name,
            avatar_url=avatar_url,
        )
        access_token = self.create_access_token(user)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user,
        }
