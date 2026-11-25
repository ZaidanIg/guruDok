from typing import Any, Dict, List, Optional

from app.models.curriculum import ChapterTopic, CurriculumSubject
from app.models.teacher import TeacherProfile
from app.schemas.generation import DocumentGenerateRequest


DEFAULT_DAYS_PIKET = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]

DEFAULT_KESEPAKATAN_KELAS = [
    "Hadir tepat waktu dan siap mengikuti pembelajaran sebelum bel masuk berbunyi.",
    "Saling menghormati guru dan sesama teman dengan bertutur kata santun.",
    "Menjaga kebersihan, kerapian, dan ketertiban ruang kelas serta melaksanakan tugas piket.",
    "Berpartisipasi aktif dalam diskusi, kerja kelompok, dan menyelesaikan tugas dengan jujur.",
    "Menggunakan gawai dan fasilitas kelas secara bijak hanya untuk mendukung kegiatan belajar.",
]


def _resolve_rombel_label(request: DocumentGenerateRequest) -> str:
    ov = request.custom_overrides
    if ov and ov.nama_rombel and ov.nama_rombel.strip():
        return ov.nama_rombel.strip()
    return f"Kelas {request.kelas}"


def _resolve_students(request: DocumentGenerateRequest) -> List[Dict[str, str]]:
    ov = request.custom_overrides
    if ov and ov.students:
        return [
            {
                "absen": str(s.nomor_absen or idx),
                "nisn": str(s.nisn or "-"),
                "nama": s.nama_lengkap,
            }
            for idx, s in enumerate(ov.students, start=1)
        ]
    return [
        {"absen": str(i), "nisn": "-", "nama": f"Peserta Didik {i:02d}"}
        for i in range(1, 16)
    ]


class AdminKelasBlueprint:
    """Shared deterministic blueprint for Service 02 (Template Administrasi Kelas)."""

    @staticmethod
    def build_blueprint(
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        teacher: TeacherProfile,
    ) -> Dict[str, Any]:
        ov = request.custom_overrides
        rombel = _resolve_rombel_label(request)
        students = _resolve_students(request)
        names = [s["nama"] for s in students]

        wali_kelas = (
            ov.wali_kelas.strip()
            if ov and ov.wali_kelas and ov.wali_kelas.strip()
            else teacher.nama_guru
        )
        ketua = (
            ov.ketua_kelas.strip()
            if ov and ov.ketua_kelas and ov.ketua_kelas.strip()
            else (names[0] if len(names) > 0 else "...................................")
        )
        wakil = (
            ov.wakil_ketua_kelas.strip()
            if ov and ov.wakil_ketua_kelas and ov.wakil_ketua_kelas.strip()
            else (names[1] if len(names) > 1 else "...................................")
        )
        sekretaris = (
            ov.sekretaris_kelas.strip()
            if ov and ov.sekretaris_kelas and ov.sekretaris_kelas.strip()
            else (names[2] if len(names) > 2 else "...................................")
        )
        bendahara = (
            ov.bendahara_kelas.strip()
            if ov and ov.bendahara_kelas and ov.bendahara_kelas.strip()
            else (names[3] if len(names) > 3 else "...................................")
        )

        piket_rows: List[Dict[str, str]] = []
        custom_piket = ov.jadwal_piket if ov and isinstance(ov.jadwal_piket, dict) else {}
        for day_idx, day in enumerate(DEFAULT_DAYS_PIKET):
            day_names = custom_piket.get(day)
            if isinstance(day_names, list) and len(day_names) > 0:
                petugas_list = [str(n) for n in day_names]
            else:
                petugas_list = [
                    names[i]
                    for i in range(day_idx, len(names), len(DEFAULT_DAYS_PIKET))
                ][:4]
            piket_rows.append(
                {
                    "hari": day,
                    "petugas": ", ".join(petugas_list) if petugas_list else "-",
                    "tugas": "Kebersihan lantai, papan tulis, ventilasi & kelengkapan spidol",
                }
            )

        denah_mode = (
            ov.denah_duduk.strip()
            if ov and ov.denah_duduk and ov.denah_duduk.strip()
            else "Kelompok Kolaboratif"
        )
        if denah_mode == "Tradisional Berbaris":
            denah_desc = "Formasi Klasikal 4 Banjar Menghadap Papan Tulis (Fokus Instruksi Langsung)"
        elif denah_mode == "U-Shape":
            denah_desc = "Formasi Huruf U / Tapal Kuda (Diskusi Terbuka & Presentasi Kelas)"
        else:
            denah_desc = "Formasi Klaster Kelompok 4-5 Siswa (Pembelajaran Mendalam & Kolaboratif)"

        seating_grid: List[List[str]] = []
        padded = list(names[:16])
        while len(padded) < 16:
            padded.append("Kursi Kosong")
        for row_i in range(4):
            row_cells = [
                f"Meja {row_i * 4 + col_i + 1}: {padded[row_i * 4 + col_i]}"
                for col_i in range(4)
            ]
            seating_grid.append(row_cells)

        kesepakatan = (
            list(ov.kesepakatan_kelas)
            if ov and ov.kesepakatan_kelas and len(ov.kesepakatan_kelas) > 0
            else list(DEFAULT_KESEPAKATAN_KELAS)
        )

        return {
            "rombel": rombel,
            "wali_kelas": wali_kelas,
            "pengurus": [
                {"jabatan": "Kepala Sekolah", "nama": teacher.nama_kepala_sekolah},
                {"jabatan": "Wali Kelas / Pembina", "nama": wali_kelas},
                {"jabatan": "Ketua Kelas", "nama": ketua},
                {"jabatan": "Wakil Ketua Kelas", "nama": wakil},
                {"jabatan": "Sekretaris Kelas", "nama": sekretaris},
                {"jabatan": "Bendahara Kelas", "nama": bendahara},
            ],
            "jadwal_piket": piket_rows,
            "denah_duduk": denah_mode,
            "denah_desc": denah_desc,
            "seating_grid": seating_grid,
            "kesepakatan_kelas": kesepakatan,
            "total_siswa": len(students),
        }


