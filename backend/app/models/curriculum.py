from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class LearningObjective:
    """Domain model representing a single Tujuan Pembelajaran (TP)."""
    code: str
    deskripsi: str
    alokasi_jp: int = 2
    urutan_atp: int = 1
    ringkasan_rapor: str = ""
    level_kognitif_bloom: str = "C3 - Menerapkan"

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "deskripsi": self.deskripsi,
            "alokasi_jp": self.alokasi_jp,
            "urutan_atp": self.urutan_atp,
            "ringkasan_rapor": self.ringkasan_rapor,
            "level_kognitif_bloom": self.level_kognitif_bloom,
        }


@dataclass
class ChapterTopic:
    """Domain model representing a Bab / Lingkup Materi Pokok."""
    id: str
    semester: int
    nomor_bab: int
    judul_bab: str
    alokasi_jp: int
    tujuan_pembelajaran: List[LearningObjective] = field(default_factory=list)
    dimensi_profil_lulusan: List[str] = field(default_factory=list)
    model_pembelajaran_default: str = "Inquiry Based Learning"
    elemen_cp: str = "Pemahaman Konsep & Keterampilan Proses"
    estimasi_pertemuan: int = 3
    rentang_minggu_promes: str = ""
    modul_ajar_template: Dict[str, Any] = field(default_factory=dict)

    def calculate_total_jp(self) -> int:
        if self.tujuan_pembelajaran:
            sum_tp = sum(tp.alokasi_jp for tp in self.tujuan_pembelajaran)
            if sum_tp > 0:
                return sum_tp
        return self.alokasi_jp

    def get_tp_codes(self) -> List[str]:
        return [tp.code for tp in self.tujuan_pembelajaran]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "semester": self.semester,
            "nomor_bab": self.nomor_bab,
            "judul_bab": self.judul_bab,
            "alokasi_jp": self.calculate_total_jp(),
            "elemen_cp": self.elemen_cp,
            "estimasi_pertemuan": self.estimasi_pertemuan,
            "rentang_minggu_promes": self.rentang_minggu_promes,
            "tujuan_pembelajaran": [tp.to_dict() for tp in self.tujuan_pembelajaran],
            "dimensi_profil_lulusan": self.dimensi_profil_lulusan,
            "model_pembelajaran_default": self.model_pembelajaran_default,
            "modul_ajar_template": self.modul_ajar_template,
        }


@dataclass
class CurriculumSubject:
    """Domain model representing a complete subject for a specific grade & phase."""
    id: str
    jenjang: str  # SD, SMP, SMA
    kelas: int    # 1 to 12
    fase: str     # Fase A, B, C, D, E, F
    nama_mapel: str
    alokasi_jp_mingguan: int
    total_alokasi_jp_tahun: int
    bab_list: List[ChapterTopic] = field(default_factory=list)
    id_mapel_bskap: str = "MAPEL-01"
    durasi_1_jp_menit: int = 40
    buku_rujukan_sibi: str = ""
    rasional_bskap: str = ""
    tujuan_bskap: str = ""
    karakteristik_bskap: str = ""
    elemen_cp_resmi: List[Dict[str, str]] = field(default_factory=list)
    verification_status: str = "DRAFT"
    verification_score: int = 0

    def get_chapter(self, chapter_id: str) -> Optional[ChapterTopic]:
        for ch in self.bab_list:
            if ch.id == chapter_id:
                return ch
        # Flexible matching by suffix or alias (e.g. "IPA-K7-B01" vs "SMP-K7-IPA-B01")
        if "-B" in chapter_id:
            suffix = chapter_id.split("-B")[-1]
            for ch in self.bab_list:
                if ch.id.endswith(f"-B{suffix}"):
                    return ch
                if suffix.isdigit() and ch.id.endswith(f"-B{int(suffix):02d}"):
                    return ch
        return None

    def get_chapters_by_semester(self, semester: int) -> List[ChapterTopic]:
        return [ch for ch in self.bab_list if ch.semester == semester]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_mapel_bskap": self.id_mapel_bskap,
            "jenjang": self.jenjang,
            "kelas": self.kelas,
            "fase": self.fase,
            "nama_mapel": self.nama_mapel,
            "alokasi_jp_mingguan": self.alokasi_jp_mingguan,
            "total_alokasi_jp_tahun": self.total_alokasi_jp_tahun,
            "durasi_1_jp_menit": self.durasi_1_jp_menit,
            "buku_rujukan_sibi": self.buku_rujukan_sibi,
            "rasional_bskap": self.rasional_bskap,
            "tujuan_bskap": self.tujuan_bskap,
            "karakteristik_bskap": self.karakteristik_bskap,
            "elemen_cp_resmi": self.elemen_cp_resmi,
            "verification_status": self.verification_status,
            "verification_score": self.verification_score,
            "bab_count": len(self.bab_list),
            "bab_list": [ch.to_dict() for ch in self.bab_list],
        }
