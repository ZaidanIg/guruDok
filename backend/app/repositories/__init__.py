"""Repositories module for GuruDok data access."""
from app.repositories.base import ICurriculumRepository, ITeacherRepository
from app.repositories.curriculum_repo import JsonCurriculumRepository
from app.repositories.teacher_repo import InMemoryTeacherRepository

__all__ = [
    "ICurriculumRepository",
    "ITeacherRepository",
    "JsonCurriculumRepository",
    "InMemoryTeacherRepository",
]
