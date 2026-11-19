from typing import Any, Dict, Optional


class GuruDokException(Exception):
    """Base exception for all domain exceptions in GuruDok."""
    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class CurriculumNotFoundError(GuruDokException):
    """Raised when curriculum data (Jenjang, Grade, Mapel, Bab) cannot be found."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, error_code="CURRICULUM_NOT_FOUND", details=details)


class ValidationError(GuruDokException):
    """Raised when request payload violates business rules."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, error_code="VALIDATION_FAILED", details=details)


class SecurityViolationError(GuruDokException):
    """Raised when input sanitization or security guard detects malicious payloads."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, error_code="SECURITY_VIOLATION", details=details)


class DocumentGenerationError(GuruDokException):
    """Raised when docx, xlsx, or pdf rendering fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, error_code="GENERATION_FAILED", details=details)


class FileNotFoundCustomError(GuruDokException):
    """Raised when a requested file or template cannot be located."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, error_code="FILE_NOT_FOUND", details=details)


class InternalServerCustomError(GuruDokException):
    """Raised when an unexpected runtime error occurs inside an async API endpoint."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, error_code="INTERNAL_SERVER_ERROR", details=details)
