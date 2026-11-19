import threading
from typing import Dict, Optional
from app.models.teacher import TeacherProfile
from app.repositories.base import ITeacherRepository


class InMemoryTeacherRepository(ITeacherRepository):
    """Thread-safe in-memory repository for teacher and school profiles."""

    def __init__(self):
        self._profiles_by_id: Dict[str, TeacherProfile] = {}
        self._profiles_by_phone: Dict[str, TeacherProfile] = {}
        self._lock = threading.Lock()

    def save(self, profile: TeacherProfile) -> TeacherProfile:
        with self._lock:
            self._profiles_by_id[profile.id] = profile
            if profile.no_whatsapp:
                self._profiles_by_phone[profile.no_whatsapp] = profile
            return profile

    def find_by_id(self, profile_id: str) -> Optional[TeacherProfile]:
        with self._lock:
            return self._profiles_by_id.get(profile_id)

    def find_by_phone(self, phone: str) -> Optional[TeacherProfile]:
        with self._lock:
            return self._profiles_by_phone.get(phone)
