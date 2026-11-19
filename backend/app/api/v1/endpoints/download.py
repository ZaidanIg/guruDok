from fastapi import APIRouter, Depends, Response, HTTPException, status
from app.api.deps import get_storage_service
from app.core.security import PathTraversalGuard, FileAttackGuard
from app.core.exceptions import (
    GuruDokException,
    SecurityViolationError,
    FileNotFoundCustomError,
    InternalServerCustomError,
)
from app.services.storage_service import IStorageService

router = APIRouter(prefix="/documents", tags=["Document Download"])

MIME_TYPES = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pdf": "application/pdf",
}


@router.get("/{filename}/download", summary="Download Document File")
async def download_document_file(
    filename: str,
    storage: IStorageService = Depends(get_storage_service),
):
    """Safely serves generated .docx, .xlsx, or .pdf file with Content-Disposition attachment."""
    try:
        clean_filename = PathTraversalGuard.sanitize_filename(filename)
        ext = FileAttackGuard.validate_extension(clean_filename)

        content = storage.get_file(clean_filename)

        # Validate file signature (.docx/.xlsx -> PK\x03\x04, .pdf -> %PDF-)
        if not FileAttackGuard.verify_file_signature(content, ext):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content integrity verification failed.",
            )

        mime_type = MIME_TYPES.get(ext, "application/octet-stream")

        return Response(
            content=content,
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{clean_filename}"',
                "Content-Length": str(len(content)),
                "Cache-Control": "no-cache, no-store, must-revalidate",
            },
        )
    except SecurityViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except FileNotFoundCustomError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal mengunduh berkas '{filename}': {str(exc)}") from exc
