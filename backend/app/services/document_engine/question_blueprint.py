import random
from typing import Any, Dict, List, Optional
from app.models.curriculum import CurriculumSubject, ChapterTopic
from app.schemas.generation import DocumentGenerateRequest, ServiceIdEnum


class QuestionBlueprintEngine:
    """Deterministic blueprint engine for Service 10 (Kuis), 11 (Sumatif Bab), and 12 (STS/SAS).

    Produces:
    - Structured questions (PG & Uraian) with optional stimulus
    - Deterministic Paket A / B shuffle
    - 7-column Kisi-Kisi table
    - Kartu Soal cards (for S12)
    - Pedoman Penskoran (auto-normalized to Skor Maks 100)
    """

    LEVEL_LABELS = {
        "C1-C2": "Level 1 (Mudah / C1-C2)",
        "C3": "Level 2 (Sedang / C3)",
        "C4-C6": "Level 3 (HOTS / C4-C6)",
    }

    OPTION_LETTERS = ["A", "B", "C", "D", "E"]

    @classmethod
    def _default_option_count(cls, jenjang: str) -> int:
        return 5 if str(jenjang).upper() == "SMA" else 4

    @classmethod
    def _resolve_target_chapters(
        cls,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        request: DocumentGenerateRequest,
    ) -> List[ChapterTopic]:
        overrides = request.custom_overrides
        if overrides and overrides.cakupan_bab_ids:
            wanted = set(overrides.cakupan_bab_ids)
            matched = [c for c in subject.bab_list if c.id in wanted or str(c.nomor_bab) in wanted]
            if matched:
                return matched
        if chapter and request.service_id != ServiceIdEnum.STS_SAS:
            return [chapter]
        sem_chapters = [c for c in subject.bab_list if c.semester == request.semester]
        return sem_chapters or subject.bab_list[:3] or ([chapter] if chapter else [])

    @classmethod
    def _build_default_questions(
        cls,
        subject: CurriculumSubject,
        chapters: List[ChapterTopic],
        request: DocumentGenerateRequest,
    ) -> List[Dict[str, Any]]:
        overrides = request.custom_overrides
        opt_count = cls._default_option_count(
            request.jenjang.value if hasattr(request.jenjang, "value") else str(request.jenjang)
        )
        if request.service_id == ServiceIdEnum.KUIS:
            pg_target = overrides.jumlah_soal_pg if (overrides and overrides.jumlah_soal_pg is not None) else 5
            uraian_target = (
                0
                if (overrides and str(overrides.tipe_soal_kuis).upper() == "PG")
                else (overrides.jumlah_soal_uraian if (overrides and overrides.jumlah_soal_uraian is not None) else 2)
            )
        elif request.service_id == ServiceIdEnum.SUMATIF_BAB:
            pg_target = overrides.jumlah_soal_pg if (overrides and overrides.jumlah_soal_pg is not None) else 5
            uraian_target = overrides.jumlah_soal_uraian if (overrides and overrides.jumlah_soal_uraian is not None) else 2
        else:
            pg_target = overrides.jumlah_soal_pg if (overrides and overrides.jumlah_soal_pg is not None) else 6
            uraian_target = overrides.jumlah_soal_uraian if (overrides and overrides.jumlah_soal_uraian is not None) else 2

        all_tps = []
        for ch in chapters:
            for tp in ch.tujuan_pembelajaran:
                all_tps.append((ch, tp))
        if not all_tps and chapters:
            all_tps = [(chapters[0], None)]

        levels = ["C1-C2", "C3", "C4-C6"]
        questions: List[Dict[str, Any]] = []

        for idx in range(pg_target):
            ch, tp = all_tps[idx % len(all_tps)] if all_tps else (None, None)
            tp_code = tp.code if tp else f"TP.{subject.kelas}.1.{idx + 1}"
            tp_desc = tp.deskripsi if tp else (ch.judul_bab if ch else subject.nama_mapel)
            materi = ch.judul_bab if ch else subject.nama_mapel
            lvl = levels[idx % len(levels)]
            questions.append(
                {
                    "no": idx + 1,
                    "tipe_soal": "PG",
                    "tp_code": tp_code,
                    "materi": materi,
                    "indikator": f"Peserta didik mampu menyelesaikan persoalan terkait {tp_desc[:90]}",
                    "level_kognitif": lvl,
                    "stimulus": "",
                    "pertanyaan": f"Berdasarkan materi {materi}, manakah pernyataan yang paling tepat mengenai {tp_desc[:110]}?",
                    "opsi": [f"Konsep utama {materi} sesuai indikator {tp_code} (Opsi {cls.OPTION_LETTERS[o]})" for o in range(opt_count)],
                    "kunci_jawaban": "A",
                    "bobot_skor": 0,
                    "pembahasan": f"Mengacu pada tujuan pembelajaran {tp_code}: {tp_desc}.",
                }
            )

        for idx in range(uraian_target):
            ch, tp = all_tps[idx % len(all_tps)] if all_tps else (None, None)
            tp_code = tp.code if tp else f"TP.{subject.kelas}.1.{idx + 1}"
            tp_desc = tp.deskripsi if tp else (ch.judul_bab if ch else subject.nama_mapel)
            materi = ch.judul_bab if ch else subject.nama_mapel
            questions.append(
                {
                    "no": pg_target + idx + 1,
                    "tipe_soal": "URAIAN",
                    "tp_code": tp_code,
                    "materi": materi,
                    "indikator": f"Peserta didik mampu menganalisis dan menguraikan {tp_desc[:90]}",
                    "level_kognitif": "C4-C6",
                    "stimulus": "",
                    "pertanyaan": f"Jelaskan dan berikan contoh penerapan nyata dari {materi} ({tp_desc[:100]})!",
                    "opsi": [],
                    "kunci_jawaban": f"Penjelasan runtut mencakup konsep inti {materi} dan contoh kontekstual yang relevan.",
                    "bobot_skor": 0,
                    "pembahasan": f"Dinilai berdasarkan ketepatan konsep, kelengkapan argumen, dan contoh penerapan ({tp_code}).",
                }
            )
        return questions

    @classmethod
    def _normalize_scores(cls, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not questions:
            return questions
        explicit_sum = sum(int(q.get("bobot_skor") or 0) for q in questions)
        if explicit_sum == 100:
            return questions

        # Auto-distribute to exact 100
        pg_qs = [q for q in questions if q["tipe_soal"] == "PG"]
        ur_qs = [q for q in questions if q["tipe_soal"] == "URAIAN"]
        if pg_qs and ur_qs:
            pg_pool, ur_pool = 70, 30
        elif pg_qs:
            pg_pool, ur_pool = 100, 0
        else:
            pg_pool, ur_pool = 0, 100

        if pg_qs:
            base_pg = pg_pool // len(pg_qs)
            rem_pg = pg_pool % len(pg_qs)
            for i, q in enumerate(pg_qs):
                q["bobot_skor"] = base_pg + (1 if i < rem_pg else 0)
        if ur_qs:
            base_ur = ur_pool // len(ur_qs)
            rem_ur = ur_pool % len(ur_qs)
            for i, q in enumerate(ur_qs):
                q["bobot_skor"] = base_ur + (1 if i < rem_ur else 0)
        return questions

    @classmethod
    def build_blueprint(
        cls,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic] = None,
    ) -> Dict[str, Any]:
        overrides = request.custom_overrides
        chapters = cls._resolve_target_chapters(subject, chapter, request)
        tp_map = {
            tp.code: (ch.judul_bab, tp.deskripsi)
            for ch in subject.bab_list
            for tp in ch.tujuan_pembelajaran
        }

        if overrides and overrides.butir_soal_kustom:
            questions: List[Dict[str, Any]] = []
            for idx, item in enumerate(overrides.butir_soal_kustom, start=1):
                tp_code = item.tp_code or (chapters[0].tujuan_pembelajaran[0].code if chapters and chapters[0].tujuan_pembelajaran else f"TP.{subject.kelas}.1.{idx}")
                materi_default = chapters[0].judul_bab if chapters else subject.nama_mapel
                materi, tp_desc = tp_map.get(tp_code, (materi_default, materi_default))
                lvl = item.level_kognitif or "C1-C2"
                questions.append(
                    {
                        "no": idx,
                        "tipe_soal": item.tipe_soal,
                        "tp_code": tp_code,
                        "materi": materi,
                        "indikator": f"Peserta didik mampu menguasai {tp_desc[:90]}",
                        "level_kognitif": lvl,
                        "stimulus": item.stimulus or "",
                        "pertanyaan": item.pertanyaan,
                        "opsi": list(item.opsi or []),
                        "kunci_jawaban": item.kunci_jawaban or ("A" if item.tipe_soal == "PG" else ""),
                        "bobot_skor": int(item.bobot_skor or 0),
                        "pembahasan": item.pembahasan or "",
                    }
                )
        else:
            questions = cls._build_default_questions(subject, chapters, request)

        paket = (overrides.paket_soal if overrides and overrides.paket_soal else "A").upper()
        pg_part = [q for q in questions if q["tipe_soal"] == "PG"]
        ur_part = [q for q in questions if q["tipe_soal"] != "PG"]

        if paket == "B" and len(questions) > 1:
            rng = random.Random(f"{subject.id}:{request.semester}:B")
            rng.shuffle(pg_part)
            rng.shuffle(ur_part)

        for idx, q in enumerate(pg_part, start=1):
            q["bagian"] = "A"
            q["section_no"] = idx
        for idx, q in enumerate(ur_part, start=1):
            q["bagian"] = "B"
            q["section_no"] = idx

        questions = pg_part + ur_part
        for idx, q in enumerate(questions, start=1):
            q["no"] = idx

        questions = cls._normalize_scores(questions)
        total_skor = sum(int(q.get("bobot_skor") or 0) for q in questions)

        kisi_kisi = [
            {
                "no": q["no"],
                "tp_code": q["tp_code"],
                "materi": q["materi"],
                "indikator": q["indikator"],
                "level_kognitif": q["level_kognitif"],
                "bentuk_soal": "Pilihan Ganda" if q["tipe_soal"] == "PG" else "Essai",
                "nomor_soal": f"{q['bagian']}.{q['section_no']}",
            }
            for q in questions
        ]

        jenis_ujian = (overrides.jenis_ujian if overrides and overrides.jenis_ujian else "STS").upper()
        alokasi_waktu = (
            int(overrides.alokasi_waktu_menit)
            if (overrides and overrides.alokasi_waktu_menit is not None)
            else 90
        )

        return {
            "service_id": request.service_id.value,
            "jenis_ujian": jenis_ujian,
            "paket_soal": paket,
            "alokasi_waktu_menit": alokasi_waktu,
            "chapters": chapters,
            "questions": questions,
            "pg_questions": pg_part,
            "essai_questions": ur_part,
            "kisi_kisi": kisi_kisi,
            "pg_count": len(pg_part),
            "uraian_count": len(ur_part),
            "total_skor_maksimal": total_skor or 100,
        }
