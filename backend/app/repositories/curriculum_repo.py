import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.core.exceptions import CurriculumNotFoundError
from app.models.curriculum import CurriculumSubject, ChapterTopic, LearningObjective
from app.repositories.base import ICurriculumRepository


class JsonCurriculumRepository(ICurriculumRepository):
    """Concrete repository that loads and indexes master curriculum data from official Kemendikdasmen datasets."""

    def __init__(self, dataset_path: Optional[Path] = None):
        self.dataset_dir = dataset_path or settings.dataset_path
        self._subjects_by_id: Dict[str, CurriculumSubject] = {}
        self._subjects_by_level: Dict[str, List[CurriculumSubject]] = {"SD": [], "SMP": [], "SMA": []}
        self._subjects_by_grade: Dict[int, List[CurriculumSubject]] = {g: [] for g in range(1, 13)}
        self._raw_modul_templates: Dict[str, dict] = {} # Key: f"{subject_id}_{chapter_id}"
        self._profil_lulusan: List[str] = []
        self._load_all_datasets()

    def _load_all_datasets(self) -> None:
        """Parses JSON files and builds fast in-memory indexes."""
        # 1. Load Dimensi Profil Lulusan
        regulasi_file = self.dataset_dir / "01_regulasi_dan_dimensi_lulusan.json"
        if regulasi_file.exists():
            with open(regulasi_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                dpl = data.get("delapan_dimensi_profil_lulusan", [])
                if not dpl:
                    dpl = data.get("dimensi_profil_lulusan_permendikdasmen_10_2025", {}).get("8_dimensi_resmi", [])
                self._profil_lulusan = [d["nama_dimensi"] for d in dpl] if dpl else []

        # 2. Load Bab, TP, ATP, and Modul Ajar from dataset 04
        dataset_04 = self.dataset_dir / "04_master_bab_tp_atp_modul_ajar.json"
        if dataset_04.exists():
            with open(dataset_04, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            # Combine complete modules and additional syllabus catalogs
            all_subjects_raw = raw_data.get("paket_lengkap_modul_ajar_per_bab", []) + raw_data.get("katalog_silabus_bab_tambahan", [])

            for item in all_subjects_raw:
                subj_id = item["id_kurikulum"]
                jenjang = item["jenjang"]
                kelas = int(item["kelas"])
                fase = item["fase"]
                nama_mapel = item["mata_pelajaran"]
                alokasi_jp_mingguan = int(item.get("jp_per_minggu", 3))
                total_alokasi_jp = int(item.get("total_jp_intrakurikuler_tahun", 108))

                # Parse chapters
                chapter_models: List[ChapterTopic] = []
                for b in item.get("daftar_bab", []):
                    ch_id = b["id_bab"]
                    nomor_bab = int(b.get("nomor_bab", 1))
                    semester = int(b.get("semester", 1))
                    judul_bab = b["judul_bab"]
                    alokasi_jp_bab = int(b.get("alokasi_jp_bab", 10))

                    # Parse learning objectives
                    tps: List[LearningObjective] = []
                    for tp_data in b.get("daftar_tp", []):
                        tps.append(
                            LearningObjective(
                                code=tp_data.get("kode_tp", f"TP.{kelas}.{nomor_bab}.1"),
                                deskripsi=tp_data.get("deskripsi_tp", ""),
                                alokasi_jp=int(tp_data.get("alokasi_jp", 2)),
                            )
                        )

                    # Extract dimensions
                    dimensi = b.get("dimensi_profil_lulusan_fokus", [])
                    if not dimensi:
                        dimensi = ["Penalaran Kritis", "Mandiri", "Kolaboratif"]

                    model_pedagogis = b.get("model_pembelajaran_pedagogis", "Inquiry Based Learning (Mendalam/DL)")

                    chapter_model = ChapterTopic(
                        id=ch_id,
                        semester=semester,
                        nomor_bab=nomor_bab,
                        judul_bab=judul_bab,
                        alokasi_jp=alokasi_jp_bab,
                        tujuan_pembelajaran=tps,
                        dimensi_profil_lulusan=dimensi,
                        model_pembelajaran_default=model_pedagogis,
                    )
                    chapter_models.append(chapter_model)

                    # Cache raw modul ajar template if available
                    if "modul_ajar_template" in b:
                        key = f"{subj_id}:{ch_id}"
                        self._raw_modul_templates[key] = b["modul_ajar_template"]

                subject = CurriculumSubject(
                    id=subj_id,
                    jenjang=jenjang,
                    kelas=kelas,
                    fase=fase,
                    nama_mapel=nama_mapel,
                    alokasi_jp_mingguan=alokasi_jp_mingguan,
                    total_alokasi_jp_tahun=total_alokasi_jp,
                    bab_list=chapter_models,
                )

                # Indexing
                self._subjects_by_id[subj_id] = subject
                if jenjang in self._subjects_by_level:
                    self._subjects_by_level[jenjang].append(subject)
                if kelas in self._subjects_by_grade:
                    self._subjects_by_grade[kelas].append(subject)

    def get_subjects(self, jenjang: Optional[str] = None, kelas: Optional[int] = None) -> List[CurriculumSubject]:
        """Returns subjects filtered by level and/or grade."""
        if jenjang and jenjang.upper() in self._subjects_by_level:
            results = self._subjects_by_level[jenjang.upper()]
        else:
            results = list(self._subjects_by_id.values())

        if kelas is not None:
            results = [s for s in results if s.kelas == kelas]

        return results

    def get_subject_by_id(self, subject_id: str) -> Optional[CurriculumSubject]:
        """Returns subject by id or None."""
        return self._subjects_by_id.get(subject_id)

    def get_chapter(self, subject_id: str, chapter_id: str) -> Optional[ChapterTopic]:
        """Returns a specific chapter for a subject."""
        subj = self.get_subject_by_id(subject_id)
        if not subj:
            return None
        return subj.get_chapter(chapter_id)

    def get_raw_modul_template(self, subject_id: str, chapter_id: str) -> Optional[dict]:
        """Returns the pre-engineered rich modul ajar content template."""
        key = f"{subject_id}:{chapter_id}"
        return self._raw_modul_templates.get(key)

    def get_profil_lulusan_dimensions(self) -> List[str]:
        """Returns list of 8 DPL."""
        return self._profil_lulusan or [
            "Keimanan dan Ketakwaan kepada Tuhan YME",
            "Kewargaan",
            "Penalaran Kritis",
            "Kreativitas",
            "Kolaborasi",
            "Kemandirian",
            "Kesehatan Raga dan Jiwa",
            "Komunikasi",
        ]

    def add_custom_chapter(
        self,
        course_id: str,
        chapter_id: str,
        nomor_bab: int,
        semester: int,
        judul_bab: str,
        elemen_cp: str,
        alokasi_jp: int,
        model_pembelajaran: str,
        modul_ajar_payload: Dict[str, Any],
        tps: List[Dict[str, Any]],
    ) -> ChapterTopic:
        subj = self.get_subject_by_id(course_id)
        if not subj:
            raise ValueError(f"Course '{course_id}' not found.")

        learning_objectives = [
            LearningObjective(
                code=t.get("code") or f"TP.{subj.kelas}.{nomor_bab}.{i+1}",
                deskripsi=t.get("deskripsi") or f"Tujuan pembelajaran {judul_bab}",
                alokasi_jp=int(t.get("alokasi_jp") or 4),
            )
            for i, t in enumerate(tps)
        ]

        ch = ChapterTopic(
            id=chapter_id,
            semester=semester,
            nomor_bab=nomor_bab,
            judul_bab=judul_bab,
            alokasi_jp=alokasi_jp,
            tujuan_pembelajaran=learning_objectives,
            dimensi_profil_lulusan=["Penalaran Kritis", "Kemandirian", "Kolaborasi"],
            model_pembelajaran_default=model_pembelajaran,
            elemen_cp=elemen_cp,
            estimasi_pertemuan=max(1, alokasi_jp // max(1, subj.alokasi_jp_mingguan)),
            rentang_minggu_promes=f"Minggu Efektif Semester {semester}",
            modul_ajar_template=modul_ajar_payload,
        )

        subj.bab_list.append(ch)
        return ch
