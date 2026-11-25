import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.security import PathTraversalGuard, FileAttackGuard
from app.core.exceptions import (
    SecurityViolationError,
    FileNotFoundCustomError,
    InternalServerCustomError,
)

MIME_TYPES = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pdf": "application/pdf",
    ".zip": "application/zip",
}


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


class R2StorageService(IStorageService):
    """Cloudflare R2 (S3-compatible) Object Storage Driver with S3v4 signature."""

    def __init__(
        self,
        account_id: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        public_url: Optional[str] = None,
        s3_client: Optional[Any] = None,
    ):
        self.account_id = account_id or settings.r2_account_id
        self.access_key_id = access_key_id or settings.r2_access_key_id
        self.secret_access_key = secret_access_key or settings.r2_secret_access_key
        self.bucket_name = bucket_name or settings.r2_bucket_name
        self.public_url = (public_url or settings.r2_public_url).rstrip("/")

        if s3_client:
            self.s3_client = s3_client
        else:
            endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"
            self.s3_client = boto3.client(
                service_name="s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name="auto",
                config=Config(signature_version="s3v4"),
            )

    def save_file(self, filename: str, content: bytes) -> str:
        clean_filename = PathTraversalGuard.sanitize_filename(filename)
        ext = FileAttackGuard.validate_extension(clean_filename)
        mime_type = MIME_TYPES.get(ext, "application/octet-stream")

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=clean_filename,
                Body=content,
                ContentType=mime_type,
            )
            return f"/api/v1/documents/{clean_filename}/download"
        except ClientError as e:
            raise InternalServerCustomError(f"Gagal mengunggah berkas '{clean_filename}' ke Cloudflare R2: {str(e)}") from e

    def get_file(self, filename: str) -> bytes:
        clean_filename = PathTraversalGuard.sanitize_filename(filename)

        try:
            resp = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=clean_filename,
            )
            return resp["Body"].read()
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey"):
                raise FileNotFoundCustomError(f"Berkas '{clean_filename}' tidak ditemukan di Cloudflare R2.") from e
            raise InternalServerCustomError(f"Gagal mengunduh berkas '{clean_filename}' dari Cloudflare R2: {str(e)}") from e

    def file_exists(self, filename: str) -> bool:
        try:
            clean_filename = PathTraversalGuard.sanitize_filename(filename)
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=clean_filename,
            )
            return True
        except (ClientError, SecurityViolationError):
            return False
