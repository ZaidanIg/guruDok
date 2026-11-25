from enum import Enum
from typing import Optional, List, Union
from pydantic import BaseModel, Field, model_validator
from app.core.security import InputSanitizer
from app.schemas.teacher import TeacherProfileCreate, PaperSizeEnum
from app.schemas.curriculum import JenjangEnum, CustomTpItem


class ServiceIdEnum(str, Enum):
    CP_TP = "03_cp_tp"
    ATP = "04_atp"
    PROTA = "05_prota"
    PROMES = "06_promes"
    KKTP = "07_kktp"
    MODUL_AJAR = "08_modul_ajar"
    LKPD = "09_lkpd"
    KUIS = "10_kuis"
    SUMATIF_BAB = "11_sumatif_bab"
    STS_SAS = "12_sts_sas"
    PRESENSI = "13_presensi"
    JURNAL_MENGAJAR = "14_jurnal_mengajar"
    DAFTAR_NILAI = "15_daftar_nilai"
    DESKRIPSI_RAPOR = "16_deskripsi_rapor"
    REKAP_RAPOR = "17_rekap_rapor"


class OutputFormatEnum(str, Enum):
    DOCX = "docx"
    XLSX = "xlsx"
    PDF = "pdf"


class StudentItemInput(BaseModel):
    """Pydantic model for student input in Presensi and Daftar Nilai."""
    nomor_absen: Optional[int] = Field(None, ge=1)
    nisn: Optional[str] = Field("-", max_length=30)
    nama_lengkap: str = Field(..., max_length=200)
    jenis_kelamin: Optional[str] = Field("L", max_length=10)


class CustomChapterItem(BaseModel):
    """Pydantic model representing a custom or modified chapter in multi-chapter documents."""
    id_bab: Optional[str] = Field(None, max_length=50)
    nomor_bab: int = Field(..., ge=1)
    semester: int = Field(..., ge=1, le=2)
    judul_bab: str = Field(..., min_length=2, max_length=300)
    elemen_cp: Optional[str] = Field("Pemahaman Konsep & Keterampilan Proses", max_length=200)
    alokasi_jp_bab: int = Field(..., ge=1, le=200)
    estimasi_jumlah_pertemuan: Optional[int] = Field(None, ge=1)
    rentang_minggu_promes: Optional[str] = Field(None, max_length=150)
    tujuan_pembelajaran: Optional[List[CustomTpItem]] = None


class CustomRubrikDplItem(BaseModel):
    """Pydantic model representing an editable item in the 8 Dimensi Profil Lulusan Rubric (Permendikdasmen No. 10/2025)."""
    no: int = Field(..., ge=1, le=8)
    nama_dimensi: str = Field(..., min_length=2, max_length=150)
    indikator: str = Field(..., min_length=2, max_length=1500)
    is_active: bool = Field(True)


class CustomCpElementItem(BaseModel):
    """Pydantic model representing a custom or modified Capaian Pembelajaran (CP) element."""
    kode_elemen: str = Field(..., min_length=1, max_length=50)
    nama_elemen: str = Field(..., min_length=2, max_length=200)
    deskripsi_cp: str = Field(..., min_length=5, max_length=3000)

    @model_validator(mode="after")
    def sanitize_fields(self):
        self.kode_elemen = InputSanitizer.sanitize_text(self.kode_elemen, max_length=50, allow_empty=False)
        self.nama_elemen = InputSanitizer.sanitize_text(self.nama_elemen, max_length=200, allow_empty=False)
        self.deskripsi_cp = InputSanitizer.sanitize_text(self.deskripsi_cp, max_length=3000, allow_empty=False)
        return self


class CustomQuestionItem(BaseModel):
    """Pydantic model representing a single teacher-authored or blueprint exam question."""
    id: Optional[str] = Field(None, max_length=80)
    tipe_soal: str = Field("PG", max_length=20)
    tp_code: Optional[str] = Field(None, max_length=50)
    level_kognitif: Optional[str] = Field("C1-C2", max_length=30)
    stimulus: Optional[str] = Field("", max_length=3000)
    pertanyaan: str = Field(..., min_length=2, max_length=3000)
    opsi: List[str] = Field(default_factory=list, max_length=5)
    kunci_jawaban: Optional[str] = Field("A", max_length=1500)
    bobot_skor: Optional[int] = Field(None, ge=0, le=100)
    pembahasan: Optional[str] = Field("", max_length=2000)

    @model_validator(mode="after")
    def sanitize_question_fields(self):
        self.pertanyaan = InputSanitizer.sanitize_text(self.pertanyaan, max_length=3000, allow_empty=False)
        if self.stimulus:
            self.stimulus = InputSanitizer.sanitize_text(self.stimulus, max_length=3000)
        if self.tp_code:
            self.tp_code = InputSanitizer.sanitize_text(self.tp_code, max_length=50)
        if self.level_kognitif:
            self.level_kognitif = InputSanitizer.sanitize_text(self.level_kognitif, max_length=30)
        if self.kunci_jawaban:
            self.kunci_jawaban = InputSanitizer.sanitize_text(self.kunci_jawaban, max_length=1500)
        if self.pembahasan:
            self.pembahasan = InputSanitizer.sanitize_text(self.pembahasan, max_length=2000)
        if self.opsi:
            self.opsi = [
                InputSanitizer.sanitize_text(o, max_length=500)
                for o in self.opsi[:5]
                if o is not None
            ]
        self.tipe_soal = "URAIAN" if str(self.tipe_soal).upper() in ("URAIAN", "ISIAN", "ESSAY") else "PG"
        return self


