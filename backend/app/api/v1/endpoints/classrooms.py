from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import Response
from app.core.exceptions import SecurityViolationError
from app.services.classroom_excel_parser import ClassroomExcelParserService, MAX_EXCEL_SIZE
from app.schemas.classroom import ClassroomParseResponse

router = APIRouter(prefix="/classrooms", tags=["Classrooms"])


@router.post("/parse-excel", response_model=ClassroomParseResponse, status_code=status.HTTP_200_OK)
async def parse_classroom_excel(file: UploadFile = File(...)) -> ClassroomParseResponse:
    """
    Stateless endpoint to parse teacher-uploaded student roster Excel file.
    Applies magic bytes validation, auto-detects header row, normalizes fields,
    sanitizes against Formula Injection & XSS, and returns parsed student data.
    Does NOT store the file on disk or server.
    """
    try:
        filename = file.filename or "uploaded_file.xlsx"

        # Check content length if available
        if file.size and file.size > MAX_EXCEL_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Ukuran file melebihi batas maksimum 2 MB ({file.size} bytes)."
            )

        file_bytes = await file.read()

        if len(file_bytes) > MAX_EXCEL_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Ukuran file melebihi batas maksimum 2 MB ({len(file_bytes)} bytes)."
            )

        parsed_data = ClassroomExcelParserService.parse_excel_file(file_bytes=file_bytes, filename=filename)

        return ClassroomParseResponse(
            success=True,
            message="File Excel siswa berhasil diproses.",
            data=parsed_data
        )

    except HTTPException:
        raise
    except SecurityViolationError as sve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(sve)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan saat memproses file Excel: {str(exc)}"
        )


@router.get("/template-excel", status_code=status.HTTP_200_OK)
async def download_student_template() -> Response:
    """
    Stateless endpoint to generate and download the official GuruDok student roster Excel template.
    Returns binary .xlsx stream with proper headers and sample guidance rows.
    """
    try:
        bio = ClassroomExcelParserService.generate_official_template()
        content = bio.getvalue()

        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": 'attachment; filename="Format_Data_Siswa_GuruDok.xlsx"',
                "Content-Length": str(len(content)),
                "Cache-Control": "no-cache"
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menghasilkan template Excel: {str(exc)}"
        )
