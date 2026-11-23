import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from psycopg.types.json import Jsonb

from app.core.database import DatabaseManager, get_db_manager
from app.core.security import InputSanitizer
from app.models.curriculum import CurriculumSubject
from app.schemas.generation import DocumentGenerateRequest


class CollectionService:
    """Silently collects and deduplicates non-PII questions and curriculum contributions on POST actions.

    Strictly excludes teacher KOP Surat (teacher_profile) and student personal data (students).
    """

    _memory_questions: List[Dict[str, Any]] = []
    _memory_contributions: List[Dict[str, Any]] = []
    _schema_initialized: bool = False

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or get_db_manager()

    def _ensure_tables(self) -> bool:
        if CollectionService._schema_initialized:
            return True
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS question_bank (
                            id VARCHAR(64) PRIMARY KEY,
                            subject_id VARCHAR(64) NOT NULL,
                            chapter_id VARCHAR(64),
                            jenjang VARCHAR(16) NOT NULL,
                            kelas SMALLINT NOT NULL,
                            tp_code VARCHAR(64),
                            tipe_soal VARCHAR(20) NOT NULL DEFAULT 'PG',
                            level_kognitif VARCHAR(32) NOT NULL DEFAULT 'C1-C2',
                            stimulus TEXT DEFAULT '',
                            pertanyaan TEXT NOT NULL,
                            opsi_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                            kunci_jawaban TEXT DEFAULT '',
                            bobot_skor SMALLINT,
                            pembahasan TEXT DEFAULT '',
                            content_hash VARCHAR(64) UNIQUE NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        );
                        CREATE INDEX IF NOT EXISTS idx_question_bank_subject ON question_bank (subject_id);
                        CREATE TABLE IF NOT EXISTS curriculum_contributions (
                            id VARCHAR(64) PRIMARY KEY,
                            subject_id VARCHAR(64) NOT NULL,
                            jenjang VARCHAR(16) NOT NULL,
                            kelas SMALLINT NOT NULL,
                            service_id VARCHAR(32) NOT NULL,
                            contribution_type VARCHAR(40) NOT NULL,
                            payload_json JSONB NOT NULL,
                            content_hash VARCHAR(64) UNIQUE NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        );
                        """
                    )
            CollectionService._schema_initialized = True
            return True
        except Exception:
            return False

    @staticmethod
    def _hash_payload(data: Any) -> str:
        raw = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _save_question(self, record: Dict[str, Any]) -> None:
        content_hash = record["content_hash"]
        if not any(q["content_hash"] == content_hash for q in CollectionService._memory_questions):
            CollectionService._memory_questions.append(record)

        if self._ensure_tables():
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO question_bank (
                                id, subject_id, chapter_id, jenjang, kelas, tp_code,
                                tipe_soal, level_kognitif, stimulus, pertanyaan, opsi_json,
                                kunci_jawaban, bobot_skor, pembahasan, content_hash
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (content_hash) DO NOTHING;
                            """,
                            (
                                record["id"],
                                record["subject_id"],
                                record["chapter_id"],
                                record["jenjang"],
                                record["kelas"],
                                record["tp_code"],
                                record["tipe_soal"],
                                record["level_kognitif"],
                                record["stimulus"],
                                record["pertanyaan"],
                                Jsonb(record["opsi"]),
                                record["kunci_jawaban"],
                                record["bobot_skor"],
                                record["pembahasan"],
                                content_hash,
                            ),
                        )
            except Exception:
                pass

    def _save_contribution(
        self,
        subject_id: str,
        jenjang: str,
        kelas: int,
        service_id: str,
        contribution_type: str,
        payload: Any,
    ) -> None:
        content_hash = self._hash_payload(
            {"subject_id": subject_id, "type": contribution_type, "payload": payload}
        )
        record = {
            "id": str(uuid.uuid4()),
            "subject_id": subject_id,
            "jenjang": jenjang,
            "kelas": kelas,
            "service_id": service_id,
            "contribution_type": contribution_type,
            "payload": payload,
            "content_hash": content_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if not any(c["content_hash"] == content_hash for c in CollectionService._memory_contributions):
            CollectionService._memory_contributions.append(record)

        if self._ensure_tables():
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO curriculum_contributions (
                                id, subject_id, jenjang, kelas, service_id,
                                contribution_type, payload_json, content_hash
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (content_hash) DO NOTHING;
                            """,
                            (
                                record["id"],
                                subject_id,
                                jenjang,
                                kelas,
                                service_id,
                                contribution_type,
                                Jsonb(payload),
                                content_hash,
                            ),
                        )
            except Exception:
                pass

    def collect_from_generation(
        self, req: DocumentGenerateRequest, subject: CurriculumSubject
    ) -> None:
        """Non-blocking silent collection of questions & curriculum overrides from POST /documents/generate.

        NEVER stores req.teacher_profile (KOP Surat) or custom_overrides.students.
        """
        try:
            overrides = req.custom_overrides
            if not overrides:
                return

            jenjang_str = req.jenjang.value if hasattr(req.jenjang, "value") else str(req.jenjang)
            service_str = req.service_id.value if hasattr(req.service_id, "value") else str(req.service_id)

            # 1. Collect teacher-authored exam questions (butir_soal_kustom)
            if overrides.butir_soal_kustom:
                for q in overrides.butir_soal_kustom:
                    pertanyaan = InputSanitizer.sanitize_text(q.pertanyaan, max_length=3000)
                    if not pertanyaan or len(pertanyaan.strip()) < 3:
                        continue
                    opsi_clean = [InputSanitizer.sanitize_text(o, max_length=500) for o in (q.opsi or [])]
                    content_hash = self._hash_payload(
                        {
                            "subject_id": req.subject_id,
                            "tipe_soal": q.tipe_soal,
                            "pertanyaan": pertanyaan.strip().lower(),
                            "opsi": opsi_clean,
                        }
                    )
                    self._save_question(
                        {
                            "id": str(uuid.uuid4()),
                            "subject_id": req.subject_id,
                            "chapter_id": req.chapter_id,
                            "jenjang": jenjang_str,
                            "kelas": int(req.kelas),
                            "tp_code": q.tp_code or "",
                            "tipe_soal": q.tipe_soal,
                            "level_kognitif": q.level_kognitif or "C1-C2",
                            "stimulus": q.stimulus or "",
                            "pertanyaan": pertanyaan,
                            "opsi": opsi_clean,
                            "kunci_jawaban": q.kunci_jawaban or "",
                            "bobot_skor": q.bobot_skor,
                            "pembahasan": q.pembahasan or "",
                            "content_hash": content_hash,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )

            # 2. Collect custom CP elements (non-PII)
            if overrides.custom_elemen_cp:
                cp_payload = [
                    {
                        "kode_elemen": cp.kode_elemen,
                        "nama_elemen": cp.nama_elemen,
                        "deskripsi_cp": cp.deskripsi_cp,
                    }
                    for cp in overrides.custom_elemen_cp
                ]
                self._save_contribution(req.subject_id, jenjang_str, int(req.kelas), service_str, "CP", cp_payload)

            # 3. Collect custom chapters / TPs (non-PII)
            if overrides.custom_chapters:
                chap_payload = [
                    {
                        "nomor_bab": ch.nomor_bab,
                        "semester": ch.semester,
                        "judul_bab": ch.judul_bab,
                        "elemen_cp": ch.elemen_cp,
                        "alokasi_jp_bab": ch.alokasi_jp_bab,
                        "tujuan_pembelajaran": [
                            {"code": tp.code, "deskripsi": tp.deskripsi, "alokasi_jp": tp.alokasi_jp}
                            for tp in (ch.tujuan_pembelajaran or [])
                        ],
                    }
                    for ch in overrides.custom_chapters
                ]
                self._save_contribution(req.subject_id, jenjang_str, int(req.kelas), service_str, "CHAPTER_TP", chap_payload)

            # 4. Collect custom Modul Ajar / LKPD / Rubrik (non-PII)
            modul_fields = {
                "judul_lkpd": overrides.judul_lkpd,
                "tujuan_lkpd": overrides.tujuan_lkpd,
                "tugas_lkpd_memahami": overrides.tugas_lkpd_memahami,
                "tugas_lkpd_mengaplikasi": overrides.tugas_lkpd_mengaplikasi,
                "tugas_lkpd_merefleksi": overrides.tugas_lkpd_merefleksi,
                "soal_asesmen_awal": overrides.soal_asesmen_awal,
                "soal_asesmen_proses": overrides.soal_asesmen_proses,
                "soal_asesmen_akhir": overrides.soal_asesmen_akhir,
            }
            if any(v for v in modul_fields.values()):
                self._save_contribution(
                    req.subject_id,
                    jenjang_str,
                    int(req.kelas),
                    service_str,
                    "MODUL_LKPD_RUBRIK",
                    {k: v for k, v in modul_fields.items() if v},
                )
        except Exception:
            # Silent non-blocking: collection errors must never block document generation
            pass

    def query_questions(
        self,
        subject_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
        tipe_soal: Optional[str] = None,
        level_kognitif: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieves questions from GuruDocDB question_bank (or in-memory fallback)."""
        results: List[Dict[str, Any]] = []
        if self._ensure_tables():
            try:
                clauses = ["1=1"]
                params: List[Any] = []
                if subject_id:
                    clauses.append("subject_id = %s")
                    params.append(subject_id)
                if chapter_id:
                    clauses.append("chapter_id = %s")
                    params.append(chapter_id)
                if tipe_soal:
                    clauses.append("tipe_soal = %s")
                    params.append(tipe_soal.upper())
                if level_kognitif:
                    clauses.append("level_kognitif = %s")
                    params.append(level_kognitif)
                params.append(max(1, min(200, int(limit))))
                sql = (
                    "SELECT id, subject_id, chapter_id, jenjang, kelas, tp_code, "
                    "tipe_soal, level_kognitif, stimulus, pertanyaan, opsi_json, "
                    "kunci_jawaban, bobot_skor, pembahasan, created_at "
                    f"FROM question_bank WHERE {' AND '.join(clauses)} "
                    "ORDER BY created_at DESC LIMIT %s;"
                )
                with self.db.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(sql, tuple(params))
                        rows = cur.fetchall()
                        for r in rows:
                            results.append(
                                {
                                    "id": r["id"],
                                    "subject_id": r["subject_id"],
                                    "chapter_id": r["chapter_id"],
                                    "jenjang": r["jenjang"],
                                    "kelas": r["kelas"],
                                    "tp_code": r["tp_code"] or "",
                                    "tipe_soal": r["tipe_soal"],
                                    "level_kognitif": r["level_kognitif"],
                                    "stimulus": r["stimulus"] or "",
                                    "pertanyaan": r["pertanyaan"],
                                    "opsi": r["opsi_json"] or [],
                                    "kunci_jawaban": r["kunci_jawaban"] or "",
                                    "bobot_skor": r["bobot_skor"],
                                    "pembahasan": r["pembahasan"] or "",
                                    "created_at": r["created_at"].isoformat() if r["created_at"] else "",
                                }
                            )
                if results:
                    return results
            except Exception:
                pass

        # In-memory fallback filter
        filtered = list(reversed(CollectionService._memory_questions))
        if subject_id:
            filtered = [q for q in filtered if q["subject_id"] == subject_id]
        if chapter_id:
            filtered = [q for q in filtered if q.get("chapter_id") == chapter_id]
        if tipe_soal:
            filtered = [q for q in filtered if q["tipe_soal"] == tipe_soal.upper()]
        if level_kognitif:
            filtered = [q for q in filtered if q["level_kognitif"] == level_kognitif]
        return filtered[: max(1, min(200, int(limit)))]
