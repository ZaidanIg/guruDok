from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_teacher_service
from app.core.exceptions import GuruDokException, InternalServerCustomError
from app.schemas.common import ApiResponse
from app.schemas.teacher import TeacherProfileCreate, TeacherProfileResponse
from app.services.teacher_service import TeacherService

router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.post("/profile", response_model=ApiResponse[TeacherProfileResponse], status_code=status.HTTP_201_CREATED, summary="Create or Update Teacher Profile")
async def save_teacher_profile(
    data: TeacherProfileCreate,
    service: TeacherService = Depends(get_teacher_service),
):
    """Zero-Trust POST endpoint to validate and save teacher and school profile (Lead Capture)."""
    try:
        saved_profile = service.register_or_update(data)
        return ApiResponse(
            data=saved_profile,
            message="Profil guru dan sekolah berhasil disimpan.",
        )
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal menyimpan profil guru dan sekolah: {str(exc)}") from exc


@router.get("/profile/{profile_id}", response_model=ApiResponse[TeacherProfileResponse], summary="Get Teacher Profile by ID")
async def get_teacher_profile(
    profile_id: str,
    service: TeacherService = Depends(get_teacher_service),
):
    """Retrieves teacher profile details by ID."""
    try:
        profile = service.get_by_id(profile_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profil guru tidak ditemukan.")
        return ApiResponse(data=profile, message="Profil guru ditemukan.")
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal mengambil profil guru '{profile_id}': {str(exc)}") from exc
