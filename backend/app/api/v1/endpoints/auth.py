from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_auth_service, require_authenticated_user
from app.core.exceptions import GuruDokException, InternalServerCustomError
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


class GoogleLoginRequest(BaseModel):
    credential: str


class CacheConsentRequest(BaseModel):
    allowed: bool = True


@router.post("/google", response_model=ApiResponse[dict], summary="Login with Google ID Token")
async def login_with_google(
    payload: GoogleLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Verifies Google ID Token and returns GuruDok JWT session + user info."""
    try:
        result = await auth_service.login_with_google(payload.credential)
        return ApiResponse(data=result, message="Berhasil masuk dengan akun Google.")
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal memproses login Google: {str(exc)}") from exc


@router.get("/me", response_model=ApiResponse[dict], summary="Get Current Authenticated User")
async def get_current_user_info(
    current_user: dict = Depends(require_authenticated_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Returns the currently authenticated Google user including persisted cache consent."""
    try:
        user_data = auth_service.get_user_with_preferences(current_user)
        return ApiResponse(data=user_data, message="Sesi pengguna aktif.")
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal mengambil data pengguna: {str(exc)}") from exc


@router.post("/cache-consent", response_model=ApiResponse[dict], summary="Save User Cache Consent")
async def save_user_cache_consent(
    payload: CacheConsentRequest,
    current_user: dict = Depends(require_authenticated_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Persists cache_allowed preference to the authenticated user's account."""
    try:
        updated_user = auth_service.save_cache_consent(current_user, allowed=payload.allowed)
        return ApiResponse(data=updated_user, message="Preferensi cache akun berhasil disimpan.")
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal menyimpan preferensi cache akun: {str(exc)}") from exc
