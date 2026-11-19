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


class OutputFormatEnum(str, Enum):
    DOCX = "docx"
    XLSX = "xlsx"
    PDF = "pdf"


class CustomDocumentOverrides(BaseModel):
    """Flexible user overrides allowing teachers to add/edit TPs, readiness, questions, and assessments."""
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
    langkah_lkpd: Optional[List[str]] = None
    glosarium: Optional[str] = Field(None, max_length=2000)
    cadangan_jp: Optional[int] = Field(0, ge=0, le=60)
    catatan_khusus: Optional[str] = Field(None, max_length=2000)

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
