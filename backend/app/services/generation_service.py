import time
import re
from typing import Optional, List
from psycopg.types.json import Jsonb

from app.core.database import DatabaseManager, get_db_manager
from app.core.exceptions import CurriculumNotFoundError, ValidationError
from app.models.teacher import TeacherProfile
from app.models.document import DocumentGenerationJob
from app.repositories.base import ICurriculumRepository, ITeacherRepository
from app.schemas.generation import DocumentGenerateRequest, DocumentGenerateResponse, ServiceIdEnum
from app.services.storage_service import IStorageService
from app.services.collection_service import CollectionService
from app.services.document_engine.generator_factory import DocumentEngineFactory


class DocumentGenerationService:
    """Core domain service orchestrating deterministic document generation backed by GuruDocDB."""

    SERVICE_DISPLAY_NAMES = {
        ServiceIdEnum.CP_TP: "Capaian Pembelajaran & Alur Tujuan (CP-TP)",
        ServiceIdEnum.ATP: "Alur Tujuan Pembelajaran (ATP)",
        ServiceIdEnum.PROTA: "Program Tahunan (Prota)",
        ServiceIdEnum.PROMES: "Program Semester (Promes)",
        ServiceIdEnum.KKTP: "Kriteria Ketercapaian Tujuan Pembelajaran (KKTP)",
        ServiceIdEnum.MODUL_AJAR: "Modul Ajar / RPP Lengkap (Deep Learning 3M)",
        ServiceIdEnum.LKPD: "Lembar Kerja Peserta Didik Mandiri (LKPD)",
        ServiceIdEnum.KUIS: "Soal Harian & Kuis Cepat",
        ServiceIdEnum.SUMATIF_BAB: "Asesmen Sumatif Lingkup Materi (Bab)",
        ServiceIdEnum.STS_SAS: "Soal STS & SAS (Kisi-Kisi, Kartu Soal & LJK)",
        ServiceIdEnum.PRESENSI: "Presensi Siswa Bulanan",
        ServiceIdEnum.DAFTAR_NILAI: "Buku Pengolahan Daftar Nilai Siswa",
    }

    def __init__(
        self,
        curriculum_repo: ICurriculumRepository,
        teacher_repo: ITeacherRepository,
        storage_service: IStorageService,
        db_manager: Optional[DatabaseManager] = None,
    ):
        self.curriculum_repo = curriculum_repo
        self.teacher_repo = teacher_repo
        self.storage_service = storage_service
        self.db = db_manager or get_db_manager()
        self._history: List[DocumentGenerationJob] = []

    def generate_document(
        self, req: DocumentGenerateRequest, user_id: Optional[str] = None
    ) -> DocumentGenerateResponse:
        start_time = time.perf_counter()

        # 1. Resolve Curriculum Subject
        subject = self.curriculum_repo.get_subject_by_id(req.subject_id)
        if not subject:
            raise CurriculumNotFoundError(f"Subject '{req.subject_id}' does not exist in master curriculum database.")

        # 1b. Multi-Chapter Override (Sprint 34: Custom Chapters / Mode Kustom / Mode Modifikasi)
        if req.custom_overrides and req.custom_overrides.custom_chapters:
            from app.models.curriculum import ChapterTopic, LearningObjective
            import copy
            subject = copy.copy(subject)
            custom_topic_list = []
            for c_item in req.custom_overrides.custom_chapters:
                ch_id = c_item.id_bab or f"{req.subject_id}-B{c_item.nomor_bab:02d}"
                tps = []
                if c_item.tujuan_pembelajaran:
                    for idx, tp in enumerate(c_item.tujuan_pembelajaran, start=1):
                        tps.append(
                            LearningObjective(
                                code=tp.code or f"TP.{subject.kelas}.{c_item.nomor_bab}.{idx}",
                                deskripsi=tp.deskripsi,
                                alokasi_jp=tp.alokasi_jp or 4,
                                urutan_atp=idx,
                            )
                        )
                else:
                    half_jp = max(2, c_item.alokasi_jp_bab // 2)
                    rem_jp = max(2, c_item.alokasi_jp_bab - half_jp)
                    tps = [
                        LearningObjective(
                            code=f"TP.{subject.kelas}.{c_item.nomor_bab}.1",
                            deskripsi=f"Memahami konsep dasar dan materi pokok {c_item.judul_bab}.",
                            alokasi_jp=half_jp,
                            urutan_atp=1,
                        ),
                        LearningObjective(
                            code=f"TP.{subject.kelas}.{c_item.nomor_bab}.2",
                            deskripsi=f"Menerapkan dan mengeksplorasi solusi kontekstual terkait {c_item.judul_bab}.",
                            alokasi_jp=rem_jp,
                            urutan_atp=2,
                        ),
                    ]
                custom_topic_list.append(
                    ChapterTopic(
                        id=ch_id,
                        semester=c_item.semester,
                        nomor_bab=c_item.nomor_bab,
                        judul_bab=c_item.judul_bab,
                        elemen_cp=c_item.elemen_cp or "Pemahaman Konsep & Keterampilan Proses",
                        alokasi_jp=c_item.alokasi_jp_bab,
                        estimasi_pertemuan=c_item.estimasi_jumlah_pertemuan or max(1, c_item.alokasi_jp_bab // max(1, subject.alokasi_jp_mingguan)),
                        rentang_minggu_promes=c_item.rentang_minggu_promes or f"Minggu Efektif Semester {c_item.semester}",
                        tujuan_pembelajaran=tps,
                    )
                )
            subject.bab_list = custom_topic_list

        # 2. Resolve Chapter if requested
        chapter = None
        if req.chapter_id:
            chapter = subject.get_chapter(req.chapter_id)
            if not chapter and req.custom_overrides and req.custom_overrides.custom_chapters:
                # If custom chapter id match fallback
                for ch in subject.bab_list:
                    if ch.id == req.chapter_id or str(ch.nomor_bab) == str(req.chapter_id):
                        chapter = ch
                        break
            if not chapter:
                raise CurriculumNotFoundError(f"Chapter '{req.chapter_id}' not found in subject '{subject.nama_mapel}'.")

        # 3. Resolve Teacher Profile
        teacher: Optional[TeacherProfile] = None
        if req.teacher_profile:
            existing = self.teacher_repo.find_by_phone(req.teacher_profile.no_whatsapp)
            if existing:
                existing.nama_guru = req.teacher_profile.nama_guru
                existing.nip_guru = req.teacher_profile.nip_guru
                existing.nama_sekolah = req.teacher_profile.nama_sekolah
                existing.npsn = req.teacher_profile.npsn
                existing.kabupaten_kota = req.teacher_profile.kabupaten_kota
                existing.provinsi = req.teacher_profile.provinsi
                existing.nama_kepala_sekolah = req.teacher_profile.nama_kepala_sekolah
                existing.nip_kepala_sekolah = req.teacher_profile.nip_kepala_sekolah
                existing.ukuran_kertas_default = req.teacher_profile.ukuran_kertas_default.value
                teacher = self.teacher_repo.save(existing)
            else:
                new_teacher = TeacherProfile(
                    nama_guru=req.teacher_profile.nama_guru,
                    nip_guru=req.teacher_profile.nip_guru,
                    nama_sekolah=req.teacher_profile.nama_sekolah,
                    npsn=req.teacher_profile.npsn,
                    kabupaten_kota=req.teacher_profile.kabupaten_kota,
                    provinsi=req.teacher_profile.provinsi,
                    nama_kepala_sekolah=req.teacher_profile.nama_kepala_sekolah,
                    nip_kepala_sekolah=req.teacher_profile.nip_kepala_sekolah,
                    no_whatsapp=req.teacher_profile.no_whatsapp,
                    email=req.teacher_profile.email,
                    ukuran_kertas_default=req.teacher_profile.ukuran_kertas_default.value,
                )
                teacher = self.teacher_repo.save(new_teacher)
        elif req.teacher_id:
            teacher = self.teacher_repo.find_by_id(req.teacher_id)
            if not teacher:
                raise ValidationError(f"Teacher profile with ID '{req.teacher_id}' was not found.")

        if not teacher:
            teacher = TeacherProfile(
                id="anon-placeholder",
                nama_guru="........................................",
                nip_guru="-",
                nama_sekolah="........................................",
                npsn="-",
                kabupaten_kota="....................",
                provinsi="",
                nama_kepala_sekolah="........................................",
                nip_kepala_sekolah="-",
                no_whatsapp="-",
                ukuran_kertas_default=req.paper_size.value,
            )

        # 4. Engine Strategy & Output Format Selection (docx, xlsx, or pdf)
        if req.output_format:
            file_format = req.output_format.value
        else:
            file_format = "xlsx" if req.service_id == ServiceIdEnum.PROMES else "docx"
        engine = DocumentEngineFactory.get_engine(req.service_id, req.output_format)

        # 5. Generate Binary File Bytes Enriched from GuruDocDB
        raw_template = None
        if req.chapter_id and hasattr(self.curriculum_repo, "get_raw_modul_template"):
            raw_template = self.curriculum_repo.get_raw_modul_template(req.subject_id, req.chapter_id)
        if req.service_id == ServiceIdEnum.PROMES and hasattr(self.curriculum_repo, "get_calendar_weeks"):
            cal_weeks = self.curriculum_repo.get_calendar_weeks(req.semester)
            raw_template = {"calendar_weeks": cal_weeks}

        file_bytes = engine.generate(
            request=req,
            subject=subject,
            chapter=chapter,
            teacher=teacher,
            raw_template=raw_template,
        )

        # 6. Generate Clean & Safe Filename
        service_slug = req.service_id.value.replace("_", "-")
        mapel_clean = re.sub(r"[^a-zA-Z0-9]", "_", subject.nama_mapel)[:15].strip("_")
        bab_part = f"_Bab{chapter.nomor_bab}" if chapter else ""
        filename = f"{service_slug}_{mapel_clean}_K{subject.kelas}_Smtr{req.semester}{bab_part}_{int(time.time())}.{file_format}"

        # 7. Persist to Storage
        download_url = self.storage_service.save_file(filename, file_bytes)

        # 8. Record Job in Memory & GuruDocDB (generated_documents_log)
        execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        size_bytes = len(file_bytes)
        params_payload = {
            "jenjang": req.jenjang.value,
            "kelas": req.kelas,
            "subject_id": req.subject_id,
            "chapter_id": req.chapter_id,
            "semester": req.semester,
            "user_id": user_id,
        }

        job = DocumentGenerationJob(
            service_id=req.service_id.value,
            service_name=self.SERVICE_DISPLAY_NAMES.get(req.service_id, "Dokumen Kurikulum Merdeka"),
            teacher_id=teacher.id,
            file_format=file_format,
            filename=filename,
            paper_size=req.paper_size.value,
            file_url=download_url,
            file_size_bytes=size_bytes,
            parameters=params_payload,
        )
        self._history.insert(0, job)
        self._persist_job_to_db(job, subject, user_id=user_id)
        # Silent auto-persist of non-PII questions & curriculum overrides (never stores KOP Surat / student PII)
        CollectionService(self.db).collect_from_generation(req, subject)

        return DocumentGenerateResponse(
            job_id=job.id,
            service_id=job.service_id,
            service_name=job.service_name,
            filename=job.filename,
            file_format=job.file_format,
            paper_size=job.paper_size,
            download_url=job.file_url,
            file_size_bytes=job.file_size_bytes,
            file_size_human=job.to_dict()["file_size_human"],
            total_pages_approx=max(1, size_bytes // 15000),
            execution_time_ms=execution_time_ms,
            created_at=job.created_at.isoformat(),
        )

    def _persist_job_to_db(
        self, job: DocumentGenerationJob, subject, user_id: Optional[str] = None
    ) -> None:
        """Persists generated document job into generated_documents_log table in GuruDocDB."""
        try:
            db_teacher_id = None if job.teacher_id == "anon-placeholder" else job.teacher_id
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO service_templates (service_code, service_name, cluster_number, is_mvp_phase1, required_form_schema)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (service_code) DO NOTHING;
                        """,
                        (job.service_id, job.service_name, 2, False, Jsonb({"service_id": job.service_id})),
                    )
                    cur.execute(
                        """
                        INSERT INTO generated_documents_log (
                            id, user_id, teacher_id, service_code, service_name, education_level, grade,
                            subject_id, subject_name, semester, filename, paper_size,
                            output_format, file_size_bytes, r2_file_url, form_input_payload
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING;
                        """,
                        (
                            job.id,
                            user_id,
                            db_teacher_id,
                            job.service_id,
                            job.service_name,
                            subject.jenjang,
                            subject.kelas,
                            subject.id,
                            subject.nama_mapel,
                            int(job.parameters.get("semester", 1)),
                            job.filename,
                            job.paper_size,
                            job.file_format,
                            job.file_size_bytes,
                            job.file_url,
                            Jsonb(job.parameters),
                        ),
                    )
        except Exception:
            # Keep in-memory history intact if custom mock teacher_repo is used in isolated unit test
            pass

    def get_history(self, limit: int = 20, user_id: Optional[str] = None) -> List[dict]:
        """Reads document generation history directly from GuruDocDB, isolated per user_id when provided."""
        from app.core.config import settings

        if settings.auth_required_for_download and not user_id:
            return []

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    if user_id:
                        cur.execute(
                            """
                            SELECT *
                            FROM generated_documents_log
                            WHERE user_id = %s::uuid
                            ORDER BY created_at DESC
                            LIMIT %s;
                            """,
                            (user_id, limit),
                        )
                    else:
                        cur.execute(
                            """
                            SELECT *
                            FROM generated_documents_log
                            ORDER BY created_at DESC
                            LIMIT %s;
                            """,
                            (limit,),
                        )
                    rows = cur.fetchall()
                    if rows:
                        results = []
                        for r in rows:
                            size_kb = round(int(r["file_size_bytes"]) / 1024, 1)
                            results.append(
                                {
                                    "id": r["id"],
                                    "service_id": r["service_code"],
                                    "service_name": r["service_name"],
                                    "teacher_id": r["teacher_id"] or "",
                                    "filename": r["filename"],
                                    "file_format": r["output_format"],
                                    "paper_size": r["paper_size"],
                                    "file_url": r["r2_file_url"],
                                    "file_size_bytes": int(r["file_size_bytes"]),
                                    "file_size_human": f"{size_kb} KB",
                                    "status": "completed",
                                    "parameters": r["form_input_payload"] or {},
                                    "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"]),
                                }
                            )
                        return results
                    if user_id:
                        return []
        except Exception:
            pass
        if user_id:
            filtered = [j for j in self._history if j.parameters.get("user_id") == user_id]
            return [j.to_dict() for j in filtered[:limit]]
        return [j.to_dict() for j in self._history[:limit]]