class CustomJurnalRowItem(BaseModel):
    """Pydantic model representing a single editable row in Service 14 (Jurnal Mengajar Harian)."""
    no: Optional[int] = Field(None, ge=1, le=200)
    hari_tanggal: str = Field(..., min_length=1, max_length=120)
    jam_pertemuan: str = Field("", max_length=80)
    tp: str = Field("", max_length=1000)
    materi: str = Field("", max_length=500)
    kegiatan: str = Field("", max_length=1500)
    kehadiran: str = Field("", max_length=250)
    refleksi: str = Field("", max_length=1000)
    paraf: str = Field("", max_length=80)

    @model_validator(mode="after")
    def sanitize_jurnal_row(self):
        self.hari_tanggal = InputSanitizer.sanitize_text(self.hari_tanggal, max_length=120, allow_empty=False)
        for field_name, limit in (
            ("jam_pertemuan", 80),
            ("tp", 1000),
            ("materi", 500),
            ("kegiatan", 1500),
            ("kehadiran", 250),
            ("refleksi", 1000),
            ("paraf", 80),
        ):
            val = getattr(self, field_name)
            if val:
                setattr(self, field_name, InputSanitizer.sanitize_text(val, max_length=limit))
        return self


class CustomRaporEntryItem(BaseModel):
    """Pydantic model representing student score & TP achievement entry for Services 16 & 17 (e-Rapor / Rekap Rapor)."""
    nomor_absen: Optional[int] = Field(None, ge=1, le=100)
    nisn: Optional[str] = Field("-", max_length=30)
    nama_lengkap: str = Field(..., min_length=1, max_length=200)
    nilai_sumatif: Optional[int] = Field(82, ge=0, le=100)
    nilai_sas: Optional[int] = Field(80, ge=0, le=100)
    tp_tertinggi_code: Optional[str] = Field(None, max_length=60)
    tp_terendah_code: Optional[str] = Field(None, max_length=60)
    catatan_deskriptif: Optional[str] = Field("", max_length=1500)

    @model_validator(mode="after")
    def sanitize_rapor_entry(self):
        self.nama_lengkap = InputSanitizer.sanitize_text(self.nama_lengkap, max_length=200, allow_empty=False)
        for field_name, limit in (
            ("nisn", 30),
            ("tp_tertinggi_code", 60),
            ("tp_terendah_code", 60),
            ("catatan_deskriptif", 1500),
        ):
            val = getattr(self, field_name)
            if val:
                setattr(self, field_name, InputSanitizer.sanitize_text(val, max_length=limit))
        return self


