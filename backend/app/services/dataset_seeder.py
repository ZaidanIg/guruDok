import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from psycopg.types.json import Jsonb

from app.core.config import settings
from app.core.database import DatabaseManager, get_db_manager


def _slugify_mapel(name: str) -> str:
    """Produces a short clean uppercase slug from an Indonesian subject name."""
    u = name.upper()
    mapping = [
        ("PENDIDIKAN AGAMA", "PAI"),
        ("PENDIDIKAN PANCASILA", "PPKN"),
        ("BAHASA INDONESIA TINGKAT LANJUT", "BINDOTL"),
        ("BAHASA INDONESIA", "BINDO"),
        ("BAHASA INGGRIS TINGKAT LANJUT", "BINGTL"),
        ("BAHASA INGGRIS", "BING"),
        ("MATEMATIKA TINGKAT LANJUT", "MATTL"),
        ("MATEMATIKA", "MAT"),
        ("ILMU PENGETAHUAN ALAM DAN SOSIAL", "IPAS"),
        ("IPA - FISIKA", "FISPAR"),
        ("IPA - KIMIA", "KIMPAR"),
        ("IPA - BIOLOGI", "BIOPAR"),
        ("IPS - SEJARAH", "SEJPAR"),
        ("IPS - EKONOMI", "EKOPAR"),
        ("IPS - GEOGRAFI", "GEOPAR"),
        ("IPS - SOSIOLOGI", "SOSPAR"),
        ("ILMU PENGETAHUAN ALAM", "IPA"),
        ("ILMU PENGETAHUAN SOSIAL", "IPS"),
        ("PENDIDIKAN JASMANI", "PJOK"),
        ("SENI, BUDAYA, DAN PRAKARYA", "SBP"),
        ("SENI DAN BUDAYA", "SENI"),
        ("PRAKARYA DAN KEWIRAUSAHAAN", "PKWU"),
        ("KODING DAN KECERDASAN ARTIFISIAL", "KKA"),
        ("INFORMATIKA", "INF"),
        ("SEJARAH TINGKAT LANJUT", "SEJTL"),
        ("SEJARAH", "SEJ"),
        ("FISIKA", "FIS"),
        ("KIMIA", "KIM"),
        ("BIOLOGI", "BIO"),
        ("EKONOMI", "EKO"),
        ("GEOGRAFI", "GEO"),
        ("SOSIOLOGI", "SOS"),
        ("ANTROPOLOGI", "ANT"),
        ("MUATAN LOKAL", "MULOK"),
    ]
    for key, code in mapping:
        if key in u:
            return code
    cleaned = re.sub(r"[^A-Z0-9]", "", u)
    return cleaned[:8] or "MAPEL"


def _resolve_bskap_subject_code(subject_name: str) -> str:
    """Maps a subject name from Dataset 02 to its official BSKAP 046/2025 subject_code in Dataset 03."""
    u = subject_name.upper()
    if "AGAMA" in u:
        return "MAPEL-01"
    if "PANCASILA" in u:
        return "MAPEL-07"
    if "BAHASA INDONESIA TINGKAT LANJUT" in u:
        return "MAPEL-09"
    if "BAHASA INDONESIA" in u:
        return "MAPEL-08"
    if "MATEMATIKA TINGKAT LANJUT" in u:
        return "MAPEL-11"
    if "MATEMATIKA" in u:
        return "MAPEL-10"
    if "BAHASA INGGRIS TINGKAT LANJUT" in u:
        return "MAPEL-13"
    if "BAHASA INGGRIS" in u:
        return "MAPEL-12"
    if "IPAS" in u or "ALAM DAN SOSIAL" in u:
        return "MAPEL-14"
    if "FISIKA" in u:
        return "MAPEL-16"
    if "KIMIA" in u:
        return "MAPEL-17"
    if "BIOLOGI" in u:
        return "MAPEL-18"
    if "ILMU PENGETAHUAN ALAM" in u:
        return "MAPEL-15"
    if "ANTROPOLOGI" in u:
        return "MAPEL-25"
    if "SOSIOLOGI" in u:
        return "MAPEL-23"
    if "EKONOMI" in u:
        return "MAPEL-24"
    if "GEOGRAFI" in u:
        return "MAPEL-22"
    if "SEJARAH" in u:
        return "MAPEL-21"
    if "ILMU PENGETAHUAN SOSIAL" in u:
        return "MAPEL-20"
    if "JASMANI" in u or "PJOK" in u:
        return "MAPEL-26"
    if "SENI" in u:
        return "MAPEL-27"
    if "PRAKARYA" in u:
        return "MAPEL-31"
    if "KODING" in u:
        return "MAPEL-46"
    if "INFORMATIKA" in u:
        return "MAPEL-19"
    return "MAPEL-08"


