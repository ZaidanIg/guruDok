from typing import List, Optional
from app.core.exceptions import CurriculumNotFoundError
from app.models.curriculum import CurriculumSubject, ChapterTopic
from app.repositories.base import ICurriculumRepository
from app.schemas.curriculum import SubjectResponse, ChapterResponse, LearningObjectiveResponse, ChapterCreateRequest


class CurriculumService:
    """Service handling curriculum business logic and cascading queries."""

    def __init__(self, repo: ICurriculumRepository):
        self.repo = repo

    def _map_chapter(self, ch: ChapterTopic) -> ChapterResponse:
        return ChapterResponse(
            id=ch.id,
            semester=ch.semester,
            nomor_bab=ch.nomor_bab,
            judul_bab=ch.judul_bab,
            alokasi_jp=ch.alokasi_jp,
            elemen_cp=getattr(ch, "elemen_cp", ""),
            estimasi_pertemuan=getattr(ch, "estimasi_pertemuan", 3),
            rentang_minggu_promes=getattr(ch, "rentang_minggu_promes", ""),
            dimensi_profil_lulusan=ch.dimensi_profil_lulusan,
            model_pembelajaran_default=ch.model_pembelajaran_default,
            modul_ajar_template=getattr(ch, "modul_ajar_template", {}) or {},
            tujuan_pembelajaran=[
                LearningObjectiveResponse(
                    code=tp.code,
                    deskripsi=tp.deskripsi,
                    alokasi_jp=tp.alokasi_jp,
                    urutan_atp=getattr(tp, "urutan_atp", 1),
                    ringkasan_rapor=getattr(tp, "ringkasan_rapor", ""),
                    level_kognitif_bloom=getattr(tp, "level_kognitif_bloom", "C3 - Menerapkan"),
                )
                for tp in ch.tujuan_pembelajaran
            ],
        )

    def _map_subject(self, s: CurriculumSubject, include_babs: bool = False) -> SubjectResponse:
        return SubjectResponse(
            id=s.id,
            id_mapel_bskap=getattr(s, "id_mapel_bskap", "MAPEL-01"),
            jenjang=s.jenjang,
            kelas=s.kelas,
            fase=s.fase,
            nama_mapel=s.nama_mapel,
            alokasi_jp_mingguan=s.alokasi_jp_mingguan,
            total_alokasi_jp_tahun=s.total_alokasi_jp_tahun,
            durasi_1_jp_menit=getattr(s, "durasi_1_jp_menit", 40),
            buku_rujukan_sibi=getattr(s, "buku_rujukan_sibi", ""),
            rasional_bskap=getattr(s, "rasional_bskap", ""),
            tujuan_bskap=getattr(s, "tujuan_bskap", ""),
            karakteristik_bskap=getattr(s, "karakteristik_bskap", ""),
            elemen_cp_resmi=getattr(s, "elemen_cp_resmi", []),
            verification_status=getattr(s, "verification_status", "DRAFT"),
            verification_score=getattr(s, "verification_score", 0),
            bab_count=len(s.bab_list),
            bab_list=[self._map_chapter(ch) for ch in s.bab_list] if include_babs else None,
        )

    def get_subjects(self, jenjang: Optional[str] = None, kelas: Optional[int] = None) -> List[SubjectResponse]:
        subjects = self.repo.get_subjects(jenjang=jenjang, kelas=kelas)
        return [self._map_subject(s, include_babs=False) for s in subjects]

    def get_subject_detail(self, subject_id: str) -> SubjectResponse:
        s = self.repo.get_subject_by_id(subject_id)
        if not s:
            raise CurriculumNotFoundError(f"Subject '{subject_id}' not found.")
        return self._map_subject(s, include_babs=True)

    def get_chapters(self, subject_id: str, semester: Optional[int] = None) -> List[ChapterResponse]:
        s = self.repo.get_subject_by_id(subject_id)
        if not s:
            raise CurriculumNotFoundError(f"Subject '{subject_id}' not found.")

        chapters = s.get_chapters_by_semester(semester) if semester else s.bab_list
        return [self._map_chapter(ch) for ch in chapters]

    def get_profil_lulusan(self) -> List[str]:
        return self.repo.get_profil_lulusan_dimensions()

    def create_custom_chapter(self, subject_id: str, data: ChapterCreateRequest) -> ChapterResponse:
        s = self.repo.get_subject_by_id(subject_id)
        if not s:
            raise CurriculumNotFoundError(f"Subject '{subject_id}' not found.")

        chapter_id = f"{subject_id}-B{data.nomor_bab:02d}-CUSTOM"

        tps_list = []
        if data.daftar_tp and len(data.daftar_tp) > 0:
            for idx, tp in enumerate(data.daftar_tp):
                tps_list.append({
                    "code": tp.code,
                    "deskripsi": tp.deskripsi,
                    "alokasi_jp": tp.alokasi_jp,
                    "deskripsi_tp": tp.deskripsi,
                })
        else:
            tps_list = [
                {
                    "code": f"TP.{s.kelas}.{data.nomor_bab}.1",
                    "deskripsi": f"Memahami dan menganalisis konsep {data.judul_bab}.",
                    "alokasi_jp": max(2, data.alokasi_jp // 2),
                    "deskripsi_tp": f"Memahami dan menganalisis konsep {data.judul_bab}.",
                },
                {
                    "code": f"TP.{s.kelas}.{data.nomor_bab}.2",
                    "deskripsi": f"Menerapkan dan mengevaluasi pemecahan masalah kontekstual terkait {data.judul_bab}.",
                    "alokasi_jp": max(2, data.alokasi_jp - max(2, data.alokasi_jp // 2)),
                    "deskripsi_tp": f"Menerapkan dan mengevaluasi pemecahan masalah kontekstual terkait {data.judul_bab}.",
                },
            ]

        from app.services.dataset_seeder import _build_rich_modul_ajar_payload
        model_code = "PBL" if "Problem" in (data.model_pembelajaran or "") else "INQUIRY"
        rich_payload = _build_rich_modul_ajar_payload(
            nama_mapel=s.nama_mapel,
            jenjang=s.jenjang,
            kelas=s.kelas,
            fase=s.fase,
            nomor_bab=data.nomor_bab,
            judul_bab=data.judul_bab,
            elemen_cp=data.elemen_cp,
            deskripsi_cp=f"Peserta didik mampu menguasai materi {data.judul_bab} pada elemen {data.elemen_cp}.",
            model_code=model_code,
            dpl_codes=["DPL-3", "DPL-5", "DPL-6"],
            tps_list=tps_list,
        )

        ch = self.repo.add_custom_chapter(
            course_id=subject_id,
            chapter_id=chapter_id,
            nomor_bab=data.nomor_bab,
            semester=data.semester,
            judul_bab=data.judul_bab,
            elemen_cp=data.elemen_cp,
            alokasi_jp=data.alokasi_jp,
            model_pembelajaran=data.model_pembelajaran or "Inquiry Based Learning (Mendalam/DL)",
            modul_ajar_payload=rich_payload,
            tps=tps_list,
        )
        return self._map_chapter(ch)
