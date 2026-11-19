import time
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.exceptions import (
    GuruDokException,
    CurriculumNotFoundError,
    ValidationError,
    SecurityViolationError,
    FileNotFoundCustomError,
    DocumentGenerationError,
    InternalServerCustomError,
)
from app.api.v1.api import api_v1_router

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="GuruDok REST API - Platform Otomasi Administrasi Guru Kurikulum Merdeka (BSKAP No. 046/H/KR/2025)",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 2. Security Middleware: Enforce Maximum Payload Size & Add Processing Time Header
@app.middleware("http")
async def security_and_timing_middleware(request: Request, call_next):
    if request.method in ["POST", "PUT", "PATCH"]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_body_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "success": False,
                    "error_code": "PAYLOAD_TOO_LARGE",
                    "message": f"Ukuran payload melebihi batas maksimum ({settings.max_request_body_size // 1024 // 1024} MB).",
                },
            )

    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    return response


# 3. Exception Handlers
@app.exception_handler(SecurityViolationError)
async def security_violation_handler(request: Request, exc: SecurityViolationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error_code": "SECURITY_VIOLATION",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(CurriculumNotFoundError)
async def curriculum_not_found_handler(request: Request, exc: CurriculumNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "success": False,
            "error_code": "CURRICULUM_NOT_FOUND",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(FileNotFoundCustomError)
async def file_not_found_handler(request: Request, exc: FileNotFoundCustomError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "success": False,
            "error_code": "FILE_NOT_FOUND",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(ValidationError)
async def custom_validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_code": "VALIDATION_FAILED",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(DocumentGenerationError)
async def generation_error_handler(request: Request, exc: DocumentGenerationError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_code": "GENERATION_FAILED",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(InternalServerCustomError)
async def internal_server_error_handler(request: Request, exc: InternalServerCustomError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(RequestValidationError)
async def pydantic_validation_handler(request: Request, exc: RequestValidationError):
    formatted_errors = []
    for err in exc.errors():
        field_path = " -> ".join([str(loc) for loc in err["loc"] if loc != "body"])
        formatted_errors.append({
            "field": field_path,
            "message": err["msg"],
            "type": err["type"],
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_code": "UNPROCESSABLE_ENTITY",
            "message": "Validasi input formulir gagal. Mohon periksa kembali kolom isian.",
            "details": formatted_errors,
        },
    )


# 4. Mount API Router
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/", summary="Root API Information")
async def root():
    try:
        return {
            "app": settings.app_name,
            "version": "1.0.0",
            "docs": "/docs",
            "api_v1": "/api/v1",
            "status": "online",
        }
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Failed to retrieve root API info: {str(exc)}") from exc
