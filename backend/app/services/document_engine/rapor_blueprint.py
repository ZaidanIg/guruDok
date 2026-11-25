from typing import Dict, Any, List
from app.models.curriculum import CurriculumSubject
from app.schemas.generation import DocumentGenerateRequest


class RaporBlueprintEngine:
    """Deterministic builder for Service 16 (Deskripsi e-Rapor) and Service 17 (Rekap Nilai Rapor)."""

    @staticmethod
    def _clean_phrase(text: str) -> str:
        s = (text or "").strip().rstrip(".")
        if not s:
            return "memahami konsep inti pembelajaran"
        # Lowercase first character unless it looks like an acronym
        if len(s) > 1 and s[0].isupper() and not s[1].isupper():
            s = s[0].lower() + s[1:]
        return s

    @staticmethod
    def build_blueprint(request: DocumentGenerateRequest, subject: CurriculumSubject) -> Dict[str, Any]:
        ov = request.custom_overrides
        rombel = (ov.nama_rombel if (ov and ov.nama_rombel) else None) or f"Kelas {subject.kelas}"
        kktp = int(ov.kktp_nilai) if (ov and ov.kktp_nilai is not None) else 75

        bobot = (ov.bobot_nilai if (ov and isinstance(ov.bobot_nilai, dict)) else None) or {}
        raw_sumatif = bobot.get("sumatif", 60)
        raw_sas = bobot.get("sas", 40)
        try:
            w_sumatif = max(0, min(100, int(raw_sumatif)))
            w_sas = max(0, min(100, int(raw_sas)))
        except (TypeError, ValueError):
            w_sumatif, w_sas = 60, 40
        total_w = w_sumatif + w_sas
        if total_w <= 0:
            w_sumatif, w_sas = 60, 40
        elif total_w != 100:
            w_sumatif = round((w_sumatif / total_w) * 100)
            w_sas = 100 - w_sumatif

        # Collect semester TPs & ringkasan_rapor from GuruDocDB
        all_chapters = list(subject.bab_list or [])
        sem_chapters = [c for c in all_chapters if c.semester == request.semester] or all_chapters
        tp_list: List[Dict[str, str]] = []
        for bab in sem_chapters:
            for tp in (bab.tujuan_pembelajaran or []):
                ringkasan = getattr(tp, "ringkasan_rapor", "") or tp.deskripsi
                tp_list.append(
                    {
                        "code": tp.code,
                        "deskripsi": tp.deskripsi,
                        "ringkasan": RaporBlueprintEngine._clean_phrase(ringkasan),
                    }
                )
        if not tp_list:
            tp_list = [
                {
                    "code": f"{subject.kelas}.1.1",
                    "deskripsi": f"Memahami konsep utama {subject.nama_mapel}",
                    "ringkasan": f"memahami konsep utama {subject.nama_mapel}",
                },
                {
                    "code": f"{subject.kelas}.1.2",
                    "deskripsi": f"Menerapkan {subject.nama_mapel} dalam pemecahan masalah kontekstual",
                    "ringkasan": f"menerapkan {subject.nama_mapel} dalam pemecahan masalah kontekstual",
                },
            ]

        tp_by_code = {t["code"]: t for t in tp_list}

        # Resolve source entries
        raw_entries = list(ov.rapor_entries or []) if (ov and ov.rapor_entries) else []
        rows: List[Dict[str, Any]] = []

        if raw_entries:
            for idx, entry in enumerate(raw_entries, start=1):
                s_score = int(entry.nilai_sumatif if entry.nilai_sumatif is not None else 82)
                sas_score = int(entry.nilai_sas if entry.nilai_sas is not None else 80)
                na = round((s_score * w_sumatif + sas_score * w_sas) / 100.0)
                tp_hi = tp_by_code.get(entry.tp_tertinggi_code or "") or tp_list[0]
                tp_lo = tp_by_code.get(entry.tp_terendah_code or "") or tp_list[-1]
                catatan = (entry.catatan_deskriptif or "").strip()
                desc_hi = f"Menunjukkan penguasaan yang sangat baik dalam {tp_hi['ringkasan']}."
                desc_lo = f"Perlu bimbingan dan pendampingan lebih lanjut dalam {tp_lo['ringkasan']}."
                full_desc = catatan if catatan else f"{desc_hi} {desc_lo}"
                rows.append(
                    {
                        "no": entry.nomor_absen or idx,
                        "nisn": entry.nisn or "-",
                        "nama": entry.nama_lengkap,
                        "sumatif": s_score,
                        "sas": sas_score,
                        "nilai_akhir": na,
                        "status": "TUNTAS" if na >= kktp else "BELUM TUNTAS",
                        "tp_tertinggi_code": tp_hi["code"],
                        "tp_tertinggi_ringkasan": tp_hi["ringkasan"],
                        "tp_terendah_code": tp_lo["code"],
                        "tp_terendah_ringkasan": tp_lo["ringkasan"],
                        "deskripsi_tinggi": desc_hi,
                        "deskripsi_bimbingan": desc_lo,
                        "deskripsi_lengkap": full_desc,
                    }
                )
        else:
            students = list(ov.students or []) if (ov and ov.students) else []
            if students:
                source_students = [
                    (
                        getattr(st, "nomor_absen", None) or idx,
                        getattr(st, "nisn", "-") or "-",
                        getattr(st, "nama_lengkap", f"Peserta Didik {idx}"),
                    )
                    for idx, st in enumerate(students, start=1)
                ]
            else:
                source_students = [
                    (i, f"2026{i:04d}", f"Peserta Didik {i}")
                    for i in range(1, 11)
                ]

            for idx, (no, nisn, nama) in enumerate(source_students):
                s_score = 86 if idx % 3 != 2 else 74
                sas_score = 84 if idx % 3 != 2 else 72
                na = round((s_score * w_sumatif + sas_score * w_sas) / 100.0)
                tp_hi = tp_list[idx % len(tp_list)]
                tp_lo = tp_list[(idx + len(tp_list) - 1) % len(tp_list)]
                desc_hi = f"Menunjukkan penguasaan yang sangat baik dalam {tp_hi['ringkasan']}."
                desc_lo = f"Perlu bimbingan dan pendampingan lebih lanjut dalam {tp_lo['ringkasan']}."
                rows.append(
                    {
                        "no": no,
                        "nisn": nisn,
                        "nama": nama,
                        "sumatif": s_score,
                        "sas": sas_score,
                        "nilai_akhir": na,
                        "status": "TUNTAS" if na >= kktp else "BELUM TUNTAS",
                        "tp_tertinggi_code": tp_hi["code"],
                        "tp_tertinggi_ringkasan": tp_hi["ringkasan"],
                        "tp_terendah_code": tp_lo["code"],
                        "tp_terendah_ringkasan": tp_lo["ringkasan"],
                        "deskripsi_tinggi": desc_hi,
                        "deskripsi_bimbingan": desc_lo,
                        "deskripsi_lengkap": f"{desc_hi} {desc_lo}",
                    }
                )

        # Compute deterministic competition ranking (RANK)
        sorted_scores = sorted([r["nilai_akhir"] for r in rows], reverse=True)
        for r in rows:
            r["peringkat"] = sorted_scores.index(r["nilai_akhir"]) + 1

        return {
            "rombel": rombel,
            "kktp": kktp,
            "bobot_sumatif": w_sumatif,
            "bobot_sas": w_sas,
            "tp_options": tp_list,
            "rows": rows,
        }
