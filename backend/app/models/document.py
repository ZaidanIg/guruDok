import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any


@dataclass
class DocumentGenerationJob:
    """Domain model tracking a document generation job and output file metadata."""
    service_id: str
    service_name: str
    teacher_id: str
    file_format: str  # docx or xlsx
    filename: str
    paper_size: str = "F4"  # F4 or A4
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_url: str = ""
    file_size_bytes: int = 0
    total_pages_approx: int = 1
    status: str = "completed"  # pending, completed, failed
    error_message: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "service_id": self.service_id,
            "service_name": self.service_name,
            "teacher_id": self.teacher_id,
            "file_format": self.file_format,
            "filename": self.filename,
            "paper_size": self.paper_size,
            "file_url": self.file_url,
            "file_size_bytes": self.file_size_bytes,
            "file_size_human": f"{round(self.file_size_bytes / 1024, 1)} KB" if self.file_size_bytes > 0 else "0 KB",
            "total_pages_approx": self.total_pages_approx,
            "status": self.status,
            "error_message": self.error_message,
            "parameters": self.parameters,
            "created_at": self.created_at.isoformat(),
        }
