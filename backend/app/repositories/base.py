from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.models.curriculum import CurriculumSubject, ChapterTopic
from app.models.teacher import TeacherProfile


class ICurriculumRepository(ABC):
    """Abstract interface for accessing official Kemendikdasmen curriculum data."""

    @abstractmethod
    def get_subjects(self, jenjang: Optional[str] = None, kelas: Optional[int] = None) -> List[CurriculumSubject]:
        """Returns subjects filtered by jenjang (SD/SMP/SMA) and/or grade."""
        pass

    @abstractmethod
    def get_subject_by_id(self, subject_id: str) -> Optional[CurriculumSubject]:
        """Finds subject by its ID (e.g., 'smp_ipa_7')."""
        pass

    @abstractmethod
    def get_chapter(self, subject_id: str, chapter_id: str) -> Optional[ChapterTopic]:
        """Finds specific chapter by subject ID and chapter ID."""
        pass

    @abstractmethod
    def get_profil_lulusan_dimensions(self) -> List[str]:
        """Returns the 8 Dimensi Profil Lulusan Permendikdasmen 10/2025."""
        pass

    @abstractmethod
    def add_custom_chapter(
        self,
        course_id: str,
        chapter_id: str,
        nomor_bab: int,
        semester: int,
        judul_bab: str,
        elemen_cp: str,
        alokasi_jp: int,
        model_pembelajaran: str,
        modul_ajar_payload: Dict[str, Any],
        tps: List[Dict[str, Any]],
    ) -> ChapterTopic:
        """Adds a user-defined custom chapter with TPs to the course."""
        pass


class ITeacherRepository(ABC):
    """Abstract interface for Teacher Profile persistence."""

    @abstractmethod
    def save(self, profile: TeacherProfile) -> TeacherProfile:
        """Saves or updates teacher profile."""
        pass

    @abstractmethod
    def find_by_id(self, profile_id: str) -> Optional[TeacherProfile]:
        """Finds teacher by ID."""
        pass

    @abstractmethod
    def find_by_phone(self, phone: str) -> Optional[TeacherProfile]:
        """Finds teacher by normalized WhatsApp phone number."""
        pass
