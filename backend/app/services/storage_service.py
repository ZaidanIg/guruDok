import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from app.core.config import settings
from app.core.security import PathTraversalGuard, FileAttackGuard
from app.core.exceptions import SecurityViolationError, FileNotFoundCustomError


class IStorageService(ABC):
    """Abstract interface for storing and retrieving generated document files."""

    @abstractmethod
    def save_file(self, filename: str, content: bytes) -> str:
        """Saves file bytes and returns accessible file URL or download path."""
        pass

    @abstractmethod
    def get_file(self, filename: str) -> bytes:
        """Retrieves raw file bytes."""
        pass

    @abstractmethod
    def file_exists(self, filename: str) -> bool:
        """Checks if file exists in storage."""
        pass


class LocalStorageService(IStorageService):
    """Local filesystem storage driver with strict path traversal prevention."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = (base_dir or settings.generated_dir).resolve()
        os.makedirs(self.base_dir, exist_ok=True)

    def save_file(self, filename: str, content: bytes) -> str:
        clean_filename = PathTraversalGuard.sanitize_filename(filename)
        FileAttackGuard.validate_extension(clean_filename)

        target_path = PathTraversalGuard.resolve_safe_path(self.base_dir, clean_filename)
        with open(target_path, "wb") as f:
            f.write(content)

        return f"/api/v1/documents/{clean_filename}/download"

    def get_file(self, filename: str) -> bytes:
        clean_filename = PathTraversalGuard.sanitize_filename(filename)
        target_path = PathTraversalGuard.resolve_safe_path(self.base_dir, clean_filename)

        if not target_path.exists():
            raise FileNotFoundCustomError(f"File '{clean_filename}' was not found in storage.")

        with open(target_path, "rb") as f:
            return f.read()

    def file_exists(self, filename: str) -> bool:
        try:
            clean_filename = PathTraversalGuard.sanitize_filename(filename)
            target_path = PathTraversalGuard.resolve_safe_path(self.base_dir, clean_filename)
            return target_path.exists()
        except SecurityViolationError:
            return False
