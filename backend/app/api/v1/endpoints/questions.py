from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query, HTTPException

from app.core.exceptions import GuruDokException, InternalServerCustomError
from app.schemas.common import ApiResponse
from app.services.collection_service import CollectionService

router = APIRouter(prefix="/questions", tags=["Question Bank"])


@router.get("", response_model=ApiResponse[List[Dict[str, Any]]], summary="List Curated & Collected Questions")
async def list_questions(
    subject_id: Optional[str] = Query(None, max_length=64),
    chapter_id: Optional[str] = Query(None, max_length=64),
    tipe_soal: Optional[str] = Query(None, max_length=20),
    level_kognitif: Optional[str] = Query(None, max_length=32),
    limit: int = Query(50, ge=1, le=200),
):
    """Returns collected non-PII questions from GuruDocDB question_bank filtered by subject/chapter/type."""
    try:
        service = CollectionService()
        items = service.query_questions(
            subject_id=subject_id,
            chapter_id=chapter_id,
            tipe_soal=tipe_soal,
            level_kognitif=level_kognitif,
            limit=limit,
        )
        return ApiResponse(
            data=items,
            message=f"Ditemukan {len(items)} butir soal dari Bank Soal GuruDok.",
        )
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal mengambil data bank soal: {str(exc)}") from exc