class SupervisiBlueprint:
    """Shared deterministic blueprint for Service 18 (Paket Siap Supervisi)."""

    INSTRUMEN_ITEMS = [
        ("1", "Administrasi Kelas & Kesepakatan Belajar", "02_admin_kelas", "Struktur organisasi, jadwal piket, denah duduk, kesepakatan kelas"),
        ("2", "Capaian Pembelajaran & Tujuan Pembelajaran (CP-TP)", "03_cp_tp", "Selaras Kepka BSKAP No. 046/H/KR/2025"),
        ("3", "Alur Tujuan Pembelajaran (ATP)", "04_atp", "Pengurutan TP logis & alokasi JP semester"),
        ("4", "Program Tahunan (Prota) & Program Semester (Promes)", "05_prota / 06_promes", "Distribusi pekan efektif sesuai Permendikdasmen 13/2025"),
        ("5", "Kriteria Ketercapaian Tujuan Pembelajaran (KKTP)", "07_kktp", "Rubrik/interval kriteria ketuntasan terukur"),
        ("6", "Modul Ajar / RPP Pembelajaran Mendalam (3M) & LKPD", "08_modul_ajar / 09_lkpd", "Integrasi 8 DPL (Permendikdasmen 10/2025) & siklus Memahami-Mengaplikasi-Merefleksi"),
        ("7", "Perangkat Asesmen Sumatif (Kuis, Sumatif Bab, STS/SAS)", "10_kuis - 12_sts_sas", "Kisi-kisi 7 kolom, kartu soal, kunci jawaban"),
        ("8", "Presensi Siswa & Jurnal Mengajar Harian", "13_presensi / 14_jurnal_mengajar", "Rekap kehadiran otomatis & catatan refleksi pertemuan"),
        ("9", "Daftar Nilai, Deskripsi e-Rapor, & Rekap Peringkat", "15_daftar_nilai - 17_rekap_rapor", "Pembobotan Sumatif/SAS & narasi e-Rapor objektif"),
    ]

    @staticmethod
    def build_blueprint(
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
    ) -> Dict[str, Any]:
        ov = request.custom_overrides
        rombel = _resolve_rombel_label(request)
        nomor_sk = (
            ov.nomor_sk_mengajar.strip()
            if ov and ov.nomor_sk_mengajar and ov.nomor_sk_mengajar.strip()
            else "800/SK-PBM/2025"
        )
        tanggal_supervisi = (
            ov.tanggal_supervisi.strip()
            if ov and ov.tanggal_supervisi and ov.tanggal_supervisi.strip()
            else "Sesuai Jadwal Supervisi Akademik Semester Berjalan"
        )
        nama_pengawas = (
            ov.nama_pengawas.strip()
            if ov and ov.nama_pengawas and ov.nama_pengawas.strip()
            else "........................................"
        )
        nip_pengawas = (
            ov.nip_pengawas.strip()
            if ov and ov.nip_pengawas and ov.nip_pengawas.strip()
            else "-"
        )

        sem_chapters = [ch for ch in subject.bab_list if ch.semester == request.semester]
        if not sem_chapters:
            sem_chapters = list(subject.bab_list)
        total_jp = sum(ch.calculate_total_jp() for ch in sem_chapters)

        bundle_manifest = [
            {"no": "01", "berkas": "01_Cover_Pengesahan_Instrumen_Supervisi.docx", "isi": "Cover Resmi, Daftar Isi, Pengesahan 3 Pihak & Instrumen Supervisi"},
            {"no": "02", "berkas": "02_Administrasi_Kelas.docx", "isi": "Struktur Kelas, Piket, Denah Duduk, Kesepakatan Kelas"},
            {"no": "03", "berkas": "03_CP_dan_TP.docx", "isi": "Capaian Pembelajaran Fase & Tujuan Pembelajaran BSKAP 046/2025"},
            {"no": "04", "berkas": "04_Alur_Tujuan_Pembelajaran_ATP.docx", "isi": "Pemetaan Alur Tujuan Pembelajaran per Semester"},
            {"no": "05", "berkas": "05_Program_Tahunan_Prota.docx", "isi": "Program Tahunan Alokasi JP"},
            {"no": "06", "berkas": "06_Program_Semester_Promes.xlsx", "isi": "Matriks Program Semester Berformula Excel"},
            {"no": "07", "berkas": "07_KKTP.docx", "isi": "Kriteria Ketercapaian Tujuan Pembelajaran"},
            {"no": "08", "berkas": "08_Modul_Ajar_DeepLearning_3M.docx", "isi": "Modul Ajar / RPP 8 DPL & 3M Lengkap"},
            {"no": "09", "berkas": "09_LKPD_Mandiri.docx", "isi": "Lembar Kerja Peserta Didik Mandiri 3M"},
            {"no": "10", "berkas": "13_Presensi_Siswa_Bulanan.xlsx", "isi": "Daftar Hadir Bulanan Berformula =COUNTIF"},
            {"no": "11", "berkas": "14_Jurnal_Mengajar_Harian.docx", "isi": "Jurnal Mengajar 9 Kolom & Refleksi"},
            {"no": "12", "berkas": "15_Daftar_Nilai_Siswa.xlsx", "isi": "Buku Pengolahan Nilai Berformula =AVERAGE"},
            {"no": "13", "berkas": "16_Deskripsi_eRapor.docx", "isi": "Narasi Deskripsi Capaian Kompetensi e-Rapor"},
            {"no": "14", "berkas": "17_Rekap_Nilai_Rapor.xlsx", "isi": "Rekapitulasi Nilai Rapor Final & Peringkat (=RANK)"},
            {"no": "15", "berkas": "18_Binder_Supervisi_Siap_Cetak.pdf", "isi": "PDF Gabungan Cover, Pengesahan & Instrumen Supervisi"},
        ]

        return {
            "rombel": rombel,
            "nomor_sk_mengajar": nomor_sk,
            "tanggal_supervisi": tanggal_supervisi,
            "nama_pengawas": nama_pengawas,
            "nip_pengawas": nip_pengawas,
            "elemen_cp_count": len(getattr(subject, "elemen_cp_resmi", []) or []),
            "chapter_count": len(sem_chapters),
            "total_jp": total_jp,
            "chapters": sem_chapters,
            "bundle_manifest": bundle_manifest,
            "instrumen_items": SupervisiBlueprint.INSTRUMEN_ITEMS,
            "fokus_bab": chapter.judul_bab if chapter else (sem_chapters[0].judul_bab if sem_chapters else subject.nama_mapel),
        }
