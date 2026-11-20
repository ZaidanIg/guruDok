from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class StudentParsedItem(BaseModel):
    """Pydantic model representing a student row parsed from an Excel file."""
    nomor_absen: int = Field(default=1, description="Nomor urut absen siswa")
    nisn: str = Field(default="-", description="Nomor Induk Siswa Nasional / NIS")
    nama_lengkap: str = Field(..., description="Nama lengkap siswa (ter-sanitasi)")
    jenis_kelamin: str = Field(default="L", description="Jenis kelamin ('L' atau 'P')")


class ClassroomParseResponseData(BaseModel):
    """Payload data returned after parsing an uploaded student roster Excel file."""
    detected_header_row: int = Field(..., description="Index baris (1-based) tempat header tabel ditemukan")
    column_mappings: Dict[str, Optional[int]] = Field(..., description="Pemetaan nama kolom ke indeks kolom (0-based)")
    total_rows: int = Field(..., description="Jumlah total siswa yang berhasil dibaca")
    students: List[StudentParsedItem] = Field(default_factory=list, description="Daftar siswa hasil ekstraksi")
    warnings: List[str] = Field(default_factory=list, description="Peringatan atau catatan terkait baris yang diabaikan")


class ClassroomParseResponse(BaseModel):
    """Top-level standard API response for Excel parsing."""
    success: bool = True
    message: str = "File Excel berhasil di-parse."
    data: ClassroomParseResponseData
