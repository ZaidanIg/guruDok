from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.models.curriculum import CurriculumSubject, ChapterTopic
from app.models.teacher import TeacherProfile
from app.schemas.generation import DocumentGenerateRequest


class DocumentEngine(ABC):
    """Abstract Strategy interface for deterministic document generation engines."""

    # Official Indonesian standard margins in mm
    MARGIN_TOP_MM = 25.4
    MARGIN_BOTTOM_MM = 25.4
    MARGIN_LEFT_MM = 30.0   # 3 cm left for binding
    MARGIN_RIGHT_MM = 20.0

    # Official Paper Dimensions in mm
    F4_WIDTH_MM = 215.0
    F4_HEIGHT_MM = 330.0

    A4_WIDTH_MM = 210.0
    A4_HEIGHT_MM = 297.0

    @abstractmethod
    def generate(
        self,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
        raw_template: Optional[dict] = None,
    ) -> bytes:
        """Generates document binary bytes deterministically."""
        pass
