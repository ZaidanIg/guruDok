from datetime import date, timedelta
from typing import Dict, Any, List

from app.models.curriculum import CurriculumSubject
from app.schemas.generation import DocumentGenerateRequest


WEEKDAY_NAME_TO_INT: Dict[str, int] = {
    "SENIN": 0,
    "SELASA": 1,
    "RABU": 2,
    "KAMIS": 3,
    "JUMAT": 4,
    "SABTU": 5,
    "MINGGU": 6,
}

INT_TO_WEEKDAY_NAME: Dict[int, str] = {
    0: "Senin",
    1: "Selasa",
    2: "Rabu",
    3: "Kamis",
    4: "Jumat",
    5: "Sabtu",
    6: "Minggu",
}

MONTH_NAMES_ID: Dict[int, str] = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}


class JurnalBlueprintEngine:
    """Deterministic builder for Service 14 (Jurnal Mengajar Harian) scheduled against GuruDocDB chapters & TPs."""

    @staticmethod
    def _parse_start_date(raw_date: str | None, semester: int) -> date:
        if raw_date:
            try:
                parts = [int(p) for p in raw_date.strip().split("-")]
                if len(parts) == 3:
                    return date(parts[0], parts[1], parts[2])
            except Exception:
                pass
        return date(2026, 7, 13) if semester == 1 else date(2027, 1, 4)

    @staticmethod
    def build_blueprint(request: DocumentGenerateRequest, subject: CurriculumSubject) -> Dict[str, Any]:
        ov = request.custom_overrides
        raw_days = (ov.hari_mengajar if (ov and ov.hari_mengajar) else None) or ["Senin", "Kamis"]
        target_weekdays = sorted(
            {
                WEEKDAY_NAME_TO_INT[d.strip().upper()]
                for d in raw_days
                if d and d.strip().upper() in WEEKDAY_NAME_TO_INT
            }
        ) or [0, 3]

        start_dt = JurnalBlueprintEngine._parse_start_date(
            ov.tanggal_mulai_semester if ov else None,
            request.semester,
        )
        jam_mengajar = (ov.jam_mengajar if (ov and ov.jam_mengajar) else None) or "1-2"
        rombel = (ov.nama_rombel if (ov and ov.nama_rombel) else None) or f"Kelas {subject.kelas}"
        total_pertemuan = (
            int(ov.jumlah_pertemuan_jurnal)
            if (ov and ov.jumlah_pertemuan_jurnal is not None)
            else 16
        )

        # Collect semester chapters & TPs sequentially
        all_chapters = list(subject.bab_list or [])
        sem_chapters = [c for c in all_chapters if c.semester == request.semester] or all_chapters

        tp_entries: List[Dict[str, str]] = []
        for bab in sem_chapters:
            tps = list(bab.tujuan_pembelajaran or [])
            if tps:
                for tp in tps:
                    tp_entries.append(
                        {
                            "tp_code": tp.code,
                            "tp_desc": tp.deskripsi,
                            "materi": f"Bab {bab.nomor_bab}: {bab.judul_bab}",
                        }
                    )
            else:
                tp_entries.append(
                    {
                        "tp_code": f"TP.{subject.kelas}.{bab.nomor_bab}.1",
                        "tp_desc": f"Memahami dan menerapkan materi {bab.judul_bab}.",
                        "materi": f"Bab {bab.nomor_bab}: {bab.judul_bab}",
                    }
                )

        if not tp_entries:
            tp_entries = [
                {
                    "tp_code": f"TP.{subject.kelas}.1.1",
                    "tp_desc": f"Menguasai kompetensi inti {subject.nama_mapel}.",
                    "materi": subject.nama_mapel,
                }
            ]

        rows: List[Dict[str, str]] = []
        if ov and ov.custom_jurnal_rows:
            for idx, r_item in enumerate(ov.custom_jurnal_rows, start=1):
                rows.append(
                    {
                        "no": str(idx),
                        "hari_tanggal": r_item.hari_tanggal,
                        "jam_pertemuan": r_item.jam_pertemuan or f"Jam {jam_mengajar} (Pert. {idx})",
                        "tp": r_item.tp or "-",
                        "materi": r_item.materi or "-",
                        "kegiatan": r_item.kegiatan or "-",
                        "kehadiran": r_item.kehadiran or "-",
                        "refleksi": r_item.refleksi or "-",
                        "paraf": r_item.paraf or "",
                    }
                )
        else:
            # Generate scheduled teaching dates matching selected weekdays
            scheduled_dates: List[date] = []
            cursor = start_dt
            guard = 0
            while len(scheduled_dates) < total_pertemuan and guard < 240:
                if cursor.weekday() in target_weekdays:
                    scheduled_dates.append(cursor)
                cursor += timedelta(days=1)
                guard += 1

            for idx, dt in enumerate(scheduled_dates, start=1):
                item = tp_entries[(idx - 1) % len(tp_entries)]
                hari_nama = INT_TO_WEEKDAY_NAME[dt.weekday()]
                tgl_str = f"{hari_nama}, {dt.day:02d} {MONTH_NAMES_ID[dt.month]} {dt.year}"
                rows.append(
                    {
                        "no": str(idx),
                        "hari_tanggal": tgl_str,
                        "jam_pertemuan": f"Jam {jam_mengajar} (Pert. {idx})",
                        "tp": f"{item['tp_code']}: {item['tp_desc']}",
                        "materi": item["materi"],
                        "kegiatan": "Memahami konsep, diskusi eksploratif, aplikasi studi kasus, dan refleksi.",
                        "kehadiran": "Hadir lengkap / .... siswa tidak hadir",
                        "refleksi": "Pembelajaran berjalan kondusif sesuai target TP.",
                        "paraf": "",
                    }
                )

        hari_label = ", ".join(INT_TO_WEEKDAY_NAME[w] for w in target_weekdays)
        return {
            "rombel": rombel,
            "hari_label": hari_label,
            "jam_mengajar": jam_mengajar,
            "tanggal_mulai": f"{start_dt.day:02d} {MONTH_NAMES_ID[start_dt.month]} {start_dt.year}",
            "total_pertemuan": len(rows),
            "rows": rows,
        }
