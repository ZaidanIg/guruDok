import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TeacherProfile:
    """Domain model representing a Teacher's official profile and school data."""
    nama_guru: str
    nip_guru: str
    nama_sekolah: str
    kabupaten_kota: str
    provinsi: str
    nama_kepala_sekolah: str
    nip_kepala_sekolah: str
    no_whatsapp: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    npsn: Optional[str] = None
    email: Optional[str] = None
    ukuran_kertas_default: str = "F4"  # F4 / Folio or A4
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_formatted_kop(self) -> dict:
        """Generates structured KOP SURAT dictionary for template injection."""
        return {
            "nama_sekolah": self.nama_sekolah.upper(),
            "kabupaten_kota": self.kabupaten_kota,
            "provinsi": self.provinsi,
            "npsn": self.npsn or "-",
            "nama_guru": self.nama_guru,
            "nip_guru": self.nip_guru if self.nip_guru != "-" else "NIP. -",
        }

    def get_lembar_pengesahan(self, tanggal_pengesahan: Optional[str] = None) -> dict:
        """Generates structured Lembar Pengesahan data for Word document footer."""
        tgl = tanggal_pengesahan or datetime.now().strftime("%d Juli %Y")
        kota = self.kabupaten_kota.replace("Kota ", "").replace("Kabupaten ", "")
        return {
            "titimangsa": f"{kota}, {tgl}",
            "jabatan_kepala": "Mengetahui,\nKepala Sekolah",
            "nama_kepala_sekolah": self.nama_kepala_sekolah,
            "nip_kepala_sekolah": f"NIP. {self.nip_kepala_sekolah}" if self.nip_kepala_sekolah != "-" else "-",
            "jabatan_guru": "Guru Mata Pelajaran",
            "nama_guru": self.nama_guru,
            "nip_guru": f"NIP. {self.nip_guru}" if self.nip_guru != "-" else "-",
        }

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nama_guru": self.nama_guru,
            "nip_guru": self.nip_guru,
            "nama_sekolah": self.nama_sekolah,
            "npsn": self.npsn,
            "kabupaten_kota": self.kabupaten_kota,
            "provinsi": self.provinsi,
            "nama_kepala_sekolah": self.nama_kepala_sekolah,
            "nip_kepala_sekolah": self.nip_kepala_sekolah,
            "no_whatsapp": self.no_whatsapp,
            "email": self.email,
            "ukuran_kertas_default": self.ukuran_kertas_default,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