class CustomDocumentOverrides(BaseModel):
    """Flexible user overrides allowing teachers to add/edit TPs, readiness, questions, assessments, and classroom rosters."""
    custom_chapters: Optional[List[CustomChapterItem]] = None
    custom_elemen_cp: Optional[List[CustomCpElementItem]] = None
    custom_tps: Optional[List[CustomTpItem]] = None
    tujuan_pembelajaran_custom: Optional[List[CustomTpItem]] = None
    custom_alokasi_jp: Optional[int] = Field(None, ge=1, le=200)
    alokasi_jp_bab: Optional[int] = Field(None, ge=1, le=200)
    kesiapan_murid: Optional[str] = Field(None, max_length=2000)
    karakteristik_materi: Optional[str] = Field(None, max_length=2000)
    lintas_disiplin_ilmu: Optional[str] = Field(None, max_length=1500)
    topik_kontekstual: Optional[str] = Field(None, max_length=1500)
    pemahaman_bermakna: Optional[str] = Field(None, max_length=1500)
    pertanyaan_pemantik: Optional[List[str]] = None
    sarana_prasarana: Optional[str] = Field(None, max_length=1500)
    langkah_pendahuluan: Optional[List[str]] = None
    langkah_memahami: Optional[List[str]] = None
    langkah_inti_memahami: Optional[List[str]] = None
    langkah_mengaplikasi: Optional[List[str]] = None
    langkah_inti_mengaplikasi: Optional[List[str]] = None
    langkah_merefleksi: Optional[List[str]] = None
    langkah_inti_merefleksi: Optional[List[str]] = None
    langkah_penutup: Optional[List[str]] = None
    soal_asesmen_awal: Optional[List[str]] = None
    soal_asesmen_proses: Optional[List[str]] = None
    soal_asesmen_akhir: Optional[List[str]] = None
    judul_lkpd: Optional[str] = Field(None, max_length=500)
    tujuan_lkpd: Optional[str] = Field(None, max_length=1500)
    petunjuk_lkpd: Optional[str] = Field(None, max_length=2000)
    tugas_lkpd_memahami: Optional[str] = Field(None, max_length=2000)
    tugas_lkpd_mengaplikasi: Optional[str] = Field(None, max_length=2000)
    tugas_lkpd_merefleksi: Optional[str] = Field(None, max_length=2000)
    langkah_lkpd: Optional[List[str]] = None
    custom_rubrik_dpl: Optional[List[CustomRubrikDplItem]] = None
    glosarium: Optional[str] = Field(None, max_length=2000)
    cadangan_jp: Optional[int] = Field(0, ge=0, le=60)
    catatan_khusus: Optional[str] = Field(None, max_length=2000)
    # Fase 2A: Classroom & Assessment Overrides
    students: Optional[List[StudentItemInput]] = None
    nama_rombel: Optional[str] = Field(None, max_length=100)
    wali_kelas: Optional[str] = Field(None, max_length=150)
    bulan_presensi: Optional[str] = Field(None, max_length=50)
    kktp_nilai: Optional[int] = Field(75, ge=1, le=100)
    daftar_asesmen_bab: Optional[List[str]] = None
    bobot_nilai: Optional[dict] = None
    # Fase 2B: Exam & Question Blueprint Overrides (Service 10, 11, 12)
    jenis_ujian: Optional[str] = Field("STS", max_length=20)
    cakupan_bab_ids: Optional[List[str]] = None
    jumlah_soal_pg: Optional[int] = Field(None, ge=0, le=50)
    jumlah_soal_uraian: Optional[int] = Field(None, ge=0, le=15)
    tipe_soal_kuis: Optional[str] = Field("CAMPURAN", max_length=30)
    bobot_level: Optional[dict] = None
    alokasi_waktu_menit: Optional[int] = Field(90, ge=0, le=240)
    paket_soal: Optional[str] = Field("A", max_length=10)
    butir_soal_kustom: Optional[List[CustomQuestionItem]] = None
    # Service 14: Jurnal Mengajar Harian Overrides
    hari_mengajar: Optional[List[str]] = None
    tanggal_mulai_semester: Optional[str] = Field(None, max_length=20)
    jam_mengajar: Optional[str] = Field(None, max_length=30)
    jumlah_pertemuan_jurnal: Optional[int] = Field(16, ge=4, le=48)
    custom_jurnal_rows: Optional[List[CustomJurnalRowItem]] = Field(None, max_length=60)
    # Service 16 & 17: Rapor Deskripsi & Rekap Overrides
    rapor_entries: Optional[List[CustomRaporEntryItem]] = Field(None, max_length=60)

    @model_validator(mode="after")
    def sync_and_sanitize(self):
        # 1. Sync TP aliases
        if self.tujuan_pembelajaran_custom and not self.custom_tps:
            self.custom_tps = self.tujuan_pembelajaran_custom
        elif self.custom_tps and not self.tujuan_pembelajaran_custom:
            self.tujuan_pembelajaran_custom = self.custom_tps

        # 2. Sync JP aliases
        if self.alokasi_jp_bab is not None and self.custom_alokasi_jp is None:
            self.custom_alokasi_jp = self.alokasi_jp_bab
        elif self.custom_alokasi_jp is not None and self.alokasi_jp_bab is None:
            self.alokasi_jp_bab = self.custom_alokasi_jp

        # 3. Sync Steps aliases
        if self.langkah_inti_memahami and not self.langkah_memahami:
            self.langkah_memahami = self.langkah_inti_memahami
        elif self.langkah_memahami and not self.langkah_inti_memahami:
            self.langkah_inti_memahami = self.langkah_memahami

        if self.langkah_inti_mengaplikasi and not self.langkah_mengaplikasi:
            self.langkah_mengaplikasi = self.langkah_inti_mengaplikasi
        elif self.langkah_mengaplikasi and not self.langkah_inti_mengaplikasi:
            self.langkah_inti_mengaplikasi = self.langkah_mengaplikasi

        if self.langkah_inti_merefleksi and not self.langkah_merefleksi:
            self.langkah_merefleksi = self.langkah_inti_merefleksi
        elif self.langkah_merefleksi and not self.langkah_inti_merefleksi:
            self.langkah_inti_merefleksi = self.langkah_merefleksi

        # 4. Sanitize text fields
        str_fields = [
            "kesiapan_murid",
            "karakteristik_materi",
            "lintas_disiplin_ilmu",
            "topik_kontekstual",
            "pemahaman_bermakna",
            "sarana_prasarana",
            "judul_lkpd",
            "tujuan_lkpd",
            "petunjuk_lkpd",
            "tugas_lkpd_memahami",
            "tugas_lkpd_mengaplikasi",
            "tugas_lkpd_merefleksi",
            "glosarium",
            "catatan_khusus",
            "nama_rombel",
            "wali_kelas",
            "bulan_presensi",
            "tanggal_mulai_semester",
            "jam_mengajar",
        ]
        for f_name in str_fields:
            val = getattr(self, f_name)
            if val is not None:
                setattr(self, f_name, InputSanitizer.sanitize_text(val, max_length=2000))

        list_fields = [
            "pertanyaan_pemantik",
            "langkah_pendahuluan",
            "langkah_memahami",
            "langkah_inti_memahami",
            "langkah_mengaplikasi",
            "langkah_inti_mengaplikasi",
            "langkah_merefleksi",
            "langkah_inti_merefleksi",
            "langkah_penutup",
            "soal_asesmen_awal",
            "soal_asesmen_proses",
            "soal_asesmen_akhir",
            "langkah_lkpd",
            "hari_mengajar",
        ]
        for lf in list_fields:
            items = getattr(self, lf)
            if items is not None:
                cleaned_list = [
                    InputSanitizer.sanitize_text(it, max_length=1000)
                    for it in items
                    if it and it.strip()
                ]
                setattr(self, lf, cleaned_list)

        # 5. Sanitize custom_rubrik_dpl
        if self.custom_rubrik_dpl:
            for r_item in self.custom_rubrik_dpl:
                r_item.nama_dimensi = InputSanitizer.sanitize_text(r_item.nama_dimensi, max_length=150)
                r_item.indikator = InputSanitizer.sanitize_text(r_item.indikator, max_length=1500)

        # 6. Sanitize custom_chapters
        if self.custom_chapters:
            for ch in self.custom_chapters:
                ch.judul_bab = InputSanitizer.sanitize_text(ch.judul_bab, max_length=300)
                if ch.elemen_cp:
                    ch.elemen_cp = InputSanitizer.sanitize_text(ch.elemen_cp, max_length=200)
                if ch.rentang_minggu_promes:
                    ch.rentang_minggu_promes = InputSanitizer.sanitize_text(ch.rentang_minggu_promes, max_length=150)
                if ch.tujuan_pembelajaran:
                    for tp in ch.tujuan_pembelajaran:
                        tp.deskripsi = InputSanitizer.sanitize_text(tp.deskripsi, max_length=1000)
        return self


