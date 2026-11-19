-- ============================================================================
-- GURUDOK MASTER DATABASE SCHEMA (PostgreSQL 16+ / 18+) — TOTAL DATASET SCHEMA
-- Sumber Regulasi & Dataset:
-- 1. Dataset 01: Regulasi, Fase, 8 Dimensi Profil Lulusan (Permendikdasmen 10/2025),
--                Kerangka Pembelajaran Mendalam 3M (PPA Revisi 2025), & Interval KKTP
-- 2. Dataset 02: Struktur Kurikulum & Alokasi JP (Permendikdasmen 13/2025)
-- 3. Dataset 03: Master CP 46 Mata Pelajaran (Kepka BSKAP No. 046/H/KR/2025)
-- 4. Dataset 04: Master Paket Kurikulum Mapel-Kelas, Bab, TP, ATP, & Modul Ajar
-- 5. Dataset 05: Master Kalender Pendidikan 52 Minggu & Matriks Promes Default
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. TABEL PENGGUNA & PROFIL SEKOLAH GURU (MASTER PROFILE)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    google_sub VARCHAR(128) UNIQUE,
    email VARCHAR(255) UNIQUE,
    whatsapp_number VARCHAR(30) UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    avatar_url TEXT,
    role VARCHAR(30) DEFAULT 'teacher',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS teacher_profiles (
    id VARCHAR(64) PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    teacher_name_with_title VARCHAR(150) NOT NULL,
    teacher_nip VARCHAR(50) DEFAULT '-',
    school_name VARCHAR(200) NOT NULL,
    school_npsn VARCHAR(20),
    city_regency VARCHAR(100) NOT NULL,
    province VARCHAR(100),
    headmaster_name VARCHAR(150) NOT NULL,
    headmaster_nip VARCHAR(50) DEFAULT '-',
    supervisor_name VARCHAR(150),
    supervisor_nip VARCHAR(50),
    whatsapp_number VARCHAR(30) UNIQUE,
    email VARCHAR(255),
    default_academic_year VARCHAR(20) DEFAULT '2026/2027',
    default_semester SMALLINT DEFAULT 1 CHECK (default_semester IN (1, 2)),
    default_paper_size VARCHAR(10) DEFAULT 'F4' CHECK (default_paper_size IN ('F4', 'A4')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 2. TABEL DATASET 01: PEMBAGIAN FASE, 8 DPL, MODEL PEDAGOGIS, 3M & KKTP
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curriculum_phases (
    phase_code VARCHAR(20) PRIMARY KEY, -- Fondasi, A, B, C, D, E, F
    education_level VARCHAR(20) NOT NULL, -- PAUD, SD, SMP, SMA
    grades JSONB NOT NULL,
    grade_label VARCHAR(100),
    jp_duration_minutes SMALLINT NOT NULL
);

CREATE TABLE IF NOT EXISTS graduate_dimensions (
    code VARCHAR(10) PRIMARY KEY, -- DPL-1 s.d. DPL-8
    dimension_name VARCHAR(120) NOT NULL,
    legacy_p5_equivalent VARCHAR(150),
    description TEXT NOT NULL,
    classroom_indicator TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pedagogical_models (
    model_code VARCHAR(30) PRIMARY KEY, -- PBL, PJBL, DISCOVERY, INQUIRY, CONTEXTUAL
    model_name VARCHAR(150) NOT NULL,
    suitable_for TEXT,
    syntax_steps JSONB NOT NULL -- Array tahapan sintaks pembelajaran
);

CREATE TABLE IF NOT EXISTS deep_learning_framework (
    item_code VARCHAR(30) PRIMARY KEY, -- PP-1..PP-3, 3M-1..3M-3
    category VARCHAR(40) NOT NULL,     -- PRINSIP_PEMBELAJARAN | PENGALAMAN_BELAJAR_3M
    item_name VARCHAR(120) NOT NULL,
    sequence_order SMALLINT DEFAULT 1,
    description TEXT NOT NULL,
    activity_templates JSONB DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS kktp_intervals (
    range_label VARCHAR(20) PRIMARY KEY, -- 0 - 60, 61 - 74, 75 - 87, 88 - 100
    predicate VARCHAR(60) NOT NULL,
    follow_up_action TEXT NOT NULL,
    rapor_template_text TEXT NOT NULL
);

-- ----------------------------------------------------------------------------
-- 3. TABEL DATASET 02: STRUKTUR KURIKULUM & ALOKASI WAKTU JP (PERMENDIKDASMEN 13/2025)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curriculum_hour_allocations (
    id SERIAL PRIMARY KEY,
    education_level VARCHAR(10) NOT NULL CHECK (education_level IN ('SD', 'SMP', 'SMA')),
    grade SMALLINT NOT NULL CHECK (grade BETWEEN 1 AND 12),
    phase VARCHAR(5) NOT NULL,
    subject_name VARCHAR(150) NOT NULL,
    subject_category VARCHAR(50) DEFAULT 'Wajib',
    jp_duration_minutes SMALLINT NOT NULL,        -- SD=35, SMP=40, SMA=45
    effective_weeks_year SMALLINT NOT NULL,       -- 36 atau 32 minggu
    effective_weeks_sem1 SMALLINT NOT NULL,       -- 18 minggu
    effective_weeks_sem2 SMALLINT NOT NULL,       -- 18 atau 14 minggu
    jp_intracurricular_year SMALLINT NOT NULL,
    jp_cocurricular_year SMALLINT DEFAULT 0,
    total_jp_year SMALLINT NOT NULL,
    jp_per_week SMALLINT NOT NULL,
    UNIQUE (education_level, grade, subject_name)
);

CREATE INDEX IF NOT EXISTS idx_alloc_level_grade ON curriculum_hour_allocations(education_level, grade);

-- ----------------------------------------------------------------------------
-- 4. TABEL DATASET 03: MASTER CAPAIAN PEMBELAJARAN (BSKAP 046/H/KR/2025 - 46 MAPEL)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curriculum_subjects (
    subject_code VARCHAR(20) PRIMARY KEY, -- MAPEL-01 s.d. MAPEL-46
    subject_name VARCHAR(150) NOT NULL,
    education_levels TEXT[] NOT NULL,
    phases TEXT[] NOT NULL,
    rationale TEXT,
    aims TEXT,
    characteristics TEXT,
    regulation_ref VARCHAR(100) DEFAULT 'Kepka BSKAP No. 046/H/KR/2025'
);

CREATE TABLE IF NOT EXISTS curriculum_phase_elements (
    id SERIAL PRIMARY KEY,
    subject_code VARCHAR(20) NOT NULL REFERENCES curriculum_subjects(subject_code) ON DELETE CASCADE,
    phase VARCHAR(10) NOT NULL,
    phase_designation VARCHAR(150),
    element_code VARCHAR(20) NOT NULL,
    element_name VARCHAR(150) NOT NULL,
    cp_description TEXT NOT NULL,
    UNIQUE (subject_code, phase, element_code)
);

CREATE INDEX IF NOT EXISTS idx_cp_subject_phase ON curriculum_phase_elements(subject_code, phase);

-- ----------------------------------------------------------------------------
-- 5. TABEL DATASET 04: PAKET KURIKULUM MAPEL-KELAS, BAB, TP, ATP & MODUL AJAR
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curriculum_courses (
    course_id VARCHAR(40) PRIMARY KEY, -- Contoh: SD-K1-BINDO, SMP-K7-IPA, SD-K2-MAT
    subject_code VARCHAR(20) NOT NULL REFERENCES curriculum_subjects(subject_code),
    education_level VARCHAR(10) NOT NULL,
    grade SMALLINT NOT NULL,
    phase VARCHAR(5) NOT NULL,
    subject_name VARCHAR(150) NOT NULL,
    sibi_reference_book TEXT,
    total_jp_intracurricular_year SMALLINT NOT NULL,
    jp_per_week SMALLINT NOT NULL,
    source_section VARCHAR(40) DEFAULT 'PAKET_LENGKAP' -- PAKET_LENGKAP | KATALOG_TAMBAHAN
);

CREATE INDEX IF NOT EXISTS idx_courses_level_grade ON curriculum_courses(education_level, grade);

CREATE TABLE IF NOT EXISTS curriculum_chapters (
    chapter_id VARCHAR(40) PRIMARY KEY, -- Contoh: IPA-K7-B01, SD-K2-MAT-B01
    course_id VARCHAR(40) NOT NULL REFERENCES curriculum_courses(course_id) ON DELETE CASCADE,
    subject_code VARCHAR(20) NOT NULL REFERENCES curriculum_subjects(subject_code),
    education_level VARCHAR(10) NOT NULL,
    grade SMALLINT NOT NULL,
    phase VARCHAR(5) NOT NULL,
    semester SMALLINT NOT NULL CHECK (semester IN (1, 2)),
    chapter_number SMALLINT NOT NULL,
    chapter_title VARCHAR(255) NOT NULL,
    element_names VARCHAR(200) NOT NULL,
    allocated_jp SMALLINT NOT NULL,
    estimated_meetings SMALLINT NOT NULL,
    promes_week_range VARCHAR(100),
    recommended_model_code VARCHAR(30) REFERENCES pedagogical_models(model_code),
    graduate_dimension_codes TEXT[] NOT NULL,
    modul_ajar_payload JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chapters_filter ON curriculum_chapters(course_id, semester, chapter_number);

CREATE TABLE IF NOT EXISTS learning_objectives_tp (
    tp_id SERIAL PRIMARY KEY,
    chapter_id VARCHAR(40) NOT NULL REFERENCES curriculum_chapters(chapter_id) ON DELETE CASCADE,
    tp_code VARCHAR(40) NOT NULL,
    atp_sequence SMALLINT NOT NULL,
    tp_description TEXT NOT NULL,
    rapor_summary_phrase TEXT NOT NULL,
    allocated_jp SMALLINT NOT NULL,
    bloom_cognitive_level VARCHAR(50),
    UNIQUE (chapter_id, tp_code)
);

CREATE INDEX IF NOT EXISTS idx_tp_chapter ON learning_objectives_tp(chapter_id, atp_sequence);

-- ----------------------------------------------------------------------------
-- 6. TABEL DATASET 05: KALENDER PENDIDIKAN 52 MINGGU & MATRIKS PROMES DEFAULT
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS academic_calendar_weeks (
    id SERIAL PRIMARY KEY,
    academic_year VARCHAR(20) NOT NULL DEFAULT '2026/2027',
    semester SMALLINT NOT NULL CHECK (semester IN (1, 2)),
    month_number SMALLINT NOT NULL CHECK (month_number BETWEEN 1 AND 12),
    month_name VARCHAR(30) NOT NULL,
    week_in_month SMALLINT NOT NULL CHECK (week_in_month BETWEEN 1 AND 5),
    week_status VARCHAR(40) NOT NULL,       -- EFEKTIF, MPLS, STS, SAS, PENGOLAHAN_NILAI, PEMBAGIAN_RAPOR, LIBUR_SEMESTER, dll.
    table_code VARCHAR(15) NOT NULL,        -- JP, MPLS, STS, SAS, RMD, RPR, LSMT, LHR
    effective_week_sequence SMALLINT,       -- 1 s.d. 18 (NULL jika minggu tidak efektif)
    description TEXT,
    UNIQUE (academic_year, semester, month_number, week_in_month)
);

CREATE INDEX IF NOT EXISTS idx_calendar_semester ON academic_calendar_weeks(semester, id);

-- ----------------------------------------------------------------------------
-- 7. TABEL TEMPLATE LAYANAN & LOG RIWAYAT DOKUMEN TER-GENERATE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS service_templates (
    service_code VARCHAR(40) PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    cluster_number SMALLINT NOT NULL,
    is_mvp_phase1 BOOLEAN DEFAULT FALSE,
    template_docx_r2_key VARCHAR(255),
    template_xlsx_r2_key VARCHAR(255),
    required_form_schema JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS generated_documents_log (
    id VARCHAR(64) PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    teacher_id VARCHAR(64) REFERENCES teacher_profiles(id) ON DELETE SET NULL,
    service_code VARCHAR(40) NOT NULL REFERENCES service_templates(service_code),
    service_name VARCHAR(120) NOT NULL,
    education_level VARCHAR(10) NOT NULL,
    grade SMALLINT NOT NULL,
    subject_id VARCHAR(40) NOT NULL,
    subject_name VARCHAR(150) NOT NULL,
    semester SMALLINT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    paper_size VARCHAR(10) NOT NULL DEFAULT 'F4',
    output_format VARCHAR(10) NOT NULL,
    file_size_bytes INTEGER NOT NULL DEFAULT 0,
    r2_file_url TEXT NOT NULL,
    form_input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
