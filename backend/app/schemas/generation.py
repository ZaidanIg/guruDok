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
    PRESENSI = "13_presensi"
    DAFTAR_NILAI = "15_daftar_nilai"


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
