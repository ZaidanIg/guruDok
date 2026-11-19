from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_auth_service, require_authenticated_user
from app.core.exceptions import GuruDokException, InternalServerCustomError
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


class GoogleLoginRequest(BaseModel):
    credential: str


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
):
    """Returns the currently authenticated Google user."""
    try:
        return ApiResponse(data=current_user, message="Sesi pengguna aktif.")
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal mengambil data pengguna: {str(exc)}") from exc
