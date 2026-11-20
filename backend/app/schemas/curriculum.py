from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
from app.core.security import InputSanitizer


class JenjangEnum(str, Enum):
    SD = "SD"
    SMP = "SMP"
    SMA = "SMA"


class FaseEnum(str, Enum):
    FASE_A = "Fase A"
    FASE_B = "Fase B"
    FASE_C = "Fase C"
    FASE_D = "Fase D"
    FASE_E = "Fase E"
    FASE_F = "Fase F"


class CustomTpItem(BaseModel):
    """Flexible user-defined or edited Tujuan Pembelajaran (TP) item."""
    code: str = Field(..., min_length=1, max_length=40)
    deskripsi: str = Field(..., min_length=3, max_length=1000)
    alokasi_jp: int = Field(4, ge=1, le=120)

    @model_validator(mode="after")
    def sanitize_fields(self):
        self.code = InputSanitizer.sanitize_text(self.code, max_length=40, allow_empty=False)
        self.deskripsi = InputSanitizer.sanitize_text(self.deskripsi, max_length=1000, allow_empty=False)
        return self


class ChapterCreateRequest(BaseModel):
    """Payload for user-defined custom chapter creation."""
    nomor_bab: int = Field(..., ge=1, le=50)
    semester: int = Field(..., ge=1, le=2)
    judul_bab: str = Field(..., min_length=2, max_length=255)
    elemen_cp: str = Field(..., min_length=2, max_length=255)
    alokasi_jp: int = Field(12, ge=1, le=200)
    model_pembelajaran: Optional[str] = Field("Inquiry Based Learning (Mendalam/DL)", max_length=150)
    daftar_tp: Optional[List[CustomTpItem]] = None

    @model_validator(mode="after")
    def sanitize_fields(self):
        self.judul_bab = InputSanitizer.sanitize_text(self.judul_bab, max_length=255, allow_empty=False)
        self.elemen_cp = InputSanitizer.sanitize_text(self.elemen_cp, max_length=255, allow_empty=False)
        if self.model_pembelajaran:
            self.model_pembelajaran = InputSanitizer.sanitize_text(self.model_pembelajaran, max_length=150)
        return self


class LearningObjectiveResponse(BaseModel):
    code: str
    deskripsi: str
    alokasi_jp: int
    urutan_atp: int = 1
    ringkasan_rapor: str = ""
    level_kognitif_bloom: str = "C3 - Menerapkan"


class ChapterResponse(BaseModel):
    id: str
    semester: int
    nomor_bab: int
    judul_bab: str
    alokasi_jp: int
    elemen_cp: str = ""
    estimasi_pertemuan: int = 3
    rentang_minggu_promes: str = ""
    tujuan_pembelajaran: List[LearningObjectiveResponse]
    dimensi_profil_lulusan: List[str]
    model_pembelajaran_default: str
    modul_ajar_template: Dict[str, Any] = {}


class SubjectResponse(BaseModel):
    id: str
    id_mapel_bskap: str = "MAPEL-01"
    jenjang: str
    kelas: int
    fase: str
    nama_mapel: str
    alokasi_jp_mingguan: int
    total_alokasi_jp_tahun: int
    durasi_1_jp_menit: int = 40
    buku_rujukan_sibi: str = ""
    rasional_bskap: str = ""
    tujuan_bskap: str = ""
    karakteristik_bskap: str = ""
    elemen_cp_resmi: List[Dict[str, str]] = []
    verification_status: str = "DRAFT"
    verification_score: int = 0
    bab_count: int
    bab_list: Optional[List[ChapterResponse]] = None
