from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination and count metadata."""
    total_items: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1


class ApiResponse(BaseModel, Generic[T]):
    """Standard unified response wrapper for all GuruDok endpoints."""
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None
    meta: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Unified error response model."""
    success: bool = False
    error_code: str
    message: str
    details: Optional[Any] = None
