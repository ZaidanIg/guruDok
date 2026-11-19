from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status

from app.core.database import get_db_manager
from app.repositories.base import ICurriculumRepository, ITeacherRepository
from app.repositories.postgres_curriculum_repo import PostgresCurriculumRepository
from app.repositories.postgres_teacher_repo import PostgresTeacherRepository
from app.services.auth_service import AuthService
from app.services.curriculum_service import CurriculumService
from app.services.teacher_service import TeacherService
from app.services.storage_service import LocalStorageService
from app.services.generation_service import DocumentGenerationService

# Global Singleton Instances Backed by PostgreSQL (GuruDocDB)
_db_manager = get_db_manager()
_curriculum_repo = PostgresCurriculumRepository(_db_manager, auto_seed=True)
_teacher_repo = PostgresTeacherRepository(_db_manager)
_storage_service = LocalStorageService()
_auth_service = AuthService(_db_manager)
_curriculum_service = CurriculumService(_curriculum_repo)
_teacher_service = TeacherService(_teacher_repo)
_generation_service = DocumentGenerationService(_curriculum_repo, _teacher_repo, _storage_service, _db_manager)


def get_curriculum_repo() -> ICurriculumRepository:
    return _curriculum_repo


def get_teacher_repo() -> ITeacherRepository:
    return _teacher_repo


def get_storage_service() -> LocalStorageService:
    return _storage_service


def get_curriculum_service() -> CurriculumService:
    return _curriculum_service


def get_teacher_service() -> TeacherService:
    return _teacher_service


def get_generation_service() -> DocumentGenerationService:
    return _generation_service


def get_auth_service() -> AuthService:
    return _auth_service


def _extract_bearer_or_query_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    query_token = request.query_params.get("token")
    if query_token:
        return query_token.strip()
    return None


def get_optional_current_user(request: Request) -> Optional[Dict[str, Any]]:
    token = _extract_bearer_or_query_token(request)
    if not token:
        return None
    return _auth_service.verify_access_token(token)


def require_authenticated_user(request: Request) -> Dict[str, Any]:
    user = get_optional_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Silakan masuk dengan akun Google untuk melanjutkan.",
        )
    return user
