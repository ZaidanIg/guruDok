from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.core.security import InputSanitizer


class PaperSizeEnum(str, Enum):
    F4 = "F4"
    A4 = "A4"


class TeacherProfileCreate(BaseModel):
    """Zero-Trust input schema for teacher and school profile."""
    nama_guru: str = Field(..., min_length=2, max_length=100, description="Nama lengkap guru dengan gelar")
    nip_guru: str = Field("-", max_length=25, description="NIP 18 digit, NUPTK 16 digit, atau '-'")
    nama_sekolah: str = Field(..., min_length=3, max_length=120, description="Nama resmi sekolah/madrasah")
    npsn: Optional[str] = Field(None, max_length=10, description="Nomor Pokok Sekolah Nasional (8 digit)")
    kabupaten_kota: str = Field(..., min_length=3, max_length=80, description="Kabupaten atau Kota")
    provinsi: str = Field(..., min_length=3, max_length=80, description="Provinsi")
    nama_kepala_sekolah: str = Field(..., min_length=2, max_length=100, description="Nama Kepala Sekolah dengan gelar")
    nip_kepala_sekolah: str = Field("-", max_length=25, description="NIP Kepala Sekolah")
    no_whatsapp: str = Field(..., min_length=10, max_length=20, description="Nomor WhatsApp aktif untuk pengiriman dokumen")
    email: Optional[str] = Field(None, max_length=100, description="Alamat email aktif")
    ukuran_kertas_default: PaperSizeEnum = Field(PaperSizeEnum.F4, description="Ukuran kertas cetak: F4 atau A4")

    @field_validator("nama_guru", "nama_sekolah", "kabupaten_kota", "provinsi", "nama_kepala_sekolah")
    @classmethod
    def sanitize_string_fields(cls, v: str) -> str:
        return InputSanitizer.sanitize_text(v, max_length=120, allow_empty=False)

    @field_validator("no_whatsapp")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return InputSanitizer.validate_and_normalize_phone(v)

    @field_validator("nip_guru", "nip_kepala_sekolah")
    @classmethod
    def validate_nip_field(cls, v: str) -> str:
        return InputSanitizer.validate_nip(v)


class TeacherProfileResponse(BaseModel):
    """Output schema for Teacher Profile."""
    id: str
    nama_guru: str
    nip_guru: str
    nama_sekolah: str
    npsn: Optional[str] = None
    kabupaten_kota: str
    provinsi: str
    nama_kepala_sekolah: str
    nip_kepala_sekolah: str
    no_whatsapp: str
    email: Optional[str] = None
    ukuran_kertas_default: str
    created_at: str
