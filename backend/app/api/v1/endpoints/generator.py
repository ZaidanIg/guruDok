from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_generation_service, get_optional_current_user
from app.core.exceptions import GuruDokException, InternalServerCustomError
from app.schemas.common import ApiResponse
from app.schemas.generation import DocumentGenerateRequest, DocumentGenerateResponse
from app.services.generation_service import DocumentGenerationService

router = APIRouter(prefix="/documents", tags=["Document Generator"])


@router.post("/generate", response_model=ApiResponse[DocumentGenerateResponse], status_code=status.HTTP_201_CREATED, summary="Generate Official Document")
async def generate_document(
    payload: DocumentGenerateRequest,
    service: DocumentGenerationService = Depends(get_generation_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """Deterministic document generation endpoint. Produces official Word (.docx), Excel (.xlsx), or PDF (.pdf)."""
    try:
        user_id = current_user["id"] if current_user else None
        result = service.generate_document(payload, user_id=user_id)
        return ApiResponse(
            data=result,
            message=f"Dokumen {result.service_name} berhasil dibuat dalam {result.execution_time_ms} ms.",
        )
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal melakukan generasi dokumen: {str(exc)}") from exc


@router.get("/history", response_model=ApiResponse[List[Dict[str, Any]]], summary="Get Generation History")
async def get_generation_history(
    limit: int = 20,
    service: DocumentGenerationService = Depends(get_generation_service),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
):
    """Returns history of documents generated from GuruDocDB, isolated per user when authenticated."""
    try:
        user_id = current_user["id"] if current_user else None
        history = service.get_history(limit=limit, user_id=user_id)
        return ApiResponse(data=history, message=f"Retrieved {len(history)} documents from history.")
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal mengambil riwayat dokumen: {str(exc)}") from exc
