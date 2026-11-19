from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.core.database import get_db_manager
from app.core.exceptions import GuruDokException, InternalServerCustomError
from app.services.dataset_seeder import DatasetSeederService

router = APIRouter()


@router.get("/health", summary="Health Check & GuruDocDB Status")
async def health_check():
    """Returns application health, live PostgreSQL (GuruDocDB) connection status, and dataset counts."""
    try:
        db = get_db_manager()
        conn_status = db.check_connection()
        is_connected = conn_status.get("connected", False)

        dataset_stats = {}
        if is_connected:
            seeder = DatasetSeederService(db)
            counts = seeder.get_table_counts()
            dataset_stats = {
                "bskap_subjects": counts.get("curriculum_subjects", 0),
                "cp_elements": counts.get("curriculum_phase_elements", 0),
                "hour_allocations": counts.get("curriculum_hour_allocations", 0),
                "courses": counts.get("curriculum_courses", 0),
                "chapters": counts.get("curriculum_chapters", 0),
                "learning_objectives_tp": counts.get("learning_objectives_tp", 0),
                "calendar_weeks": counts.get("academic_calendar_weeks", 0),
                "graduate_dimensions": counts.get("graduate_dimensions", 0),
                "pedagogical_models": counts.get("pedagogical_models", 0),
            }

        return {
            "status": "healthy" if is_connected else "degraded",
            "app_name": settings.app_name,
            "environment": settings.app_env,
            "database": "connected" if is_connected else "disconnected",
            "database_name": conn_status.get("database", settings.db_name),
            "regulation_baseline": "Kepka BSKAP No. 046/H/KR/2025 & Permendikdasmen 13/2025",
            "dataset_stats": dataset_stats,
        }
    except (GuruDokException, HTTPException):
        raise
    except Exception as exc:
        raise InternalServerCustomError(f"Gagal memeriksa status kesehatan sistem: {str(exc)}") from exc
