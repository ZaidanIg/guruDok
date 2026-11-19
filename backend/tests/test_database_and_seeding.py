import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import DatabaseManager, get_db_manager
from app.services.dataset_seeder import DatasetSeederService
from app.repositories.postgres_curriculum_repo import PostgresCurriculumRepository
from app.repositories.postgres_teacher_repo import PostgresTeacherRepository
from app.models.teacher import TeacherProfile

client = TestClient(app)


class TestDatabaseAndTotalDatasetSeeding:
    """TDD Test Suite for Sprint 05: PostgreSQL (GuruDocDB) Connection, 15-Table DDL, and 100% 5-Dataset Seeding."""

    def test_postgres_gurudocdb_connection(self):
        """1. Verifies live connection to local PostgreSQL database GuruDocDB."""
        db = get_db_manager()
        status_info = db.check_connection()
        assert status_info["connected"] is True
        assert status_info["database"] == "GuruDocDB"
        assert "PostgreSQL" in status_info["server_version"]

    def test_schema_15_tables_initialized(self):
        """2. Verifies all 15 relational tables exist in GuruDocDB after schema initialization."""
        db = get_db_manager()
        db.initialize_schema()

        expected_tables = {
            "users",
            "teacher_profiles",
            "curriculum_phases",
            "graduate_dimensions",
            "pedagogical_models",
            "deep_learning_framework",
            "kktp_intervals",
            "curriculum_hour_allocations",
            "curriculum_subjects",
            "curriculum_phase_elements",
            "curriculum_courses",
            "curriculum_chapters",
            "learning_objectives_tp",
            "academic_calendar_weeks",
            "service_templates",
            "generated_documents_log",
        }

        existing_tables = set(db.get_existing_tables())
        missing = expected_tables - existing_tables
        assert not missing, f"Missing tables in GuruDocDB: {missing}"

    def test_total_5_datasets_seeding_counts(self):
        """3. Verifies 100% of records from all 5 JSON files (01 to 05) are seeded into GuruDocDB."""
        db = get_db_manager()
        db.initialize_schema()

        seeder = DatasetSeederService(db)
        summary = seeder.seed_all_datasets()

        # Dataset 01: Regulasi, Fase, 8 DPL, 5 Model Pedagogis, Kerangka 3M, & 4 Interval KKTP
        assert summary["curriculum_phases"] == 7
        assert summary["graduate_dimensions"] == 8
        assert summary["pedagogical_models"] == 5
        assert summary["deep_learning_framework"] == 6
        assert summary["kktp_intervals"] == 4

        # Dataset 02: Struktur Kurikulum & Alokasi JP Permendikdasmen 13/2025
        assert summary["curriculum_hour_allocations"] >= 90

        # Dataset 03: Master CP BSKAP 046/H/KR/2025 (46 Mapel & 532 Elemen CP)
        assert summary["curriculum_subjects"] == 46
        assert summary["curriculum_phase_elements"] == 532

        # Dataset 04 + Total Grade 1-12 & All Subjects Integration (>= 150 Paket Mapel-Kelas, >= 600 Bab, >= 1500 TP)
        assert summary["curriculum_courses"] >= 150
        assert summary["curriculum_chapters"] >= 600
        assert summary["learning_objectives_tp"] >= 1500

        # Dataset 05: Kalender Pendidikan & Promes Default (26 Minggu Smt 1 + 26 Minggu Smt 2 = 52 Minggu)
        assert summary["academic_calendar_weeks"] == 52

        # Master Service Templates (Minimum 5 MVP services registered)
        assert summary["service_templates"] >= 5

    def test_postgres_curriculum_repository_queries_all_integrated_data(self):
        """4. Verifies PostgresCurriculumRepository reads 100% from GuruDocDB across all 12 grades & all subjects."""
        db = get_db_manager()
        repo = PostgresCurriculumRepository(db)

        # All >= 150 courses across Grades 1 to 12 must be accessible
        all_subjects = repo.get_subjects()
        assert len(all_subjects) >= 150

        # Verify every single grade 1..12 has full subject coverage (SD >= 7, SMP >= 12, SMA >= 18)
        expected_min_per_grade = {
            ("SD", 1): 7,
            ("SD", 2): 7,
            ("SD", 3): 9,
            ("SD", 4): 9,
            ("SD", 5): 10,
            ("SD", 6): 10,
            ("SMP", 7): 12,
            ("SMP", 8): 12,
            ("SMP", 9): 12,
            ("SMA", 10): 18,
            ("SMA", 11): 22,
            ("SMA", 12): 22,
        }
        for (lvl, grd), min_cnt in expected_min_per_grade.items():
            grade_subjs = repo.get_subjects(jenjang=lvl, kelas=grd)
            assert len(grade_subjs) >= min_cnt, f"{lvl} Kelas {grd} only has {len(grade_subjs)} subjects (expected >= {min_cnt})"
            for s in grade_subjs:
                assert len(s.bab_list) >= 4, f"Course {s.id} has fewer than 4 chapters"

        # Verify Informatika Kelas XI Fase F (SMA-K11-INF) from attached reference document is present
        sma_inf_11 = repo.get_subject_by_id("SMA-K11-INF")
        assert sma_inf_11 is not None
        assert sma_inf_11.nama_mapel == "Informatika"
        assert sma_inf_11.fase == "F"
        assert len(sma_inf_11.bab_list) >= 6
        assert "Strategi" in sma_inf_11.bab_list[0].judul_bab or "Informatika" in sma_inf_11.bab_list[0].judul_bab

        # Verify previously missing catalog subject (e.g., SD-K2-MAT from katalog_silabus_bab_tambahan) now has chapters!
        sd_k2_mat = repo.get_subject_by_id("SD-K2-MAT")
        assert sd_k2_mat is not None
        assert sd_k2_mat.jenjang == "SD"
        assert sd_k2_mat.kelas == 2
        assert len(sd_k2_mat.bab_list) == 6

        # Verify SMP-K7-IPA is enriched with BSKAP 046/2025 CP elements & Permendikdasmen 13/2025 JP duration
        smp_ipa = repo.get_subject_by_id("SMP-K7-IPA")
        assert smp_ipa is not None
        assert smp_ipa.id_mapel_bskap == "MAPEL-15"
        assert smp_ipa.durasi_1_jp_menit == 40
        assert len(smp_ipa.elemen_cp_resmi) >= 2
        assert len(smp_ipa.bab_list) == 6

        # Verify calendar weeks from dataset 05 are retrieved from GuruDocDB
        sem1_calendar = repo.get_calendar_weeks(semester=1)
        sem2_calendar = repo.get_calendar_weeks(semester=2)
        assert len(sem1_calendar) == 26
        assert len(sem2_calendar) == 26

        # Verify 8 DPL from GuruDocDB
        dpl = repo.get_profil_lulusan_dimensions()
        assert len(dpl) == 8
        assert "Penalaran Kritis" in dpl

    def test_postgres_teacher_repository_persistence_in_gurudocdb(self):
        """5. Verifies TeacherProfile CRUD persists directly into GuruDocDB (users & teacher_profiles tables)."""
        db = get_db_manager()
        repo = PostgresTeacherRepository(db)

        profile = TeacherProfile(
            nama_guru="Dr. Hendra Wijaya, M.Pd.",
            nip_guru="198403102009021004",
            nama_sekolah="SMA Negeri 1 Yogyakarta",
            npsn="20403174",
            kabupaten_kota="Kota Yogyakarta",
            provinsi="D.I. Yogyakarta",
            nama_kepala_sekolah="Drs. Mulyono, M.M.",
            nip_kepala_sekolah="196708121993031008",
            no_whatsapp="+6281399887766",
            ukuran_kertas_default="F4",
        )

        saved = repo.save(profile)
        assert saved.id == profile.id

        # Query back by ID and by Phone from PostgreSQL
        found_id = repo.find_by_id(saved.id)
        assert found_id is not None
        assert found_id.nama_guru == "Dr. Hendra Wijaya, M.Pd."
        assert found_id.nama_sekolah == "SMA Negeri 1 Yogyakarta"

        found_phone = repo.find_by_phone("+6281399887766")
        assert found_phone is not None
        assert found_phone.npsn == "20403174"

    def test_health_endpoint_reports_gurudocdb_connected(self):
        """6. Verifies GET /api/v1/health reports live GuruDocDB connection and dataset statistics."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert body["database"] == "connected"
        assert body["database_name"] == "GuruDocDB"
        assert body["dataset_stats"]["bskap_subjects"] == 46
        assert body["dataset_stats"]["cp_elements"] == 532
        assert body["dataset_stats"]["courses"] >= 150
        assert body["dataset_stats"]["chapters"] >= 600
