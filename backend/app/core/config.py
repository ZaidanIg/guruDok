import json
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=False)

def _resolve_path(env_key: str, default_path: Path) -> Path:
    """Resolves absolute or BASE_DIR-relative path from environment."""
    raw = os.getenv(env_key, "").strip()
    if not raw:
        return default_path
    p = Path(raw)
    return p if p.is_absolute() else (BASE_DIR / p).resolve()


DOCUMENT_DIR = BASE_DIR.parent / "document"
_DEFAULT_DATASET = (DOCUMENT_DIR / "dataset") if (DOCUMENT_DIR / "dataset").exists() else (BASE_DIR / "dataset")
DATASET_DEFAULT_PATH = _resolve_path("DATASET_PATH", _DEFAULT_DATASET)
GENERATED_DOCS_DEFAULT_PATH = _resolve_path("GENERATED_DIR", BASE_DIR / "generated_docs")


def _parse_cors_origins() -> List[str]:
    """Parses CORS_ORIGINS from JSON array or comma-separated env string."""
    default_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "https://gurudok.id",
    ]
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        return default_origins
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return list(dict.fromkeys([*default_origins, *[str(o).strip() for o in parsed if str(o).strip()]]))
    except json.JSONDecodeError:
        pass
    split_items = [item.strip() for item in raw.split(",") if item.strip()]
    return list(dict.fromkeys([*default_origins, *split_items]))


class Settings(BaseModel):
    """Application configuration settings."""
    app_name: str = "GuruDok API"
    app_env: str = os.getenv("APP_ENV", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    port: int = int(os.getenv("PORT", "8000"))
    host: str = os.getenv("HOST", "0.0.0.0")

    # PostgreSQL Database Settings (GuruDocDB)
    db_host: str = os.getenv("DB_HOST", "127.0.0.1")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "GuruDocDB")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "Asgardian13")
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'Asgardian13')}@{os.getenv('DB_HOST', '127.0.0.1')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'GuruDocDB')}",
    )

    # CORS origins
    cors_origins: List[str] = _parse_cors_origins()

    # File & Request Security limits
    max_request_body_size: int = int(os.getenv("MAX_REQUEST_BODY_SIZE", str(2 * 1024 * 1024)))  # 2MB limit
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    # Paths
    dataset_path: Path = DATASET_DEFAULT_PATH
    schema_sql_path: Path = DATASET_DEFAULT_PATH / "06_schema_postgresql_gurudok.sql"
    generated_dir: Path = GENERATED_DOCS_DEFAULT_PATH

    # Storage driver: "local" or "s3"
    storage_driver: str = os.getenv("STORAGE_DRIVER", "local")

    # Cloudflare R2 / S3
    r2_account_id: str = os.getenv("R2_ACCOUNT_ID", "")
    r2_access_key_id: str = os.getenv("R2_ACCESS_KEY_ID", "")
    r2_secret_access_key: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    r2_bucket_name: str = os.getenv("R2_BUCKET_NAME", "gurudok-documents")
    r2_public_url: str = os.getenv("R2_PUBLIC_URL", "https://files.gurudok.id")


settings = Settings()

# Ensure generated docs directory exists
os.makedirs(settings.generated_dir, exist_ok=True)
