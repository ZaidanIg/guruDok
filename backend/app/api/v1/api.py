from fastapi import APIRouter
from app.api.v1.endpoints import health, curriculum, teachers, generator, download, auth

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router)
api_v1_router.include_router(health.router)
api_v1_router.include_router(curriculum.router)
api_v1_router.include_router(teachers.router)
api_v1_router.include_router(generator.router)
api_v1_router.include_router(download.router)
