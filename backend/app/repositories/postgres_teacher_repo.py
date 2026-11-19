from typing import Optional

from app.core.database import DatabaseManager, get_db_manager
from app.models.teacher import TeacherProfile
from app.repositories.base import ITeacherRepository


class PostgresTeacherRepository(ITeacherRepository):
    """PostgreSQL-backed repository for TeacherProfile persistence in GuruDocDB."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or get_db_manager()
        self.db.initialize_schema()

    def _row_to_model(self, row: dict) -> TeacherProfile:
        return TeacherProfile(
            id=str(row["id"]),
            nama_guru=row["teacher_name_with_title"],
            nip_guru=row["teacher_nip"] or "-",
            nama_sekolah=row["school_name"],
            npsn=row.get("school_npsn"),
            kabupaten_kota=row["city_regency"],
            provinsi=row.get("province") or "",
            nama_kepala_sekolah=row["headmaster_name"],
            nip_kepala_sekolah=row.get("headmaster_nip") or "-",
            no_whatsapp=row.get("whatsapp_number") or "",
            email=row.get("email"),
            ukuran_kertas_default=row.get("default_paper_size") or "F4",
        )

    def save(self, profile: TeacherProfile) -> TeacherProfile:
        """Upserts teacher profile into teacher_profiles table in GuruDocDB."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Check if phone already exists to keep consistent ID on upsert
                if profile.no_whatsapp:
                    cur.execute(
                        "SELECT id FROM teacher_profiles WHERE whatsapp_number = %s;",
                        (profile.no_whatsapp,),
                    )
                    existing = cur.fetchone()
                    if existing:
                        profile.id = str(existing["id"])

                cur.execute(
                    """
                    INSERT INTO teacher_profiles (
                        id, teacher_name_with_title, teacher_nip, school_name, school_npsn,
                        city_regency, province, headmaster_name, headmaster_nip,
                        whatsapp_number, email, default_paper_size, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        teacher_name_with_title = EXCLUDED.teacher_name_with_title,
                        teacher_nip = EXCLUDED.teacher_nip,
                        school_name = EXCLUDED.school_name,
                        school_npsn = EXCLUDED.school_npsn,
                        city_regency = EXCLUDED.city_regency,
                        province = EXCLUDED.province,
                        headmaster_name = EXCLUDED.headmaster_name,
                        headmaster_nip = EXCLUDED.headmaster_nip,
                        whatsapp_number = EXCLUDED.whatsapp_number,
                        email = EXCLUDED.email,
                        default_paper_size = EXCLUDED.default_paper_size,
                        updated_at = NOW();
                    """,
                    (
                        profile.id,
                        profile.nama_guru,
                        profile.nip_guru,
                        profile.nama_sekolah,
                        profile.npsn,
                        profile.kabupaten_kota,
                        profile.provinsi,
                        profile.nama_kepala_sekolah,
                        profile.nip_kepala_sekolah,
                        profile.no_whatsapp,
                        profile.email,
                        profile.ukuran_kertas_default,
                    ),
                )
        return profile

    def find_by_id(self, profile_id: str) -> Optional[TeacherProfile]:
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM teacher_profiles WHERE id = %s;", (profile_id,))
                row = cur.fetchone()
                return self._row_to_model(row) if row else None

    def find_by_phone(self, phone: str) -> Optional[TeacherProfile]:
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM teacher_profiles WHERE whatsapp_number = %s;", (phone,))
                row = cur.fetchone()
                return self._row_to_model(row) if row else None
