from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator
import psycopg
from psycopg.rows import dict_row

from app.core.config import settings


class DatabaseManager:
    """Manages PostgreSQL connections, schema initialization, and health checks for GuruDocDB."""

    def __init__(self, dsn: Optional[str] = None, schema_path: Optional[Path] = None):
        self.dsn = dsn or settings.database_url
        self.schema_path = schema_path or settings.schema_sql_path

    @contextmanager
    def get_connection(self) -> Generator[psycopg.Connection, None, None]:
        """Yields a PostgreSQL connection with dict_row factory and automatic commit/rollback."""
        conn = psycopg.connect(self.dsn, row_factory=dict_row)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def check_connection(self) -> Dict[str, Any]:
        """Pings PostgreSQL server and returns database identity and server version."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT current_database() AS db_name, version() AS server_version;")
                    row = cur.fetchone()
                    return {
                        "connected": True,
                        "database": row["db_name"] if row else settings.db_name,
                        "server_version": row["server_version"] if row else "PostgreSQL",
                    }
        except Exception as e:
            return {
                "connected": False,
                "database": settings.db_name,
                "error": str(e),
            }

    def initialize_schema(self) -> None:
        """Executes the DDL SQL script (06_schema_postgresql_gurudok.sql) idempotently."""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"PostgreSQL schema file not found at {self.schema_path}")

        sql_content = self.schema_path.read_text(encoding="utf-8")
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_content)

    def get_existing_tables(self) -> List[str]:
        """Returns list of table names in the public schema of GuruDocDB."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                    """
                )
                rows = cur.fetchall()
                return [r["table_name"] for r in rows]


_db_manager_instance: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Returns singleton DatabaseManager instance."""
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager()
    return _db_manager_instance