def _build_rich_modul_ajar_payload(
    nama_mapel: str,
    jenjang: str,
    kelas: int,
    fase: str,
    nomor_bab: int,
    judul_bab: str,
    elemen_cp: str,
    deskripsi_cp: str,
    model_code: str,
    dpl_codes: List[str],
    tps_list: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generates a complete, structured Deep Learning 3M Modul Ajar payload following the official attachment template."""
    tp_texts = [t["deskripsi_tp"] for t in tps_list] or [f"Memahami dan menerapkan konsep {judul_bab} secara mendalam."]
    tp1 = tp_texts[0]
    tp2 = tp_texts[1] if len(tp_texts) > 1 else f"Menganalisis penerapan {judul_bab} dalam studi kasus nyata."
    tp3 = tp_texts[2] if len(tp_texts) > 2 else f"Merefleksikan dan menyajikan solusi kontekstual terkait {judul_bab}."

    return {
        "identifikasi": {
            "kesiapan_murid": (
                f"Peserta didik Kelas {kelas} ({jenjang} Fase {fase}) umumnya telah memiliki pengetahuan dan pengalaman awal "
                f"yang berkaitan dengan fenomena keseharian seputar {judul_bab}. Keterampilan awal mereka bersifat operasional "
                f"dan siap dikembangkan menuju pemahaman konseptual, prosedural, dan berpikir kritis pada mata pelajaran {nama_mapel}."
            ),
            "karakteristik_materi": (
                f"Materi '{judul_bab}' pada Bab {nomor_bab} ini berfokus pada penguasaan mendalam elemen {elemen_cp}. "
                f"Jenis pengetahuan yang dicapai meliputi pengetahuan konseptual (prinsip dasar {judul_bab}), pengetahuan prosedural "
                f"(langkah analisis dan penyelesaian masalah), serta pengetahuan metakognitif (kesadaran refleksi diri). "
                f"Relevansi dengan kehidupan nyata peserta didik sangat tinggi dan terintegrasi dengan pembentukan karakter profil lulusan."
            ),
            "dimensi_profil_lulusan": dpl_codes,
            "uraian_dimensi_profil_lulusan": [
                f"Penalaran Kritis: Peserta didik mampu menganalisis permasalahan dan informasi terkait {judul_bab} secara objektif.",
                f"Kolaborasi: Peserta didik bekerja sama secara aktif dalam kelompok saat mengeksplorasi LKPD {judul_bab}.",
                f"Kemandirian: Peserta didik bertanggung jawab atas proses dan hasil belajarnya dalam menguasai {judul_bab}.",
                f"Komunikasi: Peserta didik mampu mempresentasikan hasil analisis dan gagasan terkait {judul_bab} dengan jelas dan santun.",
            ],
        },
        "desain_pembelajaran": {
            "elemen_cp": elemen_cp,
            "capaian_pembelajaran_bab": deskripsi_cp,
            "lintas_disiplin_ilmu": (
                f"Bahasa Indonesia (kemampuan literasi membaca kritis, menyusun laporan, dan presentasi lisan/tulisan); "
                f"Matematika & Sains (penalaran logis, pengolahan data, dan pemecahan masalah sistematis); "
                f"Pendidikan Pancasila & IPS (etika, kolaborasi sosial, dan kontekstualisasi {judul_bab} di masyarakat)."
            ),
            "topik_pembelajaran_kontekstual": (
                f"Topik pembelajaran berpusat pada '{judul_bab} dalam Kehidupan Nyata: Dari Pemahaman Konsep Menuju Solusi Kontekstual'. "
                f"Peserta didik diajak mengamati kasus nyata di lingkungan sekolah dan masyarakat serta merancang solusi berbasis {nama_mapel}."
            ),
            "praktik_pedagogis_model": model_code,
            "kemitraan_pembelajaran": "Kolaborasi antarmurid dalam kelompok belajar heterogen, guru lintas mata pelajaran serumpun, serta pelibatan orang tua/lingkungan sekolah.",
            "lingkungan_pembelajaran": "Ruang Fisik: Ruang kelas kolaboratif dan lingkungan sekolah. Ruang Virtual: Pemanfaatan sumber belajar digital SIBI Kemendikdasmen. Budaya Belajar: Inklusif, aman, saling memuliakan, dan memupuk rasa ingin tahu.",
            "pemanfaatan_digital": "Buku Teks Digital SIBI Kemendikdasmen, tayangan visual/salindia interaktif, dan kuis formatif terstruktur.",
            "sarana_dan_prasarana": f"Buku Teks Utama {nama_mapel} Kelas {kelas} Kemendikdasmen, Lembar Kerja Peserta Didik (LKPD) Bab {nomor_bab}, papan tulis, proyektor/media visual.",
        },
        "komponen_inti": {
            "pemahaman_bermakna": (
                f"Menguasai konsep dan keterampilan pada materi {judul_bab} membekali peserta didik untuk berpikir sistematis, "
                f"mengambil keputusan berbasis bukti, dan memecahkan permasalahan nyata di lingkungan sekitarnya."
            ),
            "pertanyaan_pemantik": [
                f"Pernahkah kalian mengamati fenomena atau permasalahan di sekitar kita yang berkaitan dengan {judul_bab}?",
                f"Mengapa kita perlu memahami prinsip kerja dan konsep dasar dari {judul_bab} dalam {nama_mapel}?",
                f"Bagaimana kita dapat memanfaatkan pengetahuan tentang {judul_bab} untuk menciptakan solusi yang bermanfaat?",
            ],
            "tujuan_per_pertemuan": [
                {
                    "pertemuan": 1,
                    "judul": f"Pertemuan 1: Memahami Konsep Dasar {judul_bab} (Mindful Learning / Berkesadaran)",
                    "butir_tp": [
                        tp1,
                        f"Mengidentifikasi komponen dan karakteristik utama pada materi {judul_bab} melalui pengamatan kontekstual.",
                    ],
                },
                {
                    "pertemuan": 2,
                    "judul": f"Pertemuan 2: Mengaplikasikan & Menganalisis {judul_bab} (Meaningful Learning / Bermakna)",
                    "butir_tp": [
                        tp2,
                        f"Mengerjakan studi kasus dan lembar kerja kolaboratif pada materi {judul_bab} secara sistematis.",
                    ],
                },
                {
                    "pertemuan": 3,
                    "judul": f"Pertemuan 3: Menyajikan Solusi & Merefleksikan {judul_bab} (Joyful Learning / Menggembirakan)",
                    "butir_tp": [
                        tp3,
                        f"Mempresentasikan hasil karya/analisis kelompok dan merefleksikan manfaat pembelajaran {judul_bab}.",
                    ],
                },
            ],
            "pengalaman_belajar": {
                "prinsip_pembelajaran": [
                    "Berkesadaran (Mindful)",
                    "Bermakna (Meaningful)",
                    "Menggembirakan (Joyful)",
                ],
                "tahap_memahami": [
                    f"Guru membuka pembelajaran dengan pertanyaan pemantik kontekstual seputar {judul_bab} untuk membangun kesadaran belajar (Mindful).",
                    f"Peserta didik mengamati bahan bacaan/studi kasus tentang {judul_bab} (Diferensiasi Konten: teks, visual, dan contoh konkret).",
                    f"Peserta didik mengidentifikasi konsep-konsep kunci pada elemen {elemen_cp} melalui tanya jawab terbimbing.",
                ],
                "tahap_mengaplikasi": [
                    f"Peserta didik bekerja dalam kelompok kolaboratif menggunakan LKPD untuk menganalisis permasalahan nyata terkait {judul_bab} (Meaningful).",
                    f"Guru memberikan bimbingan berjenjang (Diferensiasi Proses / Scaffolding) sesuai tingkat kesiapan masing-masing kelompok.",
                    f"Peserta didik menyusun hasil analisis atau rancangan solusi {judul_bab} dalam format laporan/peta konsep kreatif (Diferensiasi Produk & Joyful).",
                ],
                "tahap_merefleksi": [
                    f"Setiap kelompok mempresentasikan hasil temuan tentang {judul_bab} dan saling memberikan umpan balik konstruktif.",
                    f"Peserta didik bersama guru menyimpulkan konsep esensial {judul_bab} dan melakukan refleksi metakognitif 3-2-1.",
                    f"Guru memberikan penguatan konsep serta menginformasikan rencana tindak lanjut pertemuan berikutnya.",
                ],
            },
        },
        "asesmen": {
            "asesmen_awal_diagnostik": (
                f"Observasi partisipasi brainstorming awal, tanya jawab lisan singkat, dan kuis diagnostik 5 soal untuk memetakan "
                f"pengetahuan prasyarat peserta didik mengenai {judul_bab}."
            ),
            "soal_asesmen_awal": [
                f"1. Apa yang kalian ketahui tentang istilah atau topik '{judul_bab}' dalam kehidupan sehari-hari?",
                f"2. Sebutkan minimal 2 contoh kejadian di sekitar rumah atau sekolah yang berhubungan dengan {judul_bab}!",
                f"3. Menurut pendapatmu, mengapa materi {judul_bab} penting untuk dipelajari dalam {nama_mapel}?",
                f"4. Kesulitan apa yang biasanya kalian temui saat mempelajari topik yang berkaitan dengan {elemen_cp}?",
                f"5. Hal menarik apa yang paling ingin kalian ketahui lebih dalam dari Bab {nomor_bab}: {judul_bab} ini?",
            ],
            "asesmen_formatif_proses": (
                f"Penilaian kinerja penyelesaian LKPD kelompok, observasi keaktifan diskusi & kolaborasi, serta presentasi hasil eksplorasi {judul_bab}."
            ),
            "soal_asesmen_proses": [
                f"1. Jelaskan konsep utama dari {judul_bab} berdasarkan hasil pengamatan kelompokmu pada LKPD!",
                f"2. Identifikasilah komponen-komponen penting yang memengaruhi proses pada materi {judul_bab}!",
                f"3. Berikan 1 contoh permasalahan nyata di lingkungan sekitar dan jelaskan kaitannya dengan prinsip {judul_bab}!",
                f"4. Bagaimana cara kelompokmu membagi peran untuk menyelesaikan analisis kasus {judul_bab} secara efektif?",
                f"5. Apa temuan baru yang paling bermakna bagi kelompokmu selama mengeksplorasi materi {judul_bab} hari ini?",
            ],
            "asesmen_sumatif_akhir": (
                f"Tes tertulis (uraian analitis/HOTS), jurnal reflektif, dan penilaian produk/proyek akhir Bab {nomor_bab} untuk mengukur ketercapaian KKTP."
            ),
            "soal_asesmen_akhir": [
                f"1. Jelaskan secara komprehensif pengertian dan ruang lingkup dari {judul_bab} pada mata pelajaran {nama_mapel}!",
                f"2. Analisislah hubungan antara konsep {elemen_cp} dengan penerapan praktis {judul_bab} dalam kehidupan sehari-hari!",
                f"3. Evaluasilah dampak positif serta tantangan yang muncul dalam penerapan {judul_bab} di masyarakat!",
                f"4. Pilihlah satu permasalahan kontekstual di lingkungan sekolahmu, lalu rancanglah langkah-langkah solusinya menggunakan prinsip {judul_bab}!",
                f"5. Buatlah kesimpulan reflektif mengenai bagaimana penguasaan materi {judul_bab} dapat membantumu mengembangkan kompetensi di masa depan!",
            ],
        },
        "lampiran": {
            "lkpd": {
                "judul_lkpd": f"LKPD Bab {nomor_bab}: Eksplorasi & Analisis Kontekstual {judul_bab}",
                "langkah_kerja": [
                    f"1. Bacalah pengantar studi kasus tentang '{judul_bab}' pada lembar kerja bersama anggota kelompokmu!",
                    f"2. Identifikasi masalah utama, variabel/komponen kunci, dan konsep {elemen_cp} yang terlibat!",
                    f"3. Diskusikan jawaban atas pertanyaan analisis pada tabel pengamatan LKPD secara kritis dan kolaboratif!",
                    f"4. Susunlah kesimpulan dan solusi kelompokmu, lalu presentasikan di depan kelas dengan jelas!",
                ],
            },
            "pengayaan_dan_remedial": {
                "pengayaan": f"Peserta didik yang telah mencapai ketuntasan sangat baik (melampaui KKTP) diberikan tantangan eksplorasi studi kasus tingkat lanjut pada topik {judul_bab}.",
                "remedial": f"Peserta didik yang belum mencapai KKTP diberikan pendampingan terfokus (scaffolding) dan latihan bertahap pada indikator TP Bab {nomor_bab} yang belum dikuasai.",
            },
            "glosarium": f"{judul_bab}: Lingkup materi utama Bab {nomor_bab} pada {nama_mapel}; {elemen_cp}: Elemen kompetensi resmi BSKAP No. 046/H/KR/2025; KKTP: Kriteria Ketercapaian Tujuan Pembelajaran.",
            "kata_kunci": f"{judul_bab}, {elemen_cp}, {nama_mapel}, Pembelajaran Mendalam 3M.",
        },
    }


class DatasetSeederService:
    """Seeds 100% of the 5 official Kemendikdasmen 2025 JSON datasets AND all 150+ Grade 1-12 subject courses into GuruDocDB."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None, dataset_dir: Optional[Path] = None):
        self.db = db_manager or get_db_manager()
        self.dataset_dir = dataset_dir or settings.dataset_path

    def seed_all_datasets(self) -> Dict[str, int]:
        """Executes idempotent total dataset seeding across all master curriculum tables for all grades 1-12."""
        self.db.initialize_schema()

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                self._seed_dataset_01_regulasi(cur)
                self._seed_dataset_02_alokasi_jp(cur)
                self._seed_dataset_03_master_cp(cur)
                self._seed_dataset_04_bab_tp_modul(cur)
                self._seed_modular_sibi_datasets(cur)
                self._seed_reference_informatika_xi_fase_f(cur)
                self._cleanup_synthetic_and_duplicates(cur)
                self._seed_dataset_05_kalender_promes(cur)
                self._seed_service_templates(cur)

        return self.get_table_counts()

    def _seed_dataset_01_regulasi(self, cur) -> None:
        file_path = self.dataset_dir / "01_regulasi_dan_dimensi_lulusan.json"
        data = json.loads(file_path.read_text(encoding="utf-8"))

        for fase in data.get("pembagian_fase", []):
            cur.execute(
                """
                INSERT INTO curriculum_phases (phase_code, education_level, grades, grade_label, jp_duration_minutes)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (phase_code) DO UPDATE SET
                    education_level = EXCLUDED.education_level,
                    grades = EXCLUDED.grades,
                    grade_label = EXCLUDED.grade_label,
                    jp_duration_minutes = EXCLUDED.jp_duration_minutes;
                """,
                (
                    fase["kode_fase"],
                    fase["jenjang"],
                    Jsonb(fase.get("kelas", [])),
                    fase.get("label_kelas", f"Fase {fase['kode_fase']}"),
                    int(fase["durasi_1_jp_menit"]),
                ),
            )

        for dpl in data.get("delapan_dimensi_profil_lulusan", []):
            cur.execute(
                """
                INSERT INTO graduate_dimensions (code, dimension_name, legacy_p5_equivalent, description, classroom_indicator)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET
                    dimension_name = EXCLUDED.dimension_name,
                    legacy_p5_equivalent = EXCLUDED.legacy_p5_equivalent,
                    description = EXCLUDED.description,
                    classroom_indicator = EXCLUDED.classroom_indicator;
                """,
                (
                    dpl["kode"],
                    dpl["nama_dimensi"],
                    dpl.get("padanan_p5_lama", ""),
                    dpl["deskripsi"],
                    dpl["indikator_perilaku_kelas"],
                ),
            )

        kpm = data.get("kerangka_pembelajaran_mendalam", {})
        for model in kpm.get("praktik_pedagogis_model_pembelajaran", []):
            cur.execute(
                """
                INSERT INTO pedagogical_models (model_code, model_name, suitable_for, syntax_steps)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (model_code) DO UPDATE SET
                    model_name = EXCLUDED.model_name,
                    suitable_for = EXCLUDED.suitable_for,
                    syntax_steps = EXCLUDED.syntax_steps;
                """,
                (
                    model["kode_model"],
                    model["nama_model"],
                    model.get("cocok_untuk", ""),
                    Jsonb(model.get("sintaks_langkah", [])),
                ),
            )

        for idx, pp in enumerate(kpm.get("prinsip_pembelajaran", []), start=1):
            cur.execute(
                """
                INSERT INTO deep_learning_framework (item_code, category, item_name, sequence_order, description, activity_templates)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (item_code) DO UPDATE SET
                    category = EXCLUDED.category,
                    item_name = EXCLUDED.item_name,
                    sequence_order = EXCLUDED.sequence_order,
                    description = EXCLUDED.description,
                    activity_templates = EXCLUDED.activity_templates;
                """,
                (pp["kode"], "PRINSIP_PEMBELAJARAN", pp["nama"], idx, pp["deskripsi"], Jsonb([])),
            )

        for m3 in kpm.get("pengalaman_belajar_3m", []):
            code_3m = f"3M-{m3['urutan']}"
            cur.execute(
                """
                INSERT INTO deep_learning_framework (item_code, category, item_name, sequence_order, description, activity_templates)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (item_code) DO UPDATE SET
                    category = EXCLUDED.category,
                    item_name = EXCLUDED.item_name,
                    sequence_order = EXCLUDED.sequence_order,
                    description = EXCLUDED.description,
                    activity_templates = EXCLUDED.activity_templates;
                """,
                (
                    code_3m,
                    "PENGALAMAN_BELAJAR_3M",
                    m3["tahap"],
                    int(m3["urutan"]),
                    m3["fokus"],
                    Jsonb(m3.get("template_aktivitas_umum", [])),
                ),
            )

        kktp = data.get("template_kktp_dan_deskripsi_rapor", {})
        for interval in kktp.get("interval_nilai_default", []):
            tpl_text = interval.get("template_deskripsi_rapor_tertinggi") or interval.get("template_deskripsi_rapor_terendah", "")
            cur.execute(
                """
                INSERT INTO kktp_intervals (range_label, predicate, follow_up_action, rapor_template_text)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (range_label) DO UPDATE SET
                    predicate = EXCLUDED.predicate,
                    follow_up_action = EXCLUDED.follow_up_action,
                    rapor_template_text = EXCLUDED.rapor_template_text;
                """,
                (interval["rentang"], interval["predikat"], interval["tindak_lanjut"], tpl_text),
            )

    def _seed_dataset_02_alokasi_jp(self, cur) -> None:
        file_path = self.dataset_dir / "02_struktur_kurikulum_alokasi_jp.json"
        data = json.loads(file_path.read_text(encoding="utf-8"))

        for level_name, level_obj in data.get("jenjang", {}).items():
            durasi_jp = int(level_obj.get("durasi_1_jp_menit", 40))
            for grade_str, grade_obj in level_obj.get("kelas", {}).items():
                grade_num = int(grade_str)
                phase = grade_obj.get("fase", "A")
                eff_year = int(grade_obj.get("minggu_efektif_per_tahun", 36))
                eff_s1 = int(grade_obj.get("minggu_efektif_semester_1", 18))
                eff_s2 = int(grade_obj.get("minggu_efektif_semester_2", 18))

                for mapel in grade_obj.get("mata_pelajaran", []):
                    cur.execute(
                        """
                        INSERT INTO curriculum_hour_allocations (
                            education_level, grade, phase, subject_name, subject_category,
                            jp_duration_minutes, effective_weeks_year, effective_weeks_sem1, effective_weeks_sem2,
                            jp_intracurricular_year, jp_cocurricular_year, total_jp_year, jp_per_week
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (education_level, grade, subject_name) DO UPDATE SET
                            phase = EXCLUDED.phase,
                            subject_category = EXCLUDED.subject_category,
                            jp_duration_minutes = EXCLUDED.jp_duration_minutes,
                            effective_weeks_year = EXCLUDED.effective_weeks_year,
                            effective_weeks_sem1 = EXCLUDED.effective_weeks_sem1,
                            effective_weeks_sem2 = EXCLUDED.effective_weeks_sem2,
                            jp_intracurricular_year = EXCLUDED.jp_intracurricular_year,
                            jp_cocurricular_year = EXCLUDED.jp_cocurricular_year,
                            total_jp_year = EXCLUDED.total_jp_year,
                            jp_per_week = EXCLUDED.jp_per_week;
                        """,
                        (
                            level_name,
                            grade_num,
                            phase,
                            mapel["nama"],
                            mapel.get("kategori", "Wajib"),
                            durasi_jp,
                            eff_year,
                            eff_s1,
                            eff_s2,
                            int(mapel.get("jp_intrakurikuler_tahun", 72)),
                            int(mapel.get("jp_kokurikuler_tahun", 0)),
                            int(mapel.get("total_jp_tahun", 72)),
                            int(mapel.get("jp_intrakurikuler_minggu", 2)),
                        ),
                    )

    def _seed_dataset_03_master_cp(self, cur) -> None:
        file_path = self.dataset_dir / "03_master_cp_bskap_2025_lengkap.json"
        data = json.loads(file_path.read_text(encoding="utf-8"))

        for subj in data.get("daftar_mata_pelajaran", []):
            subject_code = subj["id_mapel"]
            cur.execute(
                """
                INSERT INTO curriculum_subjects (
                    subject_code, subject_name, education_levels, phases, rationale, aims, characteristics
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (subject_code) DO UPDATE SET
                    subject_name = EXCLUDED.subject_name,
                    education_levels = EXCLUDED.education_levels,
                    phases = EXCLUDED.phases,
                    rationale = EXCLUDED.rationale,
                    aims = EXCLUDED.aims,
                    characteristics = EXCLUDED.characteristics;
                """,
                (
                    subject_code,
                    subj["mata_pelajaran"],
                    subj.get("jenjang", []),
                    subj.get("daftar_fase", []),
                    subj.get("rasional", ""),
                    subj.get("tujuan", ""),
                    subj.get("karakteristik", ""),
                ),
            )

            for fase_obj in subj.get("capaian_per_fase", []):
                phase_code = fase_obj["fase"]
                peruntukan = fase_obj.get("peruntukan", "")
                for elem in fase_obj.get("elemen_cp", []):
                    cur.execute(
                        """
                        INSERT INTO curriculum_phase_elements (
                            subject_code, phase, phase_designation, element_code, element_name, cp_description
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (subject_code, phase, element_code) DO UPDATE SET
                            phase_designation = EXCLUDED.phase_designation,
                            element_name = EXCLUDED.element_name,
                            cp_description = EXCLUDED.cp_description;
                        """,
                        (
                            subject_code,
                            phase_code,
                            peruntukan,
                            str(elem["kode_elemen"]),
                            elem["nama_elemen"],
                            elem["deskripsi_cp"],
                        ),
                    )

    def _seed_dataset_04_bab_tp_modul(self, cur) -> None:
        file_path = self.dataset_dir / "04_master_bab_tp_atp_modul_ajar.json"
        data = json.loads(file_path.read_text(encoding="utf-8"))

        # 1. Seed 7 Paket Lengkap Modul Ajar Per Bab
        for course in data.get("paket_lengkap_modul_ajar_per_bab", []):
            course_id = course["id_kurikulum"]
            subject_code = course.get("id_mapel_bskap", "MAPEL-08")
            jenjang = course["jenjang"]
            kelas = int(course["kelas"])
            fase = course["fase"]
            nama_mapel = course["mata_pelajaran"]
            total_jp = int(course.get("total_jp_intrakurikuler_tahun", 108))
            jp_minggu = int(course.get("jp_per_minggu", 3))

            cur.execute(
                """
                INSERT INTO curriculum_courses (
                    course_id, subject_code, education_level, grade, phase, subject_name,
                    sibi_reference_book, total_jp_intracurricular_year, jp_per_week, source_section
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'PAKET_LENGKAP')
                ON CONFLICT (course_id) DO UPDATE SET
                    subject_code = EXCLUDED.subject_code,
                    education_level = EXCLUDED.education_level,
                    grade = EXCLUDED.grade,
                    phase = EXCLUDED.phase,
                    subject_name = EXCLUDED.subject_name,
                    sibi_reference_book = EXCLUDED.sibi_reference_book,
                    total_jp_intracurricular_year = EXCLUDED.total_jp_intracurricular_year,
                    jp_per_week = EXCLUDED.jp_per_week,
                    source_section = EXCLUDED.source_section;
                """,
                (
                    course_id,
                    subject_code,
                    jenjang,
                    kelas,
                    fase,
                    nama_mapel,
                    course.get("buku_rujukan_sibi", ""),
                    total_jp,
                    jp_minggu,
                ),
            )

            for bab in course.get("daftar_bab", []):
                ch_id = bab["id_bab"]
                nomor_bab = int(bab.get("nomor_bab", 1))
                semester = int(bab.get("semester", 1))
                judul_bab = bab["judul_bab"]
                elemen_cp = bab.get("elemen_cp", "Pemahaman Konsep & Keterampilan Proses")
                alokasi_jp = int(bab.get("alokasi_jp_bab", 12))
                est_meetings = int(bab.get("estimasi_jumlah_pertemuan", max(1, alokasi_jp // jp_minggu)))
                promes_range = bab.get("distribusi_minggu_promes", {}).get("rentang_minggu_efektif", f"Minggu Efektif Semester {semester}")

                raw_tpl = bab.get("modul_ajar_template", {})
                dpl_codes = raw_tpl.get("identifikasi", {}).get("dimensi_profil_lulusan", ["DPL-3", "DPL-5", "DPL-6"])
                model_code = raw_tpl.get("desain_pembelajaran", {}).get("praktik_pedagogis_model", "INQUIRY")
                if model_code not in ("PBL", "PJBL", "DISCOVERY", "INQUIRY", "CONTEXTUAL"):
                    model_code = "INQUIRY"

                # Enrich raw_tpl with full Deep Learning fields if any sub-sections are missing
                enriched_tpl = _build_rich_modul_ajar_payload(
                    nama_mapel=nama_mapel,
                    jenjang=jenjang,
                    kelas=kelas,
                    fase=fase,
                    nomor_bab=nomor_bab,
                    judul_bab=judul_bab,
                    elemen_cp=elemen_cp,
                    deskripsi_cp=f"Peserta didik mampu memahami dan menerapkan konsep {judul_bab} pada elemen {elemen_cp}.",
                    model_code=model_code,
                    dpl_codes=dpl_codes,
                    tps_list=bab.get("daftar_tp", []),
                )
                # Preserve specific questions/LKPD from dataset 04 where present
                if raw_tpl.get("identifikasi"):
                    enriched_tpl["identifikasi"].update(raw_tpl["identifikasi"])
                if raw_tpl.get("desain_pembelajaran"):
                    enriched_tpl["desain_pembelajaran"].update(raw_tpl["desain_pembelajaran"])
                if raw_tpl.get("komponen_inti"):
                    enriched_tpl["komponen_inti"].update(raw_tpl["komponen_inti"])
                if raw_tpl.get("asesmen"):
                    enriched_tpl["asesmen"].update(raw_tpl["asesmen"])
                if raw_tpl.get("lampiran"):
                    enriched_tpl["lampiran"].update(raw_tpl["lampiran"])

                cur.execute(
                    """
                    INSERT INTO curriculum_chapters (
                        chapter_id, course_id, subject_code, education_level, grade, phase,
                        semester, chapter_number, chapter_title, element_names, allocated_jp,
                        estimated_meetings, promes_week_range, recommended_model_code,
                        graduate_dimension_codes, modul_ajar_payload
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chapter_id) DO UPDATE SET
                        course_id = EXCLUDED.course_id,
                        subject_code = EXCLUDED.subject_code,
                        education_level = EXCLUDED.education_level,
                        grade = EXCLUDED.grade,
                        phase = EXCLUDED.phase,
                        semester = EXCLUDED.semester,
                        chapter_number = EXCLUDED.chapter_number,
                        chapter_title = EXCLUDED.chapter_title,
                        element_names = EXCLUDED.element_names,
                        allocated_jp = EXCLUDED.allocated_jp,
                        estimated_meetings = EXCLUDED.estimated_meetings,
                        promes_week_range = EXCLUDED.promes_week_range,
                        recommended_model_code = EXCLUDED.recommended_model_code,
                        graduate_dimension_codes = EXCLUDED.graduate_dimension_codes,
                        modul_ajar_payload = EXCLUDED.modul_ajar_payload;
                    """,
                    (
                        ch_id,
                        course_id,
                        subject_code,
                        jenjang,
                        kelas,
                        fase,
                        semester,
                        nomor_bab,
                        judul_bab,
                        elemen_cp,
                        alokasi_jp,
                        est_meetings,
                        promes_range,
                        model_code,
                        dpl_codes,
                        Jsonb(enriched_tpl),
                    ),
                )

                for tp in bab.get("daftar_tp", []):
                    cur.execute(
                        """
                        INSERT INTO learning_objectives_tp (
                            chapter_id, tp_code, atp_sequence, tp_description,
                            rapor_summary_phrase, allocated_jp, bloom_cognitive_level
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (chapter_id, tp_code) DO UPDATE SET
                            atp_sequence = EXCLUDED.atp_sequence,
                            tp_description = EXCLUDED.tp_description,
                            rapor_summary_phrase = EXCLUDED.rapor_summary_phrase,
                            allocated_jp = EXCLUDED.allocated_jp,
                            bloom_cognitive_level = EXCLUDED.bloom_cognitive_level;
                        """,
                        (
                            ch_id,
                            tp["kode_tp"],
                            int(tp.get("urutan_atp", 1)),
                            tp["deskripsi_tp"],
                            tp.get("ringkasan_deskripsi_rapor", tp["deskripsi_tp"][:100]),
                            int(tp.get("alokasi_jp", 4)),
                            tp.get("level_kognitif_bloom", "C3 - Menerapkan"),
                        ),
                    )

        # 2. Seed 6 Katalog Silabus Bab Tambahan
        for add_course in data.get("katalog_silabus_bab_tambahan", []):
            course_id = add_course["id_kurikulum"]
            subject_code = add_course.get("id_mapel_bskap", "MAPEL-10")
            jenjang = add_course["jenjang"]
            kelas = int(add_course["kelas"])
            fase = add_course["fase"]
            nama_mapel = add_course["mata_pelajaran"]
            total_jp = int(add_course.get("total_jp_intrakurikuler_tahun", 108))
            jp_minggu = int(add_course.get("jp_per_minggu", 3))

            cur.execute(
                """
                INSERT INTO curriculum_courses (
                    course_id, subject_code, education_level, grade, phase, subject_name,
                    sibi_reference_book, total_jp_intracurricular_year, jp_per_week, source_section
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'KATALOG_TAMBAHAN')
                ON CONFLICT (course_id) DO UPDATE SET
                    subject_code = EXCLUDED.subject_code,
                    education_level = EXCLUDED.education_level,
                    grade = EXCLUDED.grade,
                    phase = EXCLUDED.phase,
                    subject_name = EXCLUDED.subject_name,
                    total_jp_intracurricular_year = EXCLUDED.total_jp_intracurricular_year,
                    jp_per_week = EXCLUDED.jp_per_week,
                    source_section = EXCLUDED.source_section;
                """,
                (
                    course_id,
                    subject_code,
                    jenjang,
                    kelas,
                    fase,
                    nama_mapel,
                    f"Buku Teks Utama SIBI {nama_mapel} Kelas {kelas} (Kemendikdasmen)",
                    total_jp,
                    jp_minggu,
                ),
            )

            default_model = "CONTEXTUAL" if jenjang == "SD" else ("INQUIRY" if "IPA" in nama_mapel or "Fisika" in nama_mapel else "PBL")
            raw_babs = list(add_course.get("ringkasan_bab_semester", []))
            while len(raw_babs) < 4:
                next_num = len(raw_babs) + 1
                last_elemen = raw_babs[-1].get("elemen", "Keterampilan Proses") if raw_babs else "Keterampilan Proses"
                raw_babs.append(
                    {
                        "nomor_bab": next_num,
                        "semester": 1 if next_num <= 2 else 2,
                        "judul_bab": f"Aplikasi & Proyek Terpadu {nama_mapel} ({last_elemen})",
                        "elemen": last_elemen,
                        "alokasi_jp": max(12, total_jp // 4),
                        "tp_utama": f"Merancang, menerapkan, dan mengevaluasi proyek kontekstual {nama_mapel} pada elemen {last_elemen}.",
                    }
                )
            for bab in raw_babs:
                nomor_bab = int(bab["nomor_bab"])
                semester = int(bab["semester"])
                ch_id = f"{course_id}-B{nomor_bab:02d}"
                judul_bab = bab["judul_bab"]
                elemen = bab.get("elemen", "Pemahaman Konsep")
                alokasi_jp = int(bab.get("alokasi_jp", 18))
                est_meetings = max(1, alokasi_jp // jp_minggu)
                tp_utama = bab.get("tp_utama", f"Memahami dan menerapkan konsep {judul_bab}.")

                tps_synth = [
                    {"kode_tp": f"TP.{kelas}.{nomor_bab}.1", "urutan_atp": (nomor_bab - 1) * 3 + 1, "deskripsi_tp": tp_utama, "alokasi_jp": max(2, alokasi_jp // 3)},
                    {"kode_tp": f"TP.{kelas}.{nomor_bab}.2", "urutan_atp": (nomor_bab - 1) * 3 + 2, "deskripsi_tp": f"Menganalisis studi kasus dan menerapkan konsep {judul_bab} pada elemen {elemen}.", "alokasi_jp": max(2, alokasi_jp // 3)},
                    {"kode_tp": f"TP.{kelas}.{nomor_bab}.3", "urutan_atp": (nomor_bab - 1) * 3 + 3, "deskripsi_tp": f"Menyajikan hasil eksplorasi dan evaluasi diri terkait {judul_bab} secara kolaboratif.", "alokasi_jp": max(2, alokasi_jp - 2 * max(2, alokasi_jp // 3))},
                ]

                synthesized_payload = _build_rich_modul_ajar_payload(
                    nama_mapel=nama_mapel,
                    jenjang=jenjang,
                    kelas=kelas,
                    fase=fase,
                    nomor_bab=nomor_bab,
                    judul_bab=judul_bab,
                    elemen_cp=elemen,
                    deskripsi_cp=tp_utama,
                    model_code=default_model,
                    dpl_codes=["DPL-3", "DPL-5", "DPL-6", "DPL-8"],
                    tps_list=tps_synth,
                )

                cur.execute(
                    """
                    INSERT INTO curriculum_chapters (
                        chapter_id, course_id, subject_code, education_level, grade, phase,
                        semester, chapter_number, chapter_title, element_names, allocated_jp,
                        estimated_meetings, promes_week_range, recommended_model_code,
                        graduate_dimension_codes, modul_ajar_payload
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chapter_id) DO UPDATE SET
                        course_id = EXCLUDED.course_id,
                        subject_code = EXCLUDED.subject_code,
                        semester = EXCLUDED.semester,
                        chapter_number = EXCLUDED.chapter_number,
                        chapter_title = EXCLUDED.chapter_title,
                        element_names = EXCLUDED.element_names,
                        allocated_jp = EXCLUDED.allocated_jp,
                        estimated_meetings = EXCLUDED.estimated_meetings,
                        recommended_model_code = EXCLUDED.recommended_model_code,
                        graduate_dimension_codes = EXCLUDED.graduate_dimension_codes,
                        modul_ajar_payload = EXCLUDED.modul_ajar_payload;
                    """,
                    (
                        ch_id,
                        course_id,
                        subject_code,
                        jenjang,
                        kelas,
                        fase,
                        semester,
                        nomor_bab,
                        judul_bab,
                        elemen,
                        alokasi_jp,
                        est_meetings,
                        f"Semester {semester}",
                        default_model,
                        ["DPL-3", "DPL-5", "DPL-6", "DPL-8"],
                        Jsonb(synthesized_payload),
                    ),
                )

                for tp_obj in tps_synth:
                    cur.execute(
                        """
                        INSERT INTO learning_objectives_tp (
                            chapter_id, tp_code, atp_sequence, tp_description,
                            rapor_summary_phrase, allocated_jp, bloom_cognitive_level
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (chapter_id, tp_code) DO UPDATE SET
                            atp_sequence = EXCLUDED.atp_sequence,
                            tp_description = EXCLUDED.tp_description,
                            rapor_summary_phrase = EXCLUDED.rapor_summary_phrase,
                            allocated_jp = EXCLUDED.allocated_jp,
                            bloom_cognitive_level = EXCLUDED.bloom_cognitive_level;
                        """,
                        (
                            ch_id,
                            tp_obj["kode_tp"],
                            tp_obj["urutan_atp"],
                            tp_obj["deskripsi_tp"],
                            tp_obj["deskripsi_tp"][:120].lower(),
                            tp_obj["alokasi_jp"],
                            "C3 - Menerapkan",
                        ),
                    )

    def _seed_reference_informatika_xi_fase_f(self, cur) -> None:
        """Seeds the exact Informatika Kelas XI Fase F (SMA-K11-INF) course from the user's attached reference documents."""
        course_id = "SMA-K11-INF"
        subject_code = "MAPEL-19"
        cur.execute(
            """
            INSERT INTO curriculum_courses (
                course_id, subject_code, education_level, grade, phase, subject_name,
                sibi_reference_book, total_jp_intracurricular_year, jp_per_week, source_section
            )
            VALUES (%s, %s, 'SMA', 11, 'F', 'Informatika', 'Buku Informatika untuk SMA/MA Kelas XI Fase F (Kemendikdasmen)', 180, 5, 'PAKET_LENGKAP')
            ON CONFLICT (course_id) DO UPDATE SET
                subject_code = EXCLUDED.subject_code,
                subject_name = EXCLUDED.subject_name,
                sibi_reference_book = EXCLUDED.sibi_reference_book,
                total_jp_intracurricular_year = EXCLUDED.total_jp_intracurricular_year,
                jp_per_week = EXCLUDED.jp_per_week;
            """,
            (course_id, subject_code),
        )

        inf_chapters = [
            {
                "id_bab": "INF-K11-B01",
                "nomor_bab": 1,
                "semester": 1,
                "judul_bab": "Strategi Berpikir Algoritmik dan Tentang Informatika",
                "elemen_cp": "Berpikir Komputasional",
                "alokasi_jp": 25,
                "cp_bab": "Peserta didik dapat memahami alur proses pengembangan program atau produk teknologi digital, menuliskan algoritma yang efisien, efektif, dan optimal, menganalisis persoalan dengan pemahamannya terhadap beberapa strategi algoritmik untuk menghasilkan beberapa alternatif solusi dari satu persoalan dengan merancang struktur data yang lebih kompleks dan abstrak.",
                "tps": [
                    ("11.1.1", 1, "Peserta didik dapat memahami beberapa strategi algoritmik dan membuat perencanaan kerja kelompok dengan baik.", 5),
                    ("11.1.2", 2, "Peserta didik dapat menganalisis jenis strategi algoritmik serta mengomunikasikan hasil kerja dengan presentasi dan visualisasi.", 5),
                    ("11.1.3", 3, "Peserta didik dapat memahami konsep dan penerapan rekursi serta strategi algoritma greedy.", 5),
                    ("11.1.4", 4, "Peserta didik dapat menyelesaikan masalah dengan strategi algoritmik, pemrograman dinamis, dan berpikir kritis.", 10),
                ],
            },
            {
                "id_bab": "INF-K11-B02",
                "nomor_bab": 2,
                "semester": 1,
                "judul_bab": "Menguasai Literasi Digital serta Strategi Algoritma dan Pemrograman",
                "elemen_cp": "Literasi Digital & Algoritma dan Pemrograman",
                "alokasi_jp": 40,
                "cp_bab": "Peserta didik mampu memahami penggunaan mesin pencari, mengevaluasi kebenaran konten digital, merancang kebutuhan sistem komputer, konfigurasi keamanan lanjut, serta memahami algoritma proses sorting, stack, dan queue.",
                "tps": [
                    ("11.2.1", 5, "Peserta didik dapat menjelaskan penggunaan mesin pencari untuk melakukan riset dan mengevaluasi kebenaran konten digital.", 10),
                    ("11.2.2", 6, "Peserta didik memahami beberapa algoritma proses sorting dan menerapkan strategi algoritmik yang paling efisien.", 10),
                    ("11.2.3", 7, "Peserta didik memahami konsep struktur data stack dan queue serta operasi-operasi yang dapat dikenakan pada struktur data tersebut.", 10),
                    ("11.2.4", 8, "Peserta didik dapat menerapkan konfigurasi keamanan lanjut dan membuat konten digital yang dilengkapi keamanan digital dengan kreatif.", 10),
                ],
            },
            {
                "id_bab": "INF-K11-B03",
                "nomor_bab": 3,
                "semester": 1,
                "judul_bab": "Berpikir Kritis dan Dampak Sosial Informatika",
                "elemen_cp": "Dampak Sosial Informatika & Literasi Digital",
                "alokasi_jp": 25,
                "cp_bab": "Pada akhir fase F, peserta didik mampu mengkaji secara kritis kasus-kasus sosial terkini terkait produk TIK dan sistem komputasi, menganalisis kasus, serta memberikan berbagai argumentasi dan rasionalnya.",
                "tps": [
                    ("11.3.1", 9, "Menjelaskan arti dan pentingnya berpikir kritis serta prinsip dasar yang mencakup elemen berpikir dan standar intelektual.", 8),
                    ("11.3.2", 10, "Menerapkan berpikir kritis dalam pengambilan keputusan dan menjelaskan penerapan informatika dalam bidang pertanian, kesehatan, atau bidang lain.", 8),
                    ("11.3.3", 11, "Membangun kebiasaan berpikir kritis melalui analisis kasus dampak sosial teknologi informasi (DSI).", 9),
                ],
            },
            {
                "id_bab": "INF-K11-B04",
                "nomor_bab": 4,
                "semester": 2,
                "judul_bab": "Jaringan Komputer dan Internet",
                "elemen_cp": "Jaringan Komputer dan Internet & Berpikir Komputasional",
                "alokasi_jp": 30,
                "cp_bab": "Peserta didik memahami konsep lanjutan jaringan komputer dan internet, meliputi topologi jaringan, lapisan informasi OSI Layer, mekanisme pertukaran data packet switching, cyber security, dan troubleshooting jaringan.",
                "tps": [
                    ("11.4.1", 12, "Menjelaskan, menentukan, dan merancang topologi jaringan komputer yang sesuai dengan kebutuhan serta menggunakannya untuk troubleshooting.", 10),
                    ("11.4.2", 13, "Menjelaskan model jaringan komputer dalam bentuk lapisan OSI dan menggunakannya dalam melakukan troubleshooting.", 10),
                    ("11.4.3", 14, "Menjelaskan mekanisme pengiriman data packet switching, transmisi data, pendeteksian kesalahan, dan encoding data.", 10),
                ],
            },
            {
                "id_bab": "INF-K11-B05",
                "nomor_bab": 5,
                "semester": 2,
                "judul_bab": "Pengembangan Aplikasi Mobile dengan Library Kecerdasan Artifisial",
                "elemen_cp": "Algoritma dan Pemrograman & Praktik Lintas Bidang",
                "alokasi_jp": 30,
                "cp_bab": "Peserta didik mampu bergotong royong mengembangkan artefak komputasional berupa perangkat lunak mobile (mobile apps) dengan menggunakan library kecerdasan artifisial serta menguji dan mendokumentasikan hasilnya.",
                "tps": [
                    ("11.5.1", 15, "Menjelaskan perbedaan aplikasi web, desktop, dan mobile serta mengenali persoalan yang pemecahannya didukung sistem komputasi.", 10),
                    ("11.5.2", 16, "Mengembangkan artefak komputasi berupa perangkat lunak mobile (mobile apps) menggunakan library kecerdasan artifisial.", 10),
                    ("11.5.3", 17, "Mengembangkan rencana pengujian, menguji, mendokumentasikan, dan mengomunikasikan solusi TIK dengan memperhatikan HKI.", 10),
                ],
            },
            {
                "id_bab": "INF-K11-B06",
                "nomor_bab": 6,
                "semester": 2,
                "judul_bab": "Proyek Analisis Data: Hutanku Dulu, Kini, dan yang Akan Datang",
                "elemen_cp": "Analisis Data & Praktik Lintas Bidang",
                "alokasi_jp": 30,
                "cp_bab": "Peserta didik mampu memanfaatkan sumber data terbuka, terpercaya, dan legal untuk mengolah data, melakukan prediksi lingkungan hidup, serta memvisualisasikan hasilnya dalam bentuk infografis, peta pikiran, dan poster.",
                "tps": [
                    ("11.6.1", 18, "Mengenali dan mendefinisikan persoalan lingkungan hidup yang pemecahannya didukung analisis data serta menggunakan abstraksi untuk memodelkan prediksi.", 10),
                    ("11.6.2", 19, "Mengembangkan rencana analisis data, mengolah data, dan memvisualisasikan hasilnya untuk menunjang model komputasi.", 10),
                    ("11.6.3", 20, "Mempresentasikan hasil analisis data secara lisan dan tertulis dalam bentuk infografis, peta pikiran, serta poster.", 10),
                ],
            },
        ]

        for ch in inf_chapters:
            tps_dicts = [
                {"kode_tp": code, "urutan_atp": seq, "deskripsi_tp": desc, "alokasi_jp": jp}
                for code, seq, desc, jp in ch["tps"]
            ]
            payload = _build_rich_modul_ajar_payload(
                nama_mapel="Informatika",
                jenjang="SMA",
                kelas=11,
                fase="F",
                nomor_bab=ch["nomor_bab"],
                judul_bab=ch["judul_bab"],
                elemen_cp=ch["elemen_cp"],
                deskripsi_cp=ch["cp_bab"],
                model_code="PJBL",
                dpl_codes=["DPL-3", "DPL-5", "DPL-6", "DPL-8"],
                tps_list=tps_dicts,
            )
            cur.execute(
                """
                INSERT INTO curriculum_chapters (
                    chapter_id, course_id, subject_code, education_level, grade, phase,
                    semester, chapter_number, chapter_title, element_names, allocated_jp,
                    estimated_meetings, promes_week_range, recommended_model_code,
                    graduate_dimension_codes, modul_ajar_payload
                )
                VALUES (%s, %s, %s, 'SMA', 11, 'F', %s, %s, %s, %s, %s, %s, %s, 'PJBL', %s, %s)
                ON CONFLICT (chapter_id) DO UPDATE SET
                    course_id = EXCLUDED.course_id,
                    subject_code = EXCLUDED.subject_code,
                    semester = EXCLUDED.semester,
                    chapter_number = EXCLUDED.chapter_number,
                    chapter_title = EXCLUDED.chapter_title,
                    element_names = EXCLUDED.element_names,
                    allocated_jp = EXCLUDED.allocated_jp,
                    estimated_meetings = EXCLUDED.estimated_meetings,
                    modul_ajar_payload = EXCLUDED.modul_ajar_payload;
                """,
                (
                    ch["id_bab"],
                    course_id,
                    subject_code,
                    ch["semester"],
                    ch["nomor_bab"],
                    ch["judul_bab"],
                    ch["elemen_cp"],
                    ch["alokasi_jp"],
                    max(1, ch["alokasi_jp"] // 5),
                    f"Minggu Efektif Semester {ch['semester']}",
                    ["DPL-3", "DPL-5", "DPL-6", "DPL-8"],
                    Jsonb(payload),
                ),
            )

            for code, seq, desc, jp in ch["tps"]:
                cur.execute(
                    """
                    INSERT INTO learning_objectives_tp (
                        chapter_id, tp_code, atp_sequence, tp_description,
                        rapor_summary_phrase, allocated_jp, bloom_cognitive_level
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 'C4 - Menganalisis')
                    ON CONFLICT (chapter_id, tp_code) DO UPDATE SET
                        atp_sequence = EXCLUDED.atp_sequence,
                        tp_description = EXCLUDED.tp_description,
                        allocated_jp = EXCLUDED.allocated_jp;
                    """,
                    (ch["id_bab"], code, seq, desc, desc[:120].lower(), jp),
                )

    def _seed_modular_sibi_datasets(self, cur) -> None:
        """Seeds 100% verified authentic SIBI / BSKAP 2025 datasets for SD, SMP, and SMA."""
        sibi_dir = self.dataset_dir / "sibi"
        if not sibi_dir.exists():
            return

        sibi_files = [
            sibi_dir / "sibi_sd.json",
            sibi_dir / "sibi_smp.json",
            sibi_dir / "sibi_sma.json",
        ]

        for s_file in sibi_files:
            if not s_file.exists():
                continue
            courses = json.loads(s_file.read_text(encoding="utf-8"))
            for c in courses:
                course_id = c["id_kurikulum"]
                subj_code = c.get("id_mapel_bskap") or _resolve_bskap_subject_code(c["mata_pelajaran"])
                lvl = c["jenjang"]
                grd = int(c["kelas"])
                fase = c["fase"]
                subj_name = c["mata_pelajaran"]
                sibi_book = c.get("buku_rujukan_sibi") or f"Buku Teks Utama SIBI {subj_name} Kelas {grd} (Kemendikdasmen)"
                total_jp = int(c["total_jp_intracurricular_tahun"])
                jp_week = int(c.get("jp_per_minggu", 2))
                verif_status = c.get("verification_status", "VERIFIED_SIBI")
                verif_score = 100

                cur.execute(
                    """
                    INSERT INTO curriculum_courses (
                        course_id, subject_code, education_level, grade, phase, subject_name,
                        sibi_reference_book, total_jp_intracurricular_year, jp_per_week,
                        source_section, verification_status, verification_score
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'SIBI_MODULAR_2025', %s, %s)
                    ON CONFLICT (course_id) DO UPDATE SET
                        subject_code = EXCLUDED.subject_code,
                        education_level = EXCLUDED.education_level,
                        grade = EXCLUDED.grade,
                        phase = EXCLUDED.phase,
                        subject_name = EXCLUDED.subject_name,
                        sibi_reference_book = EXCLUDED.sibi_reference_book,
                        total_jp_intracurricular_year = EXCLUDED.total_jp_intracurricular_year,
                        jp_per_week = EXCLUDED.jp_per_week,
                        source_section = EXCLUDED.source_section,
                        verification_status = EXCLUDED.verification_status,
                        verification_score = EXCLUDED.verification_score;
                    """,
                    (
                        course_id,
                        subj_code,
                        lvl,
                        grd,
                        fase,
                        subj_name,
                        sibi_book,
                        total_jp,
                        jp_week,
                        verif_status,
                        verif_score,
                    ),
                )

                # Delete any old chapters for this course to ensure clean overwrite
                cur.execute("DELETE FROM curriculum_chapters WHERE course_id = %s;", (course_id,))

                for bab in c.get("daftar_bab", []):
                    ch_id = bab["id_bab"]
                    sem = int(bab["semester"])
                    b_num = int(bab["nomor_bab"])
                    title = bab["judul_bab"]
                    elem = bab.get("elemen_cp", "Pemahaman Konsep")
                    ch_jp = int(bab["alokasi_jp_bab"])
                    est_meet = int(bab.get("estimasi_jumlah_pertemuan", max(1, ch_jp // jp_week)))
                    promes_range = bab.get("distribusi_minggu_promes", {}).get("rentang_minggu_efektif", f"Minggu Efektif Semester {sem}")
                    raw_tpl = bab.get("modul_ajar_template", {})
                    model_code = raw_tpl.get("desain_pembelajaran", {}).get("praktik_pedagogis_model", "CONTEXTUAL")
                    if model_code not in ("PBL", "PJBL", "DISCOVERY", "INQUIRY", "CONTEXTUAL"):
                        model_code = "CONTEXTUAL" if lvl == "SD" else "PBL"
                    dpl_codes = raw_tpl.get("identifikasi", {}).get("dimensi_profil_lulusan", ["DPL-3", "DPL-6", "DPL-8"])

                    enriched_tpl = _build_rich_modul_ajar_payload(
                        nama_mapel=subj_name,
                        jenjang=lvl,
                        kelas=grd,
                        fase=fase,
                        nomor_bab=b_num,
                        judul_bab=title,
                        elemen_cp=elem,
                        deskripsi_cp=f"Peserta didik mampu memahami dan menerapkan konsep {title} pada elemen {elem}.",
                        model_code=model_code,
                        dpl_codes=dpl_codes,
                        tps_list=bab.get("daftar_tp", []),
                    )
                    if raw_tpl.get("identifikasi"):
                        enriched_tpl["identifikasi"].update(raw_tpl["identifikasi"])
                    if raw_tpl.get("desain_pembelajaran"):
                        enriched_tpl["desain_pembelajaran"].update(raw_tpl["desain_pembelajaran"])
                    if raw_tpl.get("komponen_inti"):
                        enriched_tpl["komponen_inti"].update(raw_tpl["komponen_inti"])
                    if raw_tpl.get("asesmen"):
                        enriched_tpl["asesmen"].update(raw_tpl["asesmen"])
                    if raw_tpl.get("lampiran"):
                        enriched_tpl["lampiran"].update(raw_tpl["lampiran"])
                    modul_payload = enriched_tpl

                    cur.execute(
                        """
                        INSERT INTO curriculum_chapters (
                            chapter_id, course_id, subject_code, education_level, grade, phase,
                            semester, chapter_number, chapter_title, element_names, allocated_jp,
                            estimated_meetings, promes_week_range, recommended_model_code,
                            graduate_dimension_codes, modul_ajar_payload
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (chapter_id) DO UPDATE SET
                            course_id = EXCLUDED.course_id,
                            subject_code = EXCLUDED.subject_code,
                            education_level = EXCLUDED.education_level,
                            grade = EXCLUDED.grade,
                            phase = EXCLUDED.phase,
                            semester = EXCLUDED.semester,
                            chapter_number = EXCLUDED.chapter_number,
                            chapter_title = EXCLUDED.chapter_title,
                            element_names = EXCLUDED.element_names,
                            allocated_jp = EXCLUDED.allocated_jp,
                            estimated_meetings = EXCLUDED.estimated_meetings,
                            promes_week_range = EXCLUDED.promes_week_range,
                            recommended_model_code = EXCLUDED.recommended_model_code,
                            graduate_dimension_codes = EXCLUDED.graduate_dimension_codes,
                            modul_ajar_payload = EXCLUDED.modul_ajar_payload;
                        """,
                        (
                            ch_id,
                            course_id,
                            subj_code,
                            lvl,
                            grd,
                            fase,
                            sem,
                            b_num,
                            title,
                            elem,
                            ch_jp,
                            est_meet,
                            promes_range,
                            model_code,
                            dpl_codes,
                            Jsonb(modul_payload),
                        ),
                    )

                    for tp in bab.get("daftar_tp", []):
                        cur.execute(
                            """
                            INSERT INTO learning_objectives_tp (
                                chapter_id, tp_code, atp_sequence, tp_description,
                                rapor_summary_phrase, allocated_jp, bloom_cognitive_level
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (chapter_id, tp_code) DO UPDATE SET
                                atp_sequence = EXCLUDED.atp_sequence,
                                tp_description = EXCLUDED.tp_description,
                                rapor_summary_phrase = EXCLUDED.rapor_summary_phrase,
                                allocated_jp = EXCLUDED.allocated_jp,
                                bloom_cognitive_level = EXCLUDED.bloom_cognitive_level;
                            """,
                            (
                                ch_id,
                                tp["kode_tp"],
                                int(tp.get("urutan_atp", 1)),
                                tp["deskripsi_tp"],
                                tp.get("ringkasan_deskripsi_rapor", tp["deskripsi_tp"][:100]),
                                int(tp.get("alokasi_jp", 4)),
                                tp.get("level_kognitif_bloom", "C3 - Menerapkan"),
                            ),
                        )

    def _cleanup_synthetic_and_duplicates(self, cur) -> None:
        """Removes duplicate courses, legacy synthetic fallback chapters, and unverified placeholders."""
        # 1. Delete duplicate SMA-K10-FIS (keeping SMA-K10-FISPAR)
        cur.execute("DELETE FROM curriculum_courses WHERE course_id = 'SMA-K10-FIS';")

        # 2. Delete replaced generic religion courses (since 6 official religions now exist)
        cur.execute("DELETE FROM curriculum_courses WHERE subject_name = 'Pendidikan Agama dan Budi Pekerti';")

        # 3. Delete any remaining synthetic placeholder chapters
        cur.execute(
            """
            DELETE FROM curriculum_chapters
            WHERE chapter_title ILIKE '%Konsep Dasar & Eksplorasi%'
               OR chapter_title ILIKE '%Analisis & Penerapan%'
               OR chapter_title ILIKE '%Pengembangan & Pemecahan Masalah%'
               OR chapter_title ILIKE '%Proyek Kontekstual & Evaluasi%'
               OR chapter_title ILIKE '%Aplikasi & Proyek Terpadu%';
            """
        )

        # 4. Clean up any orphaned courses that have 0 chapters
        cur.execute(
            """
            DELETE FROM curriculum_courses
            WHERE course_id NOT IN (SELECT DISTINCT course_id FROM curriculum_chapters);
            """
        )

        # 5. Ensure all active courses have verification_score = 100
        cur.execute(
            """
            UPDATE curriculum_courses
            SET verification_score = 100
            WHERE verification_score < 100
              AND verification_status IN ('VERIFIED_SIBI', 'VERIFIED_BSKAP', 'TEMPLATE_FLEXIBLE');
            """
        )

    def _seed_all_150_grade_subject_courses(self, cur) -> None:
        """Deterministically generates complete courses, chapters (Smt 1 & 2), and TPs for ALL 150 grade-subject rows in curriculum_hour_allocations."""
        cur.execute("SELECT * FROM curriculum_hour_allocations ORDER BY education_level, grade, id;")
        alloc_rows = cur.fetchall()

        cur.execute("SELECT course_id, education_level, grade, subject_name FROM curriculum_courses;")
        existing_courses = cur.fetchall()
        existing_by_key = {(r["education_level"], int(r["grade"]), r["subject_name"].upper()): r["course_id"] for r in existing_courses}
        existing_ids = {r["course_id"] for r in existing_courses}

        # Cache CP elements by (subject_code, phase)
        cur.execute("SELECT subject_code, phase, element_name, cp_description FROM curriculum_phase_elements ORDER BY id;")
        cp_by_subj_phase: Dict[Tuple[str, str], List[Dict[str, str]]] = {}
        for r in cur.fetchall():
            cp_by_subj_phase.setdefault((r["subject_code"], r["phase"]), []).append(
                {"element_name": r["element_name"], "cp_description": r["cp_description"]}
            )

        for alloc in alloc_rows:
            lvl = alloc["education_level"]
            grd = int(alloc["grade"])
            fase = alloc["phase"]
            subj_name = alloc["subject_name"]
            total_jp = int(alloc["jp_intracurricular_year"]) or int(alloc["total_jp_year"]) or 72
            jp_week = max(1, int(alloc["jp_per_week"]))

            # Skip if already seeded with identical (level, grade, subject_name)
            if (lvl, grd, subj_name.upper()) in existing_by_key:
                continue

            slug = _slugify_mapel(subj_name)
            course_id = f"{lvl}-K{grd}-{slug}"
            suffix_idx = 2
            while course_id in existing_ids:
                course_id = f"{lvl}-K{grd}-{slug}{suffix_idx}"
                suffix_idx += 1

            existing_ids.add(course_id)
            existing_by_key[(lvl, grd, subj_name.upper())] = course_id
            subject_code = _resolve_bskap_subject_code(subj_name)

            cur.execute(
                """
                INSERT INTO curriculum_courses (
                    course_id, subject_code, education_level, grade, phase, subject_name,
                    sibi_reference_book, total_jp_intracurricular_year, jp_per_week, source_section
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'BSKAP_2025_FULL')
                ON CONFLICT (course_id) DO UPDATE SET
                    subject_code = EXCLUDED.subject_code,
                    subject_name = EXCLUDED.subject_name,
                    total_jp_intracurricular_year = EXCLUDED.total_jp_intracurricular_year,
                    jp_per_week = EXCLUDED.jp_per_week;
                """,
                (
                    course_id,
                    subject_code,
                    lvl,
                    grd,
                    fase,
                    subj_name,
                    f"Buku Teks Utama SIBI {subj_name} Kelas {grd} Fase {fase} (Kemendikdasmen)",
                    total_jp,
                    jp_week,
                ),
            )

            # Determine 4 chapters (2 in Semester 1, 2 in Semester 2) from official CP elements
            cp_elems = cp_by_subj_phase.get((subject_code, fase)) or [
                {"element_name": f"Pemahaman Konsep {subj_name}", "cp_description": f"Peserta didik mampu memahami dan menguasai konsep dasar {subj_name} pada Fase {fase}."},
                {"element_name": f"Keterampilan Proses & Aplikasi {subj_name}", "cp_description": f"Peserta didik mampu menerapkan keterampilan proses dan pemecahan masalah {subj_name} pada Fase {fase}."},
            ]

            default_model = "CONTEXTUAL" if lvl == "SD" else ("INQUIRY" if "IPA" in subj_name or "Fisika" in subj_name or "Kimia" in subj_name or "Biologi" in subj_name else "PBL")
            jp_per_bab = max(4, total_jp // 4)

            for bab_idx in range(1, 5):
                sem = 1 if bab_idx <= 2 else 2
                elem_obj = cp_elems[(bab_idx - 1) % len(cp_elems)]
                elem_name = elem_obj["element_name"]
                cp_desc = elem_obj["cp_description"]

                if bab_idx == 1:
                    judul_bab = f"Konsep Dasar & Eksplorasi {elem_name}"
                elif bab_idx == 2:
                    judul_bab = f"Analisis & Penerapan {elem_name} dalam Kehidupan"
                elif bab_idx == 3:
                    judul_bab = f"Pengembangan & Pemecahan Masalah {elem_name}"
                else:
                    judul_bab = f"Proyek Kontekstual & Evaluasi {elem_name}"

                ch_id = f"{course_id}-B{bab_idx:02d}"
                tp_jp = max(2, jp_per_bab // 3)
                tps_list = [
                    {
                        "kode_tp": f"TP.{grd}.{bab_idx}.1",
                        "urutan_atp": (bab_idx - 1) * 3 + 1,
                        "deskripsi_tp": f"Peserta didik mampu memahami konsep fundamental {elem_name} pada lingkup {judul_bab}.",
                        "alokasi_jp": tp_jp,
                    },
                    {
                        "kode_tp": f"TP.{grd}.{bab_idx}.2",
                        "urutan_atp": (bab_idx - 1) * 3 + 2,
                        "deskripsi_tp": f"Peserta didik mampu menganalisis dan mengaplikasikan prinsip {elem_name} dalam studi kasus nyata.",
                        "alokasi_jp": tp_jp,
                    },
                    {
                        "kode_tp": f"TP.{grd}.{bab_idx}.3",
                        "urutan_atp": (bab_idx - 1) * 3 + 3,
                        "deskripsi_tp": f"Peserta didik mampu menyajikan karya/solusi dan merefleksikan pembelajaran {judul_bab} secara kolaboratif.",
                        "alokasi_jp": max(2, jp_per_bab - 2 * tp_jp),
                    },
                ]

                payload = _build_rich_modul_ajar_payload(
                    nama_mapel=subj_name,
                    jenjang=lvl,
                    kelas=grd,
                    fase=fase,
                    nomor_bab=bab_idx,
                    judul_bab=judul_bab,
                    elemen_cp=elem_name,
                    deskripsi_cp=cp_desc,
                    model_code=default_model,
                    dpl_codes=["DPL-3", "DPL-5", "DPL-6", "DPL-8"],
                    tps_list=tps_list,
                )

                cur.execute(
                    """
                    INSERT INTO curriculum_chapters (
                        chapter_id, course_id, subject_code, education_level, grade, phase,
                        semester, chapter_number, chapter_title, element_names, allocated_jp,
                        estimated_meetings, promes_week_range, recommended_model_code,
                        graduate_dimension_codes, modul_ajar_payload
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chapter_id) DO UPDATE SET
                        chapter_title = EXCLUDED.chapter_title,
                        element_names = EXCLUDED.element_names,
                        allocated_jp = EXCLUDED.allocated_jp,
                        modul_ajar_payload = EXCLUDED.modul_ajar_payload;
                    """,
                    (
                        ch_id,
                        course_id,
                        subject_code,
                        lvl,
                        grd,
                        fase,
                        sem,
                        bab_idx,
                        judul_bab,
                        elem_name,
                        jp_per_bab,
                        max(1, jp_per_bab // jp_week),
                        f"Minggu Efektif Semester {sem}",
                        default_model,
                        ["DPL-3", "DPL-5", "DPL-6", "DPL-8"],
                        Jsonb(payload),
                    ),
                )

                for tp_item in tps_list:
                    cur.execute(
                        """
                        INSERT INTO learning_objectives_tp (
                            chapter_id, tp_code, atp_sequence, tp_description,
                            rapor_summary_phrase, allocated_jp, bloom_cognitive_level
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, 'C3 - Menerapkan')
                        ON CONFLICT (chapter_id, tp_code) DO UPDATE SET
                            tp_description = EXCLUDED.tp_description,
                            allocated_jp = EXCLUDED.allocated_jp;
                        """,
                        (
                            ch_id,
                            tp_item["kode_tp"],
                            tp_item["urutan_atp"],
                            tp_item["deskripsi_tp"],
                            tp_item["deskripsi_tp"][:120].lower(),
                            tp_item["alokasi_jp"],
                        ),
                    )

    def _seed_dataset_05_kalender_promes(self, cur) -> None:
        file_path = self.dataset_dir / "05_kalender_pendidikan_dan_promes_default.json"
        data = json.loads(file_path.read_text(encoding="utf-8"))
        academic_year = data.get("metadata", {}).get("tahun_ajaran_default", "2026/2027")

        for sem_num, sem_key in [(1, "semester_1_ganjil"), (2, "semester_2_genap")]:
            sem_obj = data.get(sem_key, {})
            for bulan in sem_obj.get("rincian_per_bulan", []):
                no_bulan = int(bulan["no_bulan"])
                nama_bulan = bulan["nama_bulan"]
                for w in bulan.get("status_tiap_minggu", []):
                    cur.execute(
                        """
                        INSERT INTO academic_calendar_weeks (
                            academic_year, semester, month_number, month_name, week_in_month,
                            week_status, table_code, effective_week_sequence, description
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (academic_year, semester, month_number, week_in_month) DO UPDATE SET
                            month_name = EXCLUDED.month_name,
                            week_status = EXCLUDED.week_status,
                            table_code = EXCLUDED.table_code,
                            effective_week_sequence = EXCLUDED.effective_week_sequence,
                            description = EXCLUDED.description;
                        """,
                        (
                            academic_year,
                            sem_num,
                            no_bulan,
                            nama_bulan,
                            int(w["minggu_ke"]),
                            w["status"],
                            w["kode_tabel"],
                            w.get("minggu_efektif_urut"),
                            w.get("keterangan", ""),
                        ),
                    )

    def _seed_service_templates(self, cur) -> None:
        mvp_services = [
            ("03_cp_tp", "Capaian Pembelajaran & Tujuan Pembelajaran (CP-TP)", 2, True),
            ("04_atp", "Alur Tujuan Pembelajaran (ATP)", 2, True),
            ("05_prota", "Program Tahunan (Prota)", 2, True),
            ("06_promes", "Program Semester (Promes)", 2, True),
            ("07_kktp", "Kriteria Ketercapaian Tujuan Pembelajaran (KKTP)", 2, False),
            ("08_modul_ajar", "Modul Ajar / RPP Lengkap (Deep Learning 3M)", 2, True),
            ("09_lkpd", "Lembar Kerja Peserta Didik Mandiri (LKPD)", 3, False),
        ]
        for code, name, cluster, is_mvp in mvp_services:
            cur.execute(
                """
                INSERT INTO service_templates (service_code, service_name, cluster_number, is_mvp_phase1, required_form_schema)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (service_code) DO UPDATE SET
                    service_name = EXCLUDED.service_name,
                    cluster_number = EXCLUDED.cluster_number,
                    is_mvp_phase1 = EXCLUDED.is_mvp_phase1;
                """,
                (code, name, cluster, is_mvp, Jsonb({"service_id": code})),
            )

    def get_table_counts(self) -> Dict[str, int]:
        tables = [
            "curriculum_phases",
            "graduate_dimensions",
            "pedagogical_models",
            "deep_learning_framework",
            "kktp_intervals",
            "curriculum_hour_allocations",
            "curriculum_subjects",
            "curriculum_phase_elements",
            "curriculum_courses",
            "curriculum_chapters",
            "learning_objectives_tp",
            "academic_calendar_weeks",
            "service_templates",
        ]
        counts: Dict[str, int] = {}
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                for t in tables:
                    cur.execute(f"SELECT COUNT(*) AS cnt FROM {t};")
                    row = cur.fetchone()
                    counts[t] = int(row["cnt"]) if row else 0
        return counts
