from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_curriculum_service
from app.core.exceptions import GuruDokException, InternalServerCustomError
from app.schemas.common import ApiResponse
from app.schemas.curriculum import SubjectResponse, ChapterResponse, ChapterCreateRequest
from app.services.curriculum_service import CurriculumService

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])


@router.get("/subjects", response_model=ApiResponse[List[SubjectResponse]], summary="Get Subjects List")
async def list_subjects(
    jenjang: Optional[str] = Query(None, description="SD, SMP, or SMA"),
    kelas: Optional[int] = Query(None, ge=1, le=12, description="Tingkat kelas 1 s/d 12"),
    service: CurriculumService = Depends(get_curriculum_service),
):
    """Returns official Kemendikdasmen curriculum subjects filtered by level or grade."""
    try:
        subjects = service.get_subjects(jenjang=jenjang, kelas=kelas)
        return ApiResponse(data=subjects, message=f"Retrieved {len(subjects)} subjects successfully.")
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal mengambil daftar mata pelajaran: {str(exc)}") from exc


@router.get("/subjects/{subject_id}", response_model=ApiResponse[SubjectResponse], summary="Get Subject Detail")
async def get_subject_detail(
    subject_id: str,
    service: CurriculumService = Depends(get_curriculum_service),
):
    """Returns detailed subject information including all chapters and learning objectives."""
    try:
        subject = service.get_subject_detail(subject_id)
        return ApiResponse(data=subject, message="Subject details retrieved successfully.")
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal mengambil detail mata pelajaran '{subject_id}': {str(exc)}") from exc


@router.get("/subjects/{subject_id}/chapters", response_model=ApiResponse[List[ChapterResponse]], summary="Get Chapters")
async def list_chapters(
    subject_id: str,
    semester: Optional[int] = Query(None, ge=1, le=2, description="Semester 1 or 2"),
    service: CurriculumService = Depends(get_curriculum_service),
):
    """Returns chapters for a subject, optionally filtered by semester."""
    try:
        chapters = service.get_chapters(subject_id, semester=semester)
        return ApiResponse(data=chapters, message=f"Retrieved {len(chapters)} chapters successfully.")
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal mengambil daftar bab untuk '{subject_id}': {str(exc)}") from exc


@router.post("/subjects/{subject_id}/chapters", response_model=ApiResponse[ChapterResponse], summary="Create Custom Chapter")
async def create_custom_chapter(
    subject_id: str,
    payload: ChapterCreateRequest,
    service: CurriculumService = Depends(get_curriculum_service),
):
    """Creates a user-defined custom chapter and stores it in GuruDocDB."""
    try:
        new_chapter = service.create_custom_chapter(subject_id=subject_id, data=payload)
        try:
            from app.services.collection_service import CollectionService
            CollectionService()._save_contribution(
                subject_id=subject_id,
                jenjang="",
                kelas=0,
                service_id="custom_chapter_post",
                contribution_type="CHAPTER_TP",
                payload={
                    "nomor_bab": payload.nomor_bab,
                    "semester": payload.semester,
                    "judul_bab": payload.judul_bab,
                    "elemen_cp": payload.elemen_cp,
                    "alokasi_jp": payload.alokasi_jp,
                },
            )
        except Exception:
            pass
        return ApiResponse(data=new_chapter, message=f"Bab baru '{new_chapter.judul_bab}' berhasil ditambahkan.")
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal menambahkan bab baru: {str(exc)}") from exc


@router.get("/dimensions", response_model=ApiResponse[List[str]], summary="Get Profil Lulusan Dimensions")
async def get_dimensions(
    service: CurriculumService = Depends(get_curriculum_service),
):
    """Returns the 8 Dimensi Profil Lulusan officially mandated by Permendikdasmen No. 10/2025."""
    try:
        dims = service.get_profil_lulusan()
        return ApiResponse(data=dims, message="Dimensions retrieved successfully.")
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal mengambil daftar Dimensi Profil Lulusan: {str(exc)}") from exc
