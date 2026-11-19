from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_generation_service
from app.core.exceptions import GuruDokException, InternalServerCustomError
from app.schemas.common import ApiResponse
from app.schemas.generation import DocumentGenerateRequest, DocumentGenerateResponse
from app.services.generation_service import DocumentGenerationService

router = APIRouter(prefix="/documents", tags=["Document Generator"])


@router.post("/generate", response_model=ApiResponse[DocumentGenerateResponse], status_code=status.HTTP_201_CREATED, summary="Generate Official Document")
async def generate_document(
    payload: DocumentGenerateRequest,
    service: DocumentGenerationService = Depends(get_generation_service),
):
    """Deterministic document generation endpoint. Produces official Word (.docx), Excel (.xlsx), or PDF (.pdf)."""
    try:
        result = service.generate_document(payload)
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
):
    """Returns history of documents generated from GuruDocDB."""
    try:
        history = service.get_history(limit=limit)
        return ApiResponse(data=history, message=f"Retrieved {len(history)} documents from history.")
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal mengambil riwayat dokumen: {str(exc)}") from exc