class DocumentGenerateRequest(BaseModel):
    service_id: ServiceIdEnum
    jenjang: JenjangEnum
    kelas: int = Field(..., ge=1, le=12)
    subject_id: str = Field(..., min_length=2, max_length=50)
    semester: int = Field(..., ge=1, le=2)
    chapter_id: Optional[str] = Field(None, max_length=50)
    model_pembelajaran: Optional[str] = Field("Inquiry Based Learning (Mendalam/DL)", max_length=100)
    paper_size: PaperSizeEnum = PaperSizeEnum.F4
    output_format: Optional[OutputFormatEnum] = None
    teacher_id: Optional[str] = None
    teacher_profile: Optional[TeacherProfileCreate] = None
    include_lkpd: bool = True
    include_asesmen: bool = True
    include_rubrik: bool = True
    custom_overrides: Optional[CustomDocumentOverrides] = None

    @model_validator(mode="after")
    def sanitize_request(self):
        self.subject_id = InputSanitizer.sanitize_text(self.subject_id, max_length=50, allow_empty=False)
        if self.chapter_id:
            self.chapter_id = InputSanitizer.sanitize_text(self.chapter_id, max_length=50)
        if self.model_pembelajaran:
            self.model_pembelajaran = InputSanitizer.sanitize_text(self.model_pembelajaran, max_length=100)
        return self


class DocumentGenerateResponse(BaseModel):
    job_id: str
    service_id: ServiceIdEnum
    service_name: str
    filename: str
    file_format: OutputFormatEnum
    paper_size: PaperSizeEnum
    download_url: str
    file_size_bytes: int
    file_size_human: str
    total_pages_approx: int
    execution_time_ms: Union[int, float]
    created_at: str


class HistoryDocumentItem(BaseModel):
    id: str
    service_id: str
    service_name: str
    filename: str
    file_format: OutputFormatEnum
    paper_size: PaperSizeEnum
    file_url: str
    file_size_human: str
    created_at: str
    parameters: Optional[dict] = None
