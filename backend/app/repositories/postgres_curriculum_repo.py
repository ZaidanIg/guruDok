from typing import List, Optional, Dict, Any, Tuple

from app.core.database import DatabaseManager, get_db_manager
from app.models.curriculum import CurriculumSubject, ChapterTopic, LearningObjective
from app.repositories.base import ICurriculumRepository
from app.services.dataset_seeder import DatasetSeederService


class PostgresCurriculumRepository(ICurriculumRepository):
    """PostgreSQL-backed repository integrating all 5 BSKAP 2025 datasets & 150+ courses across Grades 1-12 from GuruDocDB."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None, auto_seed: bool = True):
        self.db = db_manager or get_db_manager()
        self.db.initialize_schema()
        if auto_seed:
            self._ensure_seeded()

    def _ensure_seeded(self) -> None:
        """Automatically seeds the 150+ master courses across Grades 1-12 if GuruDocDB has fewer than 150 courses."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM curriculum_courses;")
                row = cur.fetchone()
                course_count = int(row["cnt"]) if row else 0
                cur.execute("SELECT COUNT(*) AS cnt FROM academic_calendar_weeks;")
                cal_row = cur.fetchone()
                cal_count = int(cal_row["cnt"]) if cal_row else 0

        if course_count < 150 or cal_count < 52:
            seeder = DatasetSeederService(self.db)
            seeder.seed_all_datasets()

    def _build_subjects_bulk(self, conn, course_rows: List[Dict[str, Any]]) -> List[CurriculumSubject]:
        if not course_rows:
            return []

        course_ids = [r["course_id"] for r in course_rows]

        with conn.cursor() as cur:
            # 1. Phases JP duration
            cur.execute("SELECT phase_code, jp_duration_minutes FROM curriculum_phases;")
            phase_dur_map = {r["phase_code"]: int(r["jp_duration_minutes"]) for r in cur.fetchall()}

            # 2. Master BSKAP subjects (rationale, aims, characteristics)
            cur.execute("SELECT subject_code, rationale, aims, characteristics FROM curriculum_subjects;")
            subj_master_map = {r["subject_code"]: r for r in cur.fetchall()}

            # 3. CP Phase elements
            cur.execute(
                """
                SELECT subject_code, phase, element_code, element_name, cp_description
                FROM curriculum_phase_elements
                ORDER BY subject_code, phase, element_code;
                """
            )
            cp_map: Dict[Tuple[str, str], List[Dict[str, str]]] = {}
            for r in cur.fetchall():
                cp_map.setdefault((r["subject_code"], r["phase"]), []).append(
                    {
                        "kode_elemen": r["element_code"],
                        "nama_elemen": r["element_name"],
                        "deskripsi_cp": r["cp_description"],
                    }
                )

            # 4. DPL & Pedagogical models
            cur.execute("SELECT code, dimension_name FROM graduate_dimensions ORDER BY code;")
            dpl_map = {r["code"]: r["dimension_name"] for r in cur.fetchall()}

            cur.execute("SELECT model_code, model_name FROM pedagogical_models;")
            model_map = {r["model_code"]: r["model_name"] for r in cur.fetchall()}

            # 5. Bulk fetch chapters for requested courses
            cur.execute(
                """
                SELECT *
                FROM curriculum_chapters
                WHERE course_id = ANY(%s)
                ORDER BY course_id, semester, chapter_number;
                """,
                (course_ids,),
            )
            all_chapter_rows = cur.fetchall()
            chapter_ids = [r["chapter_id"] for r in all_chapter_rows]

            # 6. Bulk fetch TPs for those chapters
            tps_by_chapter: Dict[str, List[LearningObjective]] = {}
            if chapter_ids:
                cur.execute(
                    """
                    SELECT *
                    FROM learning_objectives_tp
                    WHERE chapter_id = ANY(%s)
                    ORDER BY chapter_id, atp_sequence, tp_id;
                    """,
                    (chapter_ids,),
                )
                for tp_r in cur.fetchall():
                    tps_by_chapter.setdefault(tp_r["chapter_id"], []).append(
                        LearningObjective(
                            code=tp_r["tp_code"],
                            deskripsi=tp_r["tp_description"],
                            alokasi_jp=int(tp_r["allocated_jp"]),
                            urutan_atp=int(tp_r["atp_sequence"]),
                            ringkasan_rapor=tp_r.get("rapor_summary_phrase", ""),
                            level_kognitif_bloom=tp_r.get("bloom_cognitive_level", "C3 - Menerapkan"),
                        )
                    )

        chapters_by_course: Dict[str, List[ChapterTopic]] = {}
        for ch_row in all_chapter_rows:
            ch_id = ch_row["chapter_id"]
            c_id = ch_row["course_id"]
            dpl_codes = ch_row.get("graduate_dimension_codes") or []
            dpl_names = [dpl_map.get(c, c) for c in dpl_codes] or ["Penalaran Kritis", "Kemandirian", "Kolaborasi"]
            rec_model_code = ch_row.get("recommended_model_code", "INQUIRY")
            rec_model_name = model_map.get(rec_model_code, rec_model_code)

            chapters_by_course.setdefault(c_id, []).append(
                ChapterTopic(
                    id=ch_id,
                    semester=int(ch_row["semester"]),
                    nomor_bab=int(ch_row["chapter_number"]),
                    judul_bab=ch_row["chapter_title"],
                    alokasi_jp=int(ch_row["allocated_jp"]),
                    tujuan_pembelajaran=tps_by_chapter.get(ch_id, []),
                    dimensi_profil_lulusan=dpl_names,
                    model_pembelajaran_default=rec_model_name,
                    elemen_cp=ch_row.get("element_names", ""),
                    estimasi_pertemuan=int(ch_row.get("estimated_meetings", 3)),
                    rentang_minggu_promes=ch_row.get("promes_week_range", ""),
                    modul_ajar_template=ch_row.get("modul_ajar_payload") or {},
                )
            )

        subjects_result: List[CurriculumSubject] = []
        for course_row in course_rows:
            course_id = course_row["course_id"]
            subject_code = course_row["subject_code"]
            jenjang = course_row["education_level"]
            kelas = int(course_row["grade"])
            fase = course_row["phase"]
            durasi_jp = phase_dur_map.get(fase, 35 if jenjang == "SD" else (40 if jenjang == "SMP" else 45))
            master_info = subj_master_map.get(subject_code, {})

            subjects_result.append(
                CurriculumSubject(
                    id=course_id,
                    id_mapel_bskap=subject_code,
                    jenjang=jenjang,
                    kelas=kelas,
                    fase=fase,
                    nama_mapel=course_row["subject_name"],
                    alokasi_jp_mingguan=int(course_row["jp_per_week"]),
                    total_alokasi_jp_tahun=int(course_row["total_jp_intracurricular_year"]),
                    durasi_1_jp_menit=durasi_jp,
                    buku_rujukan_sibi=course_row.get("sibi_reference_book") or "",
                    rasional_bskap=master_info.get("rationale") or "",
                    tujuan_bskap=master_info.get("aims") or "",
                    karakteristik_bskap=master_info.get("characteristics") or "",
                    elemen_cp_resmi=cp_map.get((subject_code, fase), []),
                    verification_status=course_row.get("verification_status") or "DRAFT",
                    verification_score=int(course_row.get("verification_score") or 0),
                    bab_list=chapters_by_course.get(course_id, []),
                )
            )
        return subjects_result

    def get_subjects(self, jenjang: Optional[str] = None, kelas: Optional[int] = None) -> List[CurriculumSubject]:
        """Queries curriculum courses from GuruDocDB filtered by jenjang and/or grade."""
        query = "SELECT * FROM curriculum_courses WHERE 1=1"
        params: List[Any] = []
        if jenjang:
            query += " AND UPPER(education_level) = %s"
            params.append(jenjang.upper())
        if kelas is not None:
            query += " AND grade = %s"
            params.append(int(kelas))
        query += " ORDER BY education_level, grade, subject_name;"

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                course_rows = cur.fetchall()
            return self._build_subjects_bulk(conn, course_rows)

    def get_subject_by_id(self, subject_id: str) -> Optional[CurriculumSubject]:
        """Finds a specific course by course_id (e.g. 'SMA-K11-INF') from GuruDocDB."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM curriculum_courses WHERE course_id = %s;", (subject_id,))
                row = cur.fetchone()
            if not row:
                return None
            built = self._build_subjects_bulk(conn, [row])
            return built[0] if built else None

    def get_chapter(self, subject_id: str, chapter_id: str) -> Optional[ChapterTopic]:
        subj = self.get_subject_by_id(subject_id)
        if not subj:
            return None
        return subj.get_chapter(chapter_id)

    def get_raw_modul_template(self, subject_id: str, chapter_id: str) -> Optional[dict]:
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                suffix_pat = f"%-B{chapter_id.split('-B')[-1]}" if "-B" in chapter_id else f"%{chapter_id}"
                cur.execute(
                    """
                    SELECT modul_ajar_payload FROM curriculum_chapters
                    WHERE course_id = %s AND (chapter_id = %s OR chapter_id LIKE %s);
                    """,
                    (subject_id, chapter_id, suffix_pat),
                )
                row = cur.fetchone()
                return row["modul_ajar_payload"] if row else None

    def get_profil_lulusan_dimensions(self) -> List[str]:
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT dimension_name FROM graduate_dimensions ORDER BY code;")
                rows = cur.fetchall()
                return [r["dimension_name"] for r in rows]

    def get_calendar_weeks(self, semester: int) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT month_number, month_name, week_in_month, week_status, table_code, effective_week_sequence, description
                    FROM academic_calendar_weeks
                    WHERE semester = %s
                    ORDER BY id;
                    """,
                    (int(semester),),
                )
                return list(cur.fetchall())

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
        from psycopg.types.json import Jsonb

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # 1. Fetch course metadata
                cur.execute(
                    """
                    SELECT subject_code, education_level, grade, phase, jp_per_week, subject_name
                    FROM curriculum_courses
                    WHERE course_id = %s;
                    """,
                    (course_id,),
                )
                course_row = cur.fetchone()
                if not course_row:
                    raise ValueError(f"Course '{course_id}' not found in curriculum_courses")

                subject_code = course_row["subject_code"]
                jenjang = course_row["education_level"]
                kelas = int(course_row["grade"])
                fase = course_row["phase"]
                jp_minggu = int(course_row.get("jp_per_week") or 3)

                model_code = "PBL" if "Problem" in model_pembelajaran else (
                    "PJBL" if "Project" in model_pembelajaran else (
                        "DISCOVERY" if "Discovery" in model_pembelajaran else (
                            "CONTEXTUAL" if "Kontekstual" in model_pembelajaran else "INQUIRY"
                        )
                    )
                )

                est_meetings = max(1, alokasi_jp // max(1, jp_minggu))
                promes_range = f"Minggu Efektif Semester {semester}"
                dpl_codes = ["DPL-3", "DPL-5", "DPL-6"]

                # 2. Insert into curriculum_chapters
                cur.execute(
                    """
                    INSERT INTO curriculum_chapters (
                        chapter_id, course_id, subject_code, education_level, grade, phase,
                        semester, chapter_number, chapter_title, element_names, allocated_jp,
                        estimated_meetings, promes_week_range, recommended_model_code,
                        graduate_dimension_codes, modul_ajar_payload
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chapter_id) DO UPDATE SET
                        course_id = EXCLUDED.course_id,
                        subject_code = EXCLUDED.subject_code,
                        education_level = EXCLUDED.education_level,
                        grade = EXCLUDED.grade,
                        phase = EXCLUDED.phase,
                        semester = EXCLUDED.semester,
                        chapter_number = EXCLUDED.chapter_number,
                        chapter_title = EXCLUDED.chapter_title,
                        element_names = EXCLUDED.element_names,
                        allocated_jp = EXCLUDED.allocated_jp,
                        estimated_meetings = EXCLUDED.estimated_meetings,
                        promes_week_range = EXCLUDED.promes_week_range,
                        recommended_model_code = EXCLUDED.recommended_model_code,
                        graduate_dimension_codes = EXCLUDED.graduate_dimension_codes,
                        modul_ajar_payload = EXCLUDED.modul_ajar_payload;
                    """,
                    (
                        chapter_id,
                        course_id,
                        subject_code,
                        jenjang,
                        kelas,
                        fase,
                        semester,
                        nomor_bab,
                        judul_bab,
                        elemen_cp,
                        alokasi_jp,
                        est_meetings,
                        promes_range,
                        model_code,
                        dpl_codes,
                        Jsonb(modul_ajar_payload),
                    ),
                )

                # 3. Insert TPs into learning_objectives_tp
                built_tps: List[LearningObjective] = []
                for idx, tp in enumerate(tps):
                    tp_code = tp.get("code") or f"TP.{kelas}.{nomor_bab}.{idx + 1}"
                    tp_desc = tp.get("deskripsi") or f"Menerapkan konsep {judul_bab}."
                    tp_jp = int(tp.get("alokasi_jp") or max(2, alokasi_jp // max(1, len(tps))))
                    atp_seq = idx + 1
                    rapor_phrase = tp_desc[:100]

                    cur.execute(
                        """
                        INSERT INTO learning_objectives_tp (
                            chapter_id, tp_code, atp_sequence, tp_description,
                            rapor_summary_phrase, allocated_jp, bloom_cognitive_level
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (chapter_id, tp_code) DO UPDATE SET
                            atp_sequence = EXCLUDED.atp_sequence,
                            tp_description = EXCLUDED.tp_description,
                            rapor_summary_phrase = EXCLUDED.rapor_summary_phrase,
                            allocated_jp = EXCLUDED.allocated_jp,
                            bloom_cognitive_level = EXCLUDED.bloom_cognitive_level;
                        """,
                        (
                            chapter_id,
                            tp_code,
                            atp_seq,
                            tp_desc,
                            rapor_phrase,
                            tp_jp,
                            "C3 - Menerapkan",
                        ),
                    )

                    built_tps.append(
                        LearningObjective(
                            code=tp_code,
                            deskripsi=tp_desc,
                            alokasi_jp=tp_jp,
                            urutan_atp=atp_seq,
                            ringkasan_rapor=rapor_phrase,
                            level_kognitif_bloom="C3 - Menerapkan",
                        )
                    )

        return ChapterTopic(
            id=chapter_id,
            semester=semester,
            nomor_bab=nomor_bab,
            judul_bab=judul_bab,
            alokasi_jp=alokasi_jp,
            tujuan_pembelajaran=built_tps,
            dimensi_profil_lulusan=["Penalaran Kritis", "Kemandirian", "Kolaborasi"],
            model_pembelajaran_default=model_pembelajaran,
            elemen_cp=elemen_cp,
            estimasi_pertemuan=est_meetings,
            rentang_minggu_promes=promes_range,
            modul_ajar_template=modul_ajar_payload,
        )
