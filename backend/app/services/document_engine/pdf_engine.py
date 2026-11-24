import re
from typing import Optional, List, Dict, Any, Tuple
from fpdf import FPDF
from fpdf.fonts import FontFace

from app.core.exceptions import DocumentGenerationError
from app.models.curriculum import CurriculumSubject, ChapterTopic, LearningObjective
from app.models.teacher import TeacherProfile
from app.schemas.generation import DocumentGenerateRequest, ServiceIdEnum
from app.services.document_engine.base_engine import DocumentEngine
from app.services.document_engine.question_blueprint import QuestionBlueprintEngine

# Official styling constants for Table Headers & Accents (BSKAP / GuruDok Standard)
HEADER_STYLE = FontFace(emphasis="BOLD", fill_color=(217, 226, 243))  # #D9E2F3
BOLD_STYLE = FontFace(emphasis="BOLD")


def _resolve_effective_tps(chapter: Optional[ChapterTopic], request: DocumentGenerateRequest) -> List[LearningObjective]:
    """Returns customized TPs if teacher provided custom_overrides (custom_tps or tujuan_pembelajaran_custom), otherwise chapter's default TPs."""
    ov = request.custom_overrides
    custom_list = (ov.custom_tps if (ov and ov.custom_tps) else None) or (ov.tujuan_pembelajaran_custom if (ov and ov.tujuan_pembelajaran_custom) else None)
    if custom_list:
        return [
            LearningObjective(
                code=item.code,
                deskripsi=item.deskripsi,
                alokasi_jp=item.alokasi_jp,
                urutan_atp=idx,
            )
            for idx, item in enumerate(custom_list, start=1)
        ]
    return list(chapter.tujuan_pembelajaran) if chapter else []


def _resolve_effective_alokasi_jp(chapter: Optional[ChapterTopic], request: DocumentGenerateRequest) -> int:
    """Returns customized JP if teacher provided custom_overrides (custom_alokasi_jp or alokasi_jp_bab), otherwise chapter's default JP."""
    ov = request.custom_overrides
    if ov:
        if ov.custom_alokasi_jp is not None:
            return ov.custom_alokasi_jp
        if ov.alokasi_jp_bab is not None:
            return ov.alokasi_jp_bab
    if chapter:
        return chapter.calculate_total_jp()
    return 16


def _split_numbered_aims(aims_text: str, subject_name: str) -> List[str]:
    """Splits a BSKAP aims paragraph into clean numbered objectives for the Tujuan table."""
    if not aims_text:
        return [
            f"Menguasai konsep fundamental dan keterampilan proses pada mata pelajaran {subject_name}.",
            f"Mengembangkan kemampuan bernalar kritis, kreatif, mandiri, dan kolaboratif melalui {subject_name}.",
            f"Menerapkan pengetahuan {subject_name} untuk memecahkan masalah kontekstual dalam kehidupan sehari-hari.",
        ]
    parts = re.split(r"(?:\d+\.\s+)", aims_text)
    cleaned = [p.strip().rstrip(";") for p in parts[1:] if len(p.strip()) > 10]
    if not cleaned:
        cleaned = [s.strip() for s in aims_text.split(";") if len(s.strip()) > 15]
    return cleaned or [aims_text]


def _ascii_safe(text: Any) -> str:
    """Normalizes Unicode punctuation into Latin-1 safe characters for built-in PDF fonts."""
    if text is None:
        return "-"
    s = str(text)
    replacements = {
        "—": "-",
        "–": "-",
        "―": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "*",
        "…": "...",
        "×": "x",
        "≥": ">=",
        "≤": "<=",
        "°": " deg",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "ignore").decode("latin-1")


def _resolve_effective_cp_elements(subject: CurriculumSubject, request: DocumentGenerateRequest) -> List[Dict[str, str]]:
    """Resolves customized Capaian Pembelajaran (CP) elements if teacher provided custom_elemen_cp, otherwise BSKAP 046/2025 official elements."""
    ov = request.custom_overrides
    if ov and ov.custom_elemen_cp and len(ov.custom_elemen_cp) > 0:
        return [
            {
                "kode_elemen": item.kode_elemen,
                "nama_elemen": item.nama_elemen,
                "deskripsi_cp": item.deskripsi_cp,
            }
            for item in ov.custom_elemen_cp
        ]
    elems = getattr(subject, "elemen_cp_resmi", []) or []
    if elems:
        return [
            {
                "kode_elemen": e.get("kode_elemen", f"EL-{i:02d}"),
                "nama_elemen": e.get("nama_elemen", "-"),
                "deskripsi_cp": e.get("deskripsi_cp", "-"),
            }
            for i, e in enumerate(elems, start=1)
        ]
    return [
        {
            "kode_elemen": "EL-01",
            "nama_elemen": "Pemahaman Konsep",
            "deskripsi_cp": f"Peserta didik mampu memahami dan menerapkan konsep esensial {subject.nama_mapel} secara mendalam.",
        },
        {
            "kode_elemen": "EL-02",
            "nama_elemen": "Keterampilan Proses",
            "deskripsi_cp": f"Peserta didik mampu mengamati, menganalisis, dan memecahkan masalah kontekstual {subject.nama_mapel}.",
        },
    ]


class GuruDokPDF(FPDF):
    """Subclass of FPDF providing standardized page numbering, margins, and optional preview watermark."""

    def __init__(self, *args, preview_watermark: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.preview_watermark = preview_watermark

    def header(self):
        if not self.preview_watermark:
            return
        with self.local_context():
            self.set_font("Helvetica", "B", 42)
            self.set_text_color(226, 232, 240)
            cx = self.w / 2.0
            cy = self.h / 2.0
            with self.rotation(35, x=cx, y=cy):
                text = "PREVIEW DOKUMEN"
                tw = self.get_string_width(text)
                self.text(cx - (tw / 2.0), cy, text)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8.5)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f"Halaman {self.page_no()}", align="R")


class PdfDocumentEngine(DocumentEngine):
    """Engine responsible for generating official PDF (.pdf) documents on F4/A4 paper with bordered tables."""

    def generate(
        self,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
        raw_template: Optional[dict] = None,
    ) -> bytes:
        pdf_bytes, _ = self.generate_with_page_count(
            request=request,
            subject=subject,
            chapter=chapter,
            teacher=teacher,
            raw_template=raw_template,
            preview_watermark=False,
        )
        return pdf_bytes

    def generate_with_page_count(
        self,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
        raw_template: Optional[dict] = None,
        preview_watermark: bool = False,
    ) -> Tuple[bytes, int]:
        try:
            is_landscape = request.service_id in (
                ServiceIdEnum.PROMES,
                ServiceIdEnum.PRESENSI,
                ServiceIdEnum.DAFTAR_NILAI,
            )
            orientation = "L" if is_landscape else "P"
            if request.paper_size.value == "F4":
                page_format = (self.F4_WIDTH_MM, self.F4_HEIGHT_MM)
            else:
                page_format = (self.A4_WIDTH_MM, self.A4_HEIGHT_MM)

            pdf = GuruDokPDF(
                orientation=orientation,
                unit="mm",
                format=page_format,
                preview_watermark=preview_watermark,
            )
            pdf.set_margins(left=self.MARGIN_LEFT_MM, top=self.MARGIN_TOP_MM, right=self.MARGIN_RIGHT_MM)
            pdf.set_auto_page_break(auto=True, margin=self.MARGIN_BOTTOM_MM)
            pdf.add_page()

            # 1. KOP Surat Sekolah
            self._add_kop_surat(pdf, teacher)

            # 2. Content by Service ID
            tpl = raw_template or (chapter.modul_ajar_template if chapter else {}) or {}
            if request.service_id == ServiceIdEnum.MODUL_AJAR:
                self._build_modul_ajar(pdf, request, subject, chapter, teacher, tpl)
            elif request.service_id == ServiceIdEnum.ATP:
                self._build_atp(pdf, request, subject, chapter)
            elif request.service_id == ServiceIdEnum.CP_TP:
                self._build_cp_tp(pdf, request, subject, chapter)
            elif request.service_id == ServiceIdEnum.PROTA:
                self._build_prota(pdf, request, subject, chapter)
            elif request.service_id == ServiceIdEnum.PROMES:
                self._build_promes(pdf, request, subject, chapter, tpl)
            elif request.service_id == ServiceIdEnum.KKTP:
                self._build_kktp(pdf, request, subject, chapter)
            elif request.service_id == ServiceIdEnum.LKPD:
                self._build_lkpd(pdf, request, subject, chapter, tpl)
            elif request.service_id in (ServiceIdEnum.KUIS, ServiceIdEnum.SUMATIF_BAB, ServiceIdEnum.STS_SAS):
                self._build_exam_document(pdf, request, subject, chapter)
            elif request.service_id == ServiceIdEnum.PRESENSI:
                self._build_presensi(pdf, request, subject, teacher)
            elif request.service_id == ServiceIdEnum.DAFTAR_NILAI:
                self._build_daftar_nilai(pdf, request, subject, teacher)

            # 3. Lembar Pengesahan
            self._add_lembar_pengesahan(pdf, teacher)
            page_count = pdf.page_no()
            return bytes(pdf.output()), page_count

        except Exception as e:
            raise DocumentGenerationError(f"Failed to generate PDF document: {str(e)}")

    def _add_kop_surat(self, pdf: FPDF, teacher: TeacherProfile) -> None:
        kop = teacher.get_formatted_kop()
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.cell(0, 5, _ascii_safe(f"PEMERINTAH {kop['kabupaten_kota'].upper()} - DINAS PENDIDIKAN"), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 6, _ascii_safe(kop["nama_sekolah"]), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(
            0,
            5,
            _ascii_safe(f"NPSN: {kop['npsn']} | {kop['kabupaten_kota']}, Provinsi {kop['provinsi']}"),
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
        pdf.ln(1)
        y = pdf.get_y()
        pdf.set_line_width(0.7)
        pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
        pdf.set_line_width(0.2)
        pdf.line(pdf.l_margin, y + 0.8, pdf.w - pdf.r_margin, y + 0.8)
        pdf.ln(5)

    def _add_doc_title(self, pdf: FPDF, title: str, subtitle: str) -> None:
        pdf.set_font("Helvetica", "B", 11.5)
        pdf.cell(0, 6, _ascii_safe(title), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(0, 5, _ascii_safe(subtitle), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(3)

    def _add_section_title(self, pdf: FPDF, title: str) -> None:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(29, 78, 216)
        pdf.cell(0, 5.5, _ascii_safe(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(15, 23, 42)
        pdf.ln(1)

    def _build_modul_ajar(
        self,
        pdf: FPDF,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
        tpl: dict,
    ) -> None:
        ch = chapter or (subject.bab_list[0] if subject.bab_list else None)
        ov = request.custom_overrides
        ident = tpl.get("identifikasi", {}) if isinstance(tpl, dict) else {}
        desain = tpl.get("desain_pembelajaran", {}) if isinstance(tpl, dict) else {}
        inti = tpl.get("komponen_inti", {}) if isinstance(tpl, dict) else {}
        asesmen = tpl.get("asesmen", {}) if isinstance(tpl, dict) else {}
        lampiran = tpl.get("lampiran", {}) if isinstance(tpl, dict) else {}

        # Document Header Title
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "MODUL AJAR DEEP LEARNING", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "B", 10.5)
        ch_title = (ch.judul_bab if ch else subject.nama_mapel).upper()
        pdf.cell(0, 5, _ascii_safe(f"{subject.nama_mapel.upper()} - BAB {ch.nomor_bab if ch else 1}: {ch_title}"), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(3)

        # A. Identitas Modul (Bordered Table)
        self._add_section_title(pdf, "A. Identitas Modul")
        alokasi_jp = _resolve_effective_alokasi_jp(ch, request)
        durasi_menit = getattr(subject, "durasi_1_jp_menit", 40)
        jp_per_minggu = max(1, subject.alokasi_jp_mingguan)
        tps_effective = _resolve_effective_tps(ch, request)
        pertemuan_count = max(len(tps_effective), max(1, round(alokasi_jp / jp_per_minggu)))

        id_rows = [
            ("Nama Penyusun", f"{teacher.nama_guru} (NIP. {teacher.nip_guru})"),
            ("Institusi / Sekolah", teacher.nama_sekolah),
            ("Tahun Penyusunan / Semester", f"Tahun Ajaran 2025/2026 / Semester {request.semester} ({'Ganjil' if request.semester == 1 else 'Genap'})"),
            ("Jenjang / Fase / Kelas", f"{subject.jenjang} / Fase {subject.fase} / Kelas {subject.kelas}"),
            ("Mata Pelajaran", subject.nama_mapel),
            ("Bab / Materi Pokok", f"Bab {ch.nomor_bab if ch else 1}: {ch.judul_bab if ch else subject.nama_mapel}"),
            ("Alokasi Waktu", f"{alokasi_jp} JP ({pertemuan_count} Pertemuan x {jp_per_minggu} JP @ {durasi_menit} Menit)"),
        ]
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(45, 115), line_height=5.2, first_row_as_headings=False) as table:
            for label, val in id_rows:
                row = table.row()
                row.cell(_ascii_safe(label), style=BOLD_STYLE)
                row.cell(_ascii_safe(val))
        pdf.ln(2)

        # B. Identifikasi Kesiapan Peserta Didik
        self._add_section_title(pdf, "B. Identifikasi Kesiapan Peserta Didik")
        kesiapan_txt = (ov.kesiapan_murid if (ov and ov.kesiapan_murid) else None) or ident.get(
            "kesiapan_murid",
            f"Peserta didik Kelas {subject.kelas} (Fase {subject.fase}) umumnya telah memiliki pengetahuan dan pengalaman awal yang berkaitan dengan materi {ch.judul_bab if ch else subject.nama_mapel}.",
        )
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 4.8, _ascii_safe(kesiapan_txt), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

        # C. Karakteristik Materi Pelajaran
        self._add_section_title(pdf, "C. KARAKTERISTIK MATERI PELAJARAN")
        karakteristik_txt = (ov.karakteristik_materi if (ov and ov.karakteristik_materi) else None) or ident.get(
            "karakteristik_materi",
            f"Materi '{ch.judul_bab if ch else subject.nama_mapel}' pada Bab ini berfokus pada penguasaan konsep, pengetahuan prosedural, dan metakognitif yang aplikatif.",
        )
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 4.8, _ascii_safe(karakteristik_txt), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

        # D. Dimensi Profil Lulusan Pembelajaran (Bordered Table with Header Fill)
        self._add_section_title(pdf, "D. Dimensi Profil Lulusan Pembelajaran")
        active_dimensions = (ch.dimensi_profil_lulusan if ch else None) or ["Penalaran Kritis", "Kreativitas", "Kolaborasi", "Kemandirian"]
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(45, 115), line_height=5.2) as table:
            hdr = table.row(style=HEADER_STYLE)
            hdr.cell("Dimensi Profil Lulusan")
            hdr.cell("Implementasi pada Pembelajaran Bab Ini")
            for dim in active_dimensions:
                r = table.row()
                r.cell(_ascii_safe(dim), style=BOLD_STYLE)
                r.cell(_ascii_safe(f"Dikembangkan melalui aktivitas diskusi, eksplorasi konsep {ch.judul_bab if ch else subject.nama_mapel}, dan refleksi pemecahan masalah."))
        pdf.ln(2)

        # E. DESAIN PEMBELAJARAN (Bordered Table)
        self._add_section_title(pdf, "DESAIN PEMBELAJARAN")
        cp_bab_str = desain.get("capaian_pembelajaran_bab") or (
            subject.elemen_cp_resmi[0]["deskripsi_cp"] if getattr(subject, "elemen_cp_resmi", None) else f"Peserta didik mampu menguasai materi {ch.judul_bab if ch else subject.nama_mapel}."
        )
        elemen_name = ch.elemen_cp if ch else "Pemahaman Konsep"
        lintas_txt = (ov.lintas_disiplin_ilmu if (ov and ov.lintas_disiplin_ilmu) else None) or desain.get(
            "lintas_disiplin_ilmu",
            "Bahasa Indonesia (literasi & presentasi); Matematika (logika & analisis); Sains & IPS (konteks nyata).",
        )
        tp_lines = "\n".join(f"{idx}. Pertemuan {idx} [{tp.code}]: {tp.deskripsi} ({tp.alokasi_jp} JP)" for idx, tp in enumerate(tps_effective, start=1))
        topik_txt = (ov.topik_kontekstual if (ov and ov.topik_kontekstual) else None) or desain.get(
            "topik_pembelajaran_kontekstual",
            f"Penerapan materi {ch.judul_bab if ch else subject.nama_mapel} dalam memecahkan masalah kontekstual kehidupan sehari-hari.",
        )
        pemantik_list = (ov.pertanyaan_pemantik if (ov and ov.pertanyaan_pemantik) else None) or inti.get("pertanyaan_pemantik", [
            f"Bagaimana konsep {ch.judul_bab if ch else subject.nama_mapel} dapat membantu menyelesaikan persoalan di dunia nyata?"
        ])
        model_pedagogis = request.model_pembelajaran or "Inquiry Based Learning (Mendalam/DL)"

        des_rows = [
            ("A. Capaian Pembelajaran (CP)", f"Elemen {elemen_name}: {cp_bab_str}"),
            ("B. LINTAS DISIPLIN ILMU", lintas_txt),
            ("C. Tujuan Pembelajaran (TP)", tp_lines),
            ("D. TOPIK PEMBELAJARAN KONTEKSTUAL", topik_txt),
            ("E. Kerangka Pembelajaran", f"Model Pedagogis: {model_pedagogis}\nPertanyaan Pemantik: " + " | ".join(pemantik_list)),
        ]
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(45, 115), line_height=5.2, first_row_as_headings=False) as table:
            for lbl, val in des_rows:
                r = table.row()
                r.cell(_ascii_safe(lbl), style=BOLD_STYLE)
                r.cell(_ascii_safe(val))
        pdf.ln(2)

        # F. LANGKAH-LANGKAH PEMBELAJARAN BERDIFERENSIASI (DEEP LEARNING 3M)
        self._add_section_title(pdf, "F. LANGKAH-LANGKAH PEMBELAJARAN BERDIFERENSIASI (PENDEKATAN DEEP LEARNING 3M)")
        pb = inti.get("pengalaman_belajar", {})
        memahami_steps = (ov.langkah_memahami if (ov and ov.langkah_memahami) else None) or (ov.langkah_inti_memahami if (ov and ov.langkah_inti_memahami) else None) or pb.get("tahap_memahami", [f"Peserta didik mengeksplorasi konsep dan literatur terkait {ch.judul_bab if ch else subject.nama_mapel}."])
        mengaplikasi_steps = (ov.langkah_mengaplikasi if (ov and ov.langkah_mengaplikasi) else None) or (ov.langkah_inti_mengaplikasi if (ov and ov.langkah_inti_mengaplikasi) else None) or pb.get("tahap_mengaplikasi", [f"Peserta didik bekerja dalam kelompok mengerjakan studi kasus / LKPD tentang {ch.judul_bab if ch else subject.nama_mapel}."])
        merefleksi_steps = (ov.langkah_merefleksi if (ov and ov.langkah_merefleksi) else None) or (ov.langkah_inti_merefleksi if (ov and ov.langkah_inti_merefleksi) else None) or pb.get("tahap_merefleksi", ["Kelompok mempresentasikan hasil karya dan melakukan evaluasi pemahaman bersama guru."])

        for idx, tp in enumerate(tps_effective):
            q_pemantik = pemantik_list[idx % len(pemantik_list)]
            step_m = memahami_steps[idx % len(memahami_steps)]
            step_a = mengaplikasi_steps[idx % len(mengaplikasi_steps)]
            step_r = merefleksi_steps[idx % len(merefleksi_steps)]

            pdf.set_font("Helvetica", size=8.5)
            with pdf.table(col_widths=(45, 115), line_height=5.2) as table:
                hdr = table.row(style=HEADER_STYLE)
                hdr.cell(_ascii_safe(f"PERTEMUAN {idx + 1} - Fokus TP: [{tp.code}] {tp.deskripsi} ({tp.alokasi_jp} JP)"), colspan=2)

                r1 = table.row()
                r1.cell("1. Pendahuluan (15%)", style=BOLD_STYLE)
                r1.cell(_ascii_safe(f"Guru membuka kelas dengan salam, doa, presensi, apersepsi mengaitkan pengalaman nyata siswa dengan topik {ch.judul_bab if ch else subject.nama_mapel}, serta menyampaikan pertanyaan pemantik: \"{q_pemantik}\"."))

                r2 = table.row()
                r2.cell("2. Kegiatan Inti 3M (70%)", style=BOLD_STYLE)
                r2.cell(_ascii_safe(f"* Memahami (Mindful Learning): {step_m}\n* Mengaplikasi (Meaningful Learning): {step_a}\n* Merefleksi (Joyful Learning): {step_r}"))

                r3 = table.row()
                r3.cell("3. Penutup (15%)", style=BOLD_STYLE)
                r3.cell(_ascii_safe(f"Peserta didik bersama guru menyimpulkan poin penting pertemuan {idx + 1}, melakukan refleksi singkat, dan menerima informasi materi berikutnya."))
            pdf.ln(2)

        # G. Asesmen Pembelajaran & Butir Soal (Bordered Table)
        if request.include_asesmen:
            self._add_section_title(pdf, "G. Asesmen Pembelajaran & Butir Soal")
            soal_awal = (ov.soal_asesmen_awal if (ov and ov.soal_asesmen_awal) else None) or asesmen.get("soal_asesmen_awal", [
                f"Apa yang kamu ketahui mengenai konsep {ch.judul_bab if ch else subject.nama_mapel}?",
                "Sebutkan contoh penerapan nyata materi ini di lingkungan sekitarmu!",
            ])
            soal_proses = (ov.soal_asesmen_proses if (ov and ov.soal_asesmen_proses) else None) or asesmen.get("soal_asesmen_proses", [
                f"Kerjakan investigasi kelompok pada LKPD materi {ch.judul_bab if ch else subject.nama_mapel}!",
                "Diskusikan argumen pemecahan masalah dan presentasikan di depan kelas!",
            ])
            soal_akhir = (ov.soal_asesmen_akhir if (ov and ov.soal_asesmen_akhir) else None) or asesmen.get("soal_asesmen_akhir", [
                f"Evaluasi komparatif studi kasus implementasi {ch.judul_bab if ch else subject.nama_mapel}!",
                "Simpulkan solusi optimal berdasarkan hasil analisis data!",
            ])

            pdf.set_font("Helvetica", size=8.5)
            with pdf.table(col_widths=(45, 115), line_height=5.2) as table:
                hdr = table.row(style=HEADER_STYLE)
                hdr.cell("Jenis Asesmen")
                hdr.cell("Teknik & Butir Soal Instrumen")

                r_diag = table.row()
                r_diag.cell("1. Diagnostik (Awal)", style=BOLD_STYLE)
                r_diag.cell(_ascii_safe("Tanya jawab pemantik & kuisioner awal:\n" + "\n".join(f"- {s}" for s in soal_awal)))

                r_form = table.row()
                r_form.cell("2. Formatif (Proses)", style=BOLD_STYLE)
                r_form.cell(_ascii_safe("Observasi kinerja kelompok & LKPD:\n" + "\n".join(f"- {s}" for s in soal_proses)))

                r_sum = table.row()
                r_sum.cell("3. Sumatif (Akhir)", style=BOLD_STYLE)
                r_sum.cell(_ascii_safe("Tes tertulis / unjuk kerja akhir bab:\n" + "\n".join(f"- {s}" for s in soal_akhir)))
            pdf.ln(2)

        # H. Lampiran 1: Lembar Kerja Peserta Didik (LKPD)
        if request.include_lkpd:
            pdf.add_page()
            self._add_section_title(pdf, "H. LAMPIRAN 1: LEMBAR KERJA PESERTA DIDIK (LKPD)")
            lkpd = lampiran.get("lkpd", {})
            judul_lk = (ov.judul_lkpd if (ov and ov.judul_lkpd) else None) or lkpd.get("judul_lkpd") or f"LKPD: {ch_title} (Pendekatan Deep Learning 3M)"
            tujuan_lk = (ov.tujuan_lkpd if (ov and ov.tujuan_lkpd) else None) or lkpd.get("tujuan_aktivitas") or f"Mengembangkan penguasaan kompetensi materi {ch_title} secara kolaboratif."
            t1_lk = (ov.tugas_lkpd_memahami if (ov and ov.tugas_lkpd_memahami) else None) or "Pelajari konsep dasar materi bersama kelompok."
            t2_lk = (ov.tugas_lkpd_mengaplikasi if (ov and ov.tugas_lkpd_mengaplikasi) else None) or "Diskusikan solusi studi kasus kontekstual pemecahan masalah."
            t3_lk = (ov.tugas_lkpd_merefleksi if (ov and ov.tugas_lkpd_merefleksi) else None) or "Simpulkan manfaat pembelajaran hari ini dan evaluasi pemahaman."

            pdf.set_font("Helvetica", size=8.5)
            with pdf.table(col_widths=(45, 115), line_height=5.2, first_row_as_headings=False) as table:
                r1 = table.row()
                r1.cell("Judul LKPD", style=BOLD_STYLE)
                r1.cell(_ascii_safe(judul_lk))
                r2 = table.row()
                r2.cell("Tujuan Aktivitas", style=BOLD_STYLE)
                r2.cell(_ascii_safe(tujuan_lk))
                r3 = table.row()
                r3.cell("Langkah 3M", style=BOLD_STYLE)
                r3.cell(_ascii_safe(f"1. Memahami: {t1_lk}\n2. Mengaplikasi: {t2_lk}\n3. Merefleksi: {t3_lk}"))
            pdf.ln(2)

        # I. Lampiran 2: Rubrik Asesmen 8 Dimensi Profil Lulusan
        if request.include_rubrik:
            pdf.add_page()
            self._add_section_title(pdf, "I. LAMPIRAN 2: RUBRIK 8 DIMENSI PROFIL LULUSAN (PERMENDIKDASMEN 10/2025)")
            default_dpl = [
                ("1", "Keimanan & Ketakwaan Tuhan YME", "Berdoa, bersikap jujur, dan peduli lingkungan sekitar."),
                ("2", "Kewargaan & Cinta Tanah Air", "Menghargai keberagaman, patuh aturan, dan toleran."),
                ("3", "Penalaran Kritis", "Berpikir logis, analitis, dan menarik kesimpulan berbasis bukti."),
                ("4", "Kreativitas", "Menghasilkan karya pemecahan masalah yang inovatif dan orisinal."),
                ("5", "Kolaborasi", "Bekerja sama aktif, berbagi peran adil, dan saling membantu."),
                ("6", "Kemandirian", "Regulasi diri mandiri, inisiatif belajar, dan tuntas tepat waktu."),
                ("7", "Kesehatan & Kebugaran", "Menjaga kebersihan, keselamatan praktik, dan fokus emosi positif."),
                ("8", "Komunikasi", "Menyimak aktif, presentasi runtut, dan menanggapi santun."),
            ]

            active_dpl = []
            if ov and ov.custom_rubrik_dpl:
                for item in ov.custom_rubrik_dpl:
                    if item.is_active:
                        active_dpl.append((str(item.no), item.nama_dimensi, item.indikator))
            if not active_dpl:
                active_dpl = default_dpl

            pdf.set_font("Helvetica", size=7.5)
            with pdf.table(col_widths=(8, 42, 62, 12, 12, 12, 12), line_height=4.8, first_row_as_headings=True) as table:
                hdr = table.row()
                hdr.cell("No", style=BOLD_STYLE)
                hdr.cell("Dimensi Profil Lulusan", style=BOLD_STYLE)
                hdr.cell("Indikator Perilaku Amatan", style=BOLD_STYLE)
                hdr.cell("MB", style=BOLD_STYLE)
                hdr.cell("B", style=BOLD_STYLE)
                hdr.cell("BSH", style=BOLD_STYLE)
                hdr.cell("SB", style=BOLD_STYLE)
                for no_s, n_d, i_d in active_dpl:
                    r = table.row()
                    r.cell(no_s)
                    r.cell(_ascii_safe(n_d), style=BOLD_STYLE)
                    r.cell(_ascii_safe(i_d))
                    r.cell("[  ]")
                    r.cell("[  ]")
                    r.cell("[  ]")
                    r.cell("[  ]")
            pdf.ln(1)
            pdf.set_font("Helvetica", "I", 7.5)
            pdf.cell(0, 4, _ascii_safe("* Skala Observasi: MB = Mulai Berkembang (1), B = Berkembang (2), BSH = Berkembang Sesuai Harapan (3), SB = Sangat Berkembang (4)."), new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 4, _ascii_safe("Catatan Observasi Guru: ......................................................................................................................................................"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

        if lampiran.get("glosarium"):
            pdf.set_font("Helvetica", size=8.5)
            with pdf.table(col_widths=(45, 115), line_height=5.2, first_row_as_headings=False) as table:
                r_glo = table.row()
                r_glo.cell("Glosarium", style=BOLD_STYLE)
                r_glo.cell(_ascii_safe(lampiran["glosarium"]))
            pdf.ln(2)

    def _build_cp_tp(self, pdf: FPDF, request: DocumentGenerateRequest, subject: CurriculumSubject, chapter: Optional[ChapterTopic] = None) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "CAPAIAN PEMBELAJARAN (CP) & PEMETAAN TUJUAN PEMBELAJARAN (TP)", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.cell(0, 5, _ascii_safe(f"MATA PELAJARAN {subject.nama_mapel.upper()} - FASE {subject.fase} (KELAS {subject.kelas})"), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(3)

        durasi_menit = getattr(subject, "durasi_1_jp_menit", 40)
        total_jp_tahun = subject.total_alokasi_jp_tahun or (subject.alokasi_jp_mingguan * 36)
        id_rows = [
            ("Mata Pelajaran", subject.nama_mapel),
            ("Jenjang / Fase / Kelas", f"{subject.jenjang} / Fase {subject.fase} / Kelas {subject.kelas}"),
            ("Alokasi Waktu", f"{total_jp_tahun} JP/Tahun ({subject.alokasi_jp_mingguan} JP/Minggu x {durasi_menit} Menit)"),
            ("Dasar Hukum", "Kepka BSKAP No. 046/H/KR/2025 & Permendikdasmen No. 13/2025"),
        ]
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(45, 115), line_height=5.2, first_row_as_headings=False) as table:
            for k, v in id_rows:
                r = table.row()
                r.cell(_ascii_safe(k), style=BOLD_STYLE)
                r.cell(_ascii_safe(v))
        pdf.ln(2)

        self._add_section_title(pdf, f"1. Rasional Mata Pelajaran {subject.nama_mapel}")
        rasional = getattr(subject, "rasional_bskap", "") or (
            f"Mata pelajaran {subject.nama_mapel} membekali peserta didik dengan kemampuan berpikir kritis, analitis, "
            f"kreatif, serta keterampilan pemecahan masalah secara sistematis sesuai perkembangan zaman."
        )
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 4.8, _ascii_safe(rasional), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        self._add_section_title(pdf, f"2. Tujuan Mata Pelajaran {subject.nama_mapel}")
        aims_list = _split_numbered_aims(getattr(subject, "tujuan_bskap", ""), subject.nama_mapel)
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(12, 148), line_height=5.2) as table:
            hdr = table.row(style=HEADER_STYLE)
            hdr.cell("No")
            hdr.cell("Rumusan Tujuan Mata Pelajaran")
            for idx, aim in enumerate(aims_list, start=1):
                r = table.row()
                r.cell(str(idx), style=BOLD_STYLE)
                r.cell(_ascii_safe(aim))
        pdf.ln(2)

        self._add_section_title(pdf, f"3. Capaian Pembelajaran Fase {subject.fase} Berdasarkan Elemen")
        elems = _resolve_effective_cp_elements(subject, request)
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(45, 115), line_height=5.2) as table:
            hdr = table.row(style=HEADER_STYLE)
            hdr.cell("Elemen")
            hdr.cell("Deskripsi Capaian Pembelajaran Resmi (BSKAP 046/2025)")
            for e in elems:
                r = table.row()
                r.cell(_ascii_safe(e.get("nama_elemen", "-")), style=BOLD_STYLE)
                r.cell(_ascii_safe(e.get("deskripsi_cp", "-")))
        pdf.ln(2)

        self._add_section_title(pdf, "4. Pemetaan Tujuan Pembelajaran (TP) per Bab")
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(35, 18, 92, 15), line_height=5.2) as table:
            hdr = table.row(style=HEADER_STYLE)
            hdr.cell("Bab / Materi")
            hdr.cell("Kode TP")
            hdr.cell("Rumusan Tujuan Pembelajaran")
            hdr.cell("JP")
            for ch in subject.bab_list:
                is_curr = (request.chapter_id and ch.id == request.chapter_id) or (chapter and ch.id == chapter.id)
                tps = _resolve_effective_tps(ch, request) if is_curr else ch.tujuan_pembelajaran
                for tp in tps:
                    r = table.row()
                    r.cell(_ascii_safe(f"Bab {ch.nomor_bab}"), style=BOLD_STYLE)
                    r.cell(_ascii_safe(tp.code), style=BOLD_STYLE)
                    r.cell(_ascii_safe(tp.deskripsi))
                    r.cell(str(tp.alokasi_jp))
        pdf.ln(2)

    def _build_atp(self, pdf: FPDF, request: DocumentGenerateRequest, subject: CurriculumSubject, chapter: Optional[ChapterTopic] = None) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "ALUR TUJUAN PEMBELAJARAN (ATP) KURIKULUM MERDEKA", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.cell(0, 5, _ascii_safe(f"MATA PELAJARAN {subject.nama_mapel.upper()} - FASE {subject.fase} (KELAS {subject.kelas})"), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(3)

        self._add_section_title(pdf, "Identitas ATP")
        durasi_menit = getattr(subject, "durasi_1_jp_menit", 40)
        id_rows = [
            ("Mata Pelajaran", subject.nama_mapel),
            ("Jenjang / Fase / Kelas", f"{subject.jenjang} / Fase {subject.fase} / Kelas {subject.kelas}"),
            ("Alokasi Waktu", f"{subject.alokasi_jp_mingguan} JP/Minggu (1 JP = {durasi_menit} Menit)"),
            ("Rujukan Regulasi", "Kepka BSKAP No. 046/H/KR/2025 & Permendikdasmen No. 13/2025"),
        ]
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(45, 115), line_height=5.2, first_row_as_headings=False) as table:
            for k, v in id_rows:
                r = table.row()
                r.cell(_ascii_safe(k), style=BOLD_STYLE)
                r.cell(_ascii_safe(v))
        pdf.ln(2)

        self._add_section_title(pdf, "Alur dan Tujuan Pembelajaran (ATP)")
        pdf.set_font("Helvetica", size=8)
        with pdf.table(col_widths=(12, 18, 65, 45, 20), line_height=5.0) as table:
            hdr = table.row(style=HEADER_STYLE)
            hdr.cell("No")
            hdr.cell("Alur/TP")
            hdr.cell("Alur Tujuan Pembelajaran & Lingkup Materi")
            hdr.cell("Dimensi Profil Lulusan")
            hdr.cell("Alokasi JP")
            seq = 1
            for ch in subject.bab_list:
                is_curr = (request.chapter_id and ch.id == request.chapter_id) or (chapter and ch.id == chapter.id)
                tps = _resolve_effective_tps(ch, request) if is_curr else ch.tujuan_pembelajaran
                dpl_str = ", ".join(ch.dimensi_profil_lulusan) if ch.dimensi_profil_lulusan else "Bernalar Kritis"
                for tp in tps:
                    r = table.row()
                    r.cell(str(seq), style=BOLD_STYLE)
                    r.cell(_ascii_safe(tp.code), style=BOLD_STYLE)
                    r.cell(_ascii_safe(f"Bab {ch.nomor_bab}: {tp.deskripsi}"))
                    r.cell(_ascii_safe(dpl_str))
                    r.cell(_ascii_safe(f"{tp.alokasi_jp} JP"))
                    seq += 1
        pdf.ln(2)

    def _build_prota(self, pdf: FPDF, request: DocumentGenerateRequest, subject: CurriculumSubject, chapter: Optional[ChapterTopic] = None) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "PROGRAM TAHUNAN (PROTA) TAHUN AJARAN 2025/2026", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.cell(0, 5, _ascii_safe(f"MATA PELAJARAN {subject.nama_mapel.upper()} - KELAS {subject.kelas} (FASE {subject.fase})"), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(3)

        self._add_section_title(pdf, "Identitas Program Tahunan")
        total_target = subject.total_alokasi_jp_tahun or (subject.alokasi_jp_mingguan * 36)
        id_rows = [
            ("Mata Pelajaran", subject.nama_mapel),
            ("Kelas / Fase / Jenjang", f"Kelas {subject.kelas} / Fase {subject.fase} / {subject.jenjang}"),
            ("Total Target Waktu", f"{total_target} JP / Tahun ({subject.alokasi_jp_mingguan} JP/Minggu)"),
            ("Dasar Regulasi", "Kepka BSKAP No. 046/H/KR/2025 & Permendikdasmen No. 13/2025"),
        ]
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(45, 115), line_height=5.2, first_row_as_headings=False) as table:
            for k, v in id_rows:
                r = table.row()
                r.cell(_ascii_safe(k), style=BOLD_STYLE)
                r.cell(_ascii_safe(v))
        pdf.ln(2)

        self._add_section_title(pdf, "Distribusi Program Tahunan")
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(12, 18, 85, 25, 20), line_height=5.2) as table:
            hdr = table.row(style=HEADER_STYLE)
            hdr.cell("No")
            hdr.cell("Smt")
            hdr.cell("Bab / Materi Pokok")
            hdr.cell("Alokasi JP")
            hdr.cell("Keterangan")
            total_jp = 0
            for idx, ch in enumerate(subject.bab_list, start=1):
                is_curr = (request.chapter_id and ch.id == request.chapter_id) or (chapter and ch.id == chapter.id)
                bab_jp = _resolve_effective_alokasi_jp(ch, request) if is_curr else ch.alokasi_jp
                total_jp += bab_jp
                r = table.row()
                r.cell(str(idx), style=BOLD_STYLE)
                r.cell(str(ch.semester))
                r.cell(_ascii_safe(f"Bab {ch.nomor_bab}: {ch.judul_bab}"))
                r.cell(f"{bab_jp} JP")
                r.cell(f"{ch.estimasi_pertemuan} PTM")

            # Summary row
            r_tot = table.row(style=HEADER_STYLE)
            r_tot.cell("TOTAL ALOKASI WAKTU TAHUNAN", colspan=3)
            r_tot.cell(f"{total_jp} JP")
            r_tot.cell("Tuntas")
        pdf.ln(2)

    def _build_promes(self, pdf: FPDF, request: DocumentGenerateRequest, subject: CurriculumSubject, chapter: Optional[ChapterTopic] = None, tpl: Optional[dict] = None) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(
            0,
            6,
            _ascii_safe(f"PROGRAM SEMESTER (PROMES) - SEMESTER {request.semester} TAHUN AJARAN 2025/2026"),
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.cell(0, 5, _ascii_safe(f"MATA PELAJARAN {subject.nama_mapel.upper()} | KELAS {subject.kelas} (FASE {subject.fase}) | {subject.alokasi_jp_mingguan} JP/MINGGU"), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(3)

        chapters = subject.get_chapters_by_semester(request.semester) or subject.bab_list
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(12, 28, 115, 25, 80), line_height=5.2) as table:
            hdr = table.row(style=HEADER_STYLE)
            hdr.cell("No")
            hdr.cell("Bab")
            hdr.cell("Materi Pokok / Tujuan Pembelajaran")
            hdr.cell("Alokasi JP")
            hdr.cell("Distribusi Minggu Efektif")
            total_smt_jp = 0
            for idx, ch in enumerate(chapters, start=1):
                is_curr = (request.chapter_id and ch.id == request.chapter_id) or (chapter and ch.id == chapter.id)
                bab_jp = _resolve_effective_alokasi_jp(ch, request) if is_curr else ch.alokasi_jp
                tps = _resolve_effective_tps(ch, request) if is_curr else ch.tujuan_pembelajaran
                total_smt_jp += bab_jp
                tp_summary = f"{ch.judul_bab}\n" + "\n".join(f"- [{t.code}] {t.deskripsi}" for t in tps[:2])
                r = table.row()
                r.cell(str(idx), style=BOLD_STYLE)
                r.cell(f"Bab {ch.nomor_bab}", style=BOLD_STYLE)
                r.cell(_ascii_safe(tp_summary))
                r.cell(f"{bab_jp} JP")
                r.cell(_ascii_safe(ch.rentang_minggu_promes or "Bulan 1 - 6 (Minggu Efektif)"))

            # Total row
            r_tot = table.row(style=HEADER_STYLE)
            r_tot.cell("TOTAL ALOKASI JP SEMESTER INI", colspan=3)
            r_tot.cell(f"{total_smt_jp} JP")
            r_tot.cell("Sesuai Kalender")
        pdf.ln(2)

    def _build_kktp(self, pdf: FPDF, request: DocumentGenerateRequest, subject: CurriculumSubject, chapter: Optional[ChapterTopic]) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "KRITERIA KETERCAPAIAN TUJUAN PEMBELAJARAN (KKTP)", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.cell(0, 5, _ascii_safe(f"PENDEKATAN RUBRIK & INTERVAL NILAI (PPA REVISI 2025) - FASE {subject.fase}"), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(3)

        self._add_section_title(pdf, "Identitas Dokumen KKTP")
        id_rows = [
            ("Mata Pelajaran", subject.nama_mapel),
            ("Jenjang / Kelas / Fase", f"{subject.jenjang} / Kelas {request.kelas} / Fase {subject.fase}"),
            ("Materi / Bab / Semester", f"{chapter.judul_bab if chapter else 'Semua Bab'} / Semester {request.semester}"),
            ("Pendekatan KKTP", "Rubrik Deskriptif 4 Kategori & Interval Nilai Tuntas (PPA 2025)"),
        ]
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(45, 115), line_height=5.2, first_row_as_headings=False) as table:
            for k, v in id_rows:
                r = table.row()
                r.cell(_ascii_safe(k), style=BOLD_STYLE)
                r.cell(_ascii_safe(v))
        pdf.ln(2)

        self._add_section_title(pdf, "A. Skala Interval Nilai KKTP (4 Kategori)")
        intervals = [
            ("0 - 40%", "Belum Mencapai Ketuntasan", "Remedial di seluruh materi pembelajaran"),
            ("41 - 65%", "Belum Mencapai Ketuntasan", "Remedial pada bagian indikator yang belum tuntas"),
            ("66 - 85%", "Sudah Mencapai Ketuntasan", "Tidak perlu remedial, siap materi berikutnya"),
            ("86 - 100%", "Sudah Mencapai Ketuntasan", "Diberikan pengayaan / tantangan tingkat lanjut"),
        ]
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(25, 50, 85), line_height=5.2) as table:
            hdr = table.row(style=HEADER_STYLE)
            hdr.cell("Interval")
            hdr.cell("Kategori Ketuntasan")
            hdr.cell("Tindak Lanjut / Intervensi Guru")
            for rng, cat, act in intervals:
                r = table.row()
                r.cell(rng, style=BOLD_STYLE)
                r.cell(_ascii_safe(cat))
                r.cell(_ascii_safe(act))
        pdf.ln(2)

        self._add_section_title(pdf, "B. Rubrik Ketercapaian Tujuan Pembelajaran")
        tps = _resolve_effective_tps(chapter, request) if chapter else [tp for c in subject.bab_list for tp in c.tujuan_pembelajaran]
        pdf.set_font("Helvetica", size=8)
        with pdf.table(col_widths=(18, 52, 45, 45), line_height=5.0) as table:
            hdr = table.row(style=HEADER_STYLE)
            hdr.cell("Kode TP")
            hdr.cell("Tujuan Pembelajaran")
            hdr.cell("Perlu Bimbingan (0-65%)")
            hdr.cell("Cakap / Mahir (66-100%)")
            for tp in tps:
                r = table.row()
                r.cell(_ascii_safe(tp.code), style=BOLD_STYLE)
                r.cell(_ascii_safe(f"{tp.deskripsi} ({tp.alokasi_jp} JP)"))
                r.cell("Belum mampu menjelaskan konsep secara utuh; butuh panduan guru.")
                r.cell("Mampu mengaplikasikan konsep secara mandiri dan bernalar kritis.")
        pdf.ln(2)

    def _build_lkpd(self, pdf: FPDF, request: DocumentGenerateRequest, subject: CurriculumSubject, chapter: Optional[ChapterTopic], tpl: dict) -> None:
        ch = chapter or (subject.bab_list[0] if subject.bab_list else None)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "LEMBAR KERJA PESERTA DIDIK (LKPD) MANDIRI", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.cell(0, 5, _ascii_safe("PENDEKATAN PEMBELAJARAN MENDALAM (DEEP LEARNING 3M)"), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(3)

        self._add_section_title(pdf, "Identitas Siswa & Pembelajaran")
        id_rows = [
            ("Mata Pelajaran", subject.nama_mapel),
            ("Topik / Bab Pokok", f"Bab {ch.nomor_bab if ch else 1}: {ch.judul_bab if ch else subject.nama_mapel}"),
            ("Jenjang / Kelas / Semester", f"{subject.jenjang} / Kelas {request.kelas} (Fase {subject.fase}) / Semester {request.semester}"),
            ("Nama Siswa / Kelompok", "....................................................   Kelas / No: .........."),
        ]
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(45, 115), line_height=5.2, first_row_as_headings=False) as table:
            for k, v in id_rows:
                r = table.row()
                r.cell(_ascii_safe(k), style=BOLD_STYLE)
                r.cell(_ascii_safe(v))
        pdf.ln(2)

        self._add_section_title(pdf, "A. Tujuan Pembelajaran (Fokus LKPD)")
        tps = _resolve_effective_tps(ch, request) if ch else []
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(20, 140), line_height=5.2) as table:
            hdr = table.row(style=HEADER_STYLE)
            hdr.cell("Kode")
            hdr.cell("Tujuan Pembelajaran yang Diharapkan")
            for tp in tps:
                r = table.row()
                r.cell(_ascii_safe(tp.code), style=BOLD_STYLE)
                r.cell(_ascii_safe(f"{tp.deskripsi} ({tp.alokasi_jp} JP)"))
        pdf.ln(2)

        self._add_section_title(pdf, "B. Langkah Aktivitas Pembelajaran Mendalam (3M)")
        pm = tpl.get("pembelajaran_mendalam_3m") or {}
        stages = [
            ("1. Tahap Memahami", pm.get("memahami", f"Pelajari konsep dasar {ch.judul_bab if ch else subject.nama_mapel} bersama teman kelompok.")),
            ("2. Tahap Mengaplikasi", pm.get("mengaplikasi", "Lakukan investigasi dan diskusikan solusi studi kasus kontekstual.")),
            ("3. Tahap Merefleksi", pm.get("merefleksi", "Presentasikan hasil karya dan simpulkan hikmah pembelajaran.")),
        ]
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(45, 115), line_height=5.2) as table:
            hdr = table.row(style=HEADER_STYLE)
            hdr.cell("Tahapan 3M")
            hdr.cell("Instruksi & Panduan Aktivitas Peserta Didik")
            for st_title, st_desc in stages:
                r = table.row()
                r.cell(_ascii_safe(st_title), style=BOLD_STYLE)
                r.cell(_ascii_safe(st_desc))
        pdf.ln(2)

        self._add_section_title(pdf, "C. Lembar Tugas & Soal Latihan Mandiri")
        pdf.set_font("Helvetica", size=8.5)
        with pdf.table(col_widths=(12, 148), line_height=5.2) as table:
            hdr = table.row(style=HEADER_STYLE)
            hdr.cell("No")
            hdr.cell("Pertanyaan & Penugasan")
            tasks = [
                f"Jelaskan konsep utama materi {ch.judul_bab if ch else subject.nama_mapel} dengan bahasamu sendiri!",
                f"Bagaimana cara menerapkan konsep {ch.judul_bab if ch else subject.nama_mapel} untuk menyelesaikan persoalan nyata di sekitarmu?",
                "Tuliskan kesimpulan dan refleksi belajarmu hari ini pada lembar kerja yang tersedia!",
            ]
            for idx, t_text in enumerate(tasks, start=1):
                r = table.row()
                r.cell(str(idx), style=BOLD_STYLE)
                r.cell(_ascii_safe(t_text))
        pdf.ln(2)

    def _build_exam_document(
        self,
        pdf: FPDF,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
    ) -> None:
        bp = QuestionBlueprintEngine.build_blueprint(request, subject, chapter)
        letters = QuestionBlueprintEngine.OPTION_LETTERS

        if request.service_id == ServiceIdEnum.KUIS:
            title = "KUIS HARIAN & PENILAIAN FORMATIF"
        elif request.service_id == ServiceIdEnum.SUMATIF_BAB:
            title = "ASESMEN SUMATIF LINGKUP MATERI (BAB)"
        else:
            title = f"PENILAIAN {bp['jenis_ujian']} - PAKET {bp['paket_soal']}"

        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, _ascii_safe(title), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 5, _ascii_safe(f"{subject.nama_mapel} | {subject.jenjang} Kelas {subject.kelas} | Semester {request.semester}"), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(3)

        # 1. Halaman Pertama: Naskah Soal Evaluasi Siswa
        usable_w = pdf.w - pdf.l_margin - pdf.r_margin

        if bp["pg_questions"]:
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "A. Soal Pilihan Ganda", new_x="LMARGIN", new_y="NEXT")
            for q in bp["pg_questions"]:
                if q.get("stimulus"):
                    pdf.set_x(pdf.l_margin)
                    pdf.set_font("Helvetica", "", 8.8)
                    pdf.multi_cell(usable_w, 4.8, _ascii_safe(q["stimulus"]))
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "B", 9)
                pdf.multi_cell(usable_w, 5, _ascii_safe(f"{q['section_no']}. {q['pertanyaan']}"))
                pdf.set_font("Helvetica", "", 8.8)
                for o_idx, opt_text in enumerate(q.get("opsi") or []):
                    letter = letters[o_idx] if o_idx < len(letters) else str(o_idx + 1)
                    pdf.set_x(pdf.l_margin)
                    pdf.multi_cell(usable_w, 4.6, _ascii_safe(f"   {letter}. {opt_text}"))
                pdf.ln(1.5)

        if bp["essai_questions"]:
            pdf.ln(2)
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "B. Soal Essai", new_x="LMARGIN", new_y="NEXT")
            for q in bp["essai_questions"]:
                if q.get("stimulus"):
                    pdf.set_x(pdf.l_margin)
                    pdf.set_font("Helvetica", "", 8.8)
                    pdf.multi_cell(usable_w, 4.8, _ascii_safe(q["stimulus"]))
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "B", 9)
                pdf.multi_cell(usable_w, 5, _ascii_safe(f"{q['section_no']}. {q['pertanyaan']}"))
                pdf.set_font("Helvetica", "", 8.8)
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(usable_w, 5, "   Jawaban: ___________________________________________________________")
                pdf.ln(1.5)

        # 2. Halaman Kedua: Kunci Jawaban & Kisi-Kisi Pegangan Guru
        pdf.add_page()
        self._add_section_title(pdf, "DOKUMEN PEGANGAN GURU -- KUNCI JAWABAN & KISI-KISI SOAL")
        self._add_section_title(pdf, "Kunci Jawaban & Pedoman Penskoran (Pegangan Guru)")
        pdf.set_font("Helvetica", size=8)
        with pdf.table(col_widths=(12, 30, 98, 20), line_height=5) as table:
            hdr = table.row(style=HEADER_STYLE)
            for h_col in ("No", "Bentuk & Level", "Kunci Jawaban & Pembahasan", "Skor"):
                hdr.cell(h_col)
            for q in bp["questions"]:
                r = table.row()
                r.cell(f"{q['bagian']}.{q['section_no']}")
                bentuk_label = "PG" if q["tipe_soal"] == "PG" else "Essai"
                r.cell(_ascii_safe(f"{bentuk_label} ({q['level_kognitif']})"))
                pemb = f" - {q['pembahasan']}" if q.get("pembahasan") else ""
                r.cell(_ascii_safe(f"{q['kunci_jawaban']}{pemb}"))
                r.cell(str(q["bobot_skor"]))
            r_tot = table.row()
            r_tot.cell("-")
            r_tot.cell("TOTAL")
            r_tot.cell("Nilai Akhir = (Skor Diperoleh / 100) x 100")
            r_tot.cell(str(bp["total_skor_maksimal"]))
        pdf.ln(3)

        # Kisi-Kisi 7 Kolom (S11 & S12)
        if request.service_id in (ServiceIdEnum.SUMATIF_BAB, ServiceIdEnum.STS_SAS):
            self._add_section_title(pdf, "Tabel Kisi-Kisi Penulisan Soal (7 Kolom)")
            pdf.set_font("Helvetica", size=7.5)
            with pdf.table(col_widths=(10, 20, 28, 52, 18, 18, 14), line_height=4.8) as table:
                hdr = table.row(style=HEADER_STYLE)
                for h_col in ("No", "TP", "Materi", "Indikator Soal", "Level", "Bentuk", "Soal"):
                    hdr.cell(h_col)
                for row in bp["kisi_kisi"]:
                    r = table.row()
                    r.cell(str(row["no"]))
                    r.cell(_ascii_safe(row["tp_code"]))
                    r.cell(_ascii_safe(row["materi"][:30]))
                    r.cell(_ascii_safe(row["indikator"][:60]))
                    r.cell(_ascii_safe(row["level_kognitif"]))
                    r.cell(_ascii_safe(row["bentuk_soal"]))
                    r.cell(_ascii_safe(row["nomor_soal"]))
            pdf.ln(3)
            tot = table.row(style=BOLD_STYLE)
            tot.cell("-")
            tot.cell("TOTAL")
            tot.cell("Nilai Akhir = (Skor Diperoleh / 100) x 100")
            tot.cell(str(bp["total_skor_maksimal"]))

        # LJK khusus S12
        if request.service_id == ServiceIdEnum.STS_SAS:
            pdf.add_page()
            self._add_section_title(pdf, "Lembar Jawab Peserta Didik (LJK)")
            pg_qs = [q for q in bp["questions"] if q["tipe_soal"] == "PG"]
            if pg_qs:
                pdf.set_font("Helvetica", size=8.5)
                with pdf.table(col_widths=(20, 140), line_height=5) as table:
                    hdr = table.row(style=HEADER_STYLE)
                    hdr.cell("No")
                    hdr.cell("Pilihan Jawaban")
                    for q in pg_qs:
                        r = table.row()
                        r.cell(str(q["no"]))
                        opts_str = "   ".join(f"[ {letters[i]} ]" for i in range(max(4, len(q.get("opsi") or []))))
                        r.cell(opts_str)

    def _build_presensi(
        self,
        pdf: FPDF,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        teacher: TeacherProfile,
    ) -> None:
        ov = request.custom_overrides
        rombel = (ov.nama_rombel if (ov and ov.nama_rombel) else None) or f"Kelas {subject.kelas}"
        bulan = (ov.bulan_presensi if (ov and ov.bulan_presensi) else None) or "Juli 2026"
        self._add_doc_title(
            pdf,
            "PRESENSI DAN KEHADIRAN PESERTA DIDIK",
            f"{subject.nama_mapel} | {rombel} | Bulan {bulan} | Semester {request.semester}",
        )
        students = (ov.students if (ov and ov.students) else None) or []
        rows_src = [
            (idx, getattr(s, "nis", "-") or "-", getattr(s, "nama", f"Peserta Didik {idx}"), getattr(s, "jenis_kelamin", "L") or "L")
            for idx, s in enumerate(students, start=1)
        ] or [(i, f"2026{i:03d}", f"Peserta Didik {i}", "L" if i % 2 else "P") for i in range(1, 16)]

        pdf.set_font("Helvetica", size=7.5)
        col_widths = (10, 22, 58, 10) + (8,) * 12 + (11, 11, 11, 11)
        with pdf.table(col_widths=col_widths, line_height=4.8) as table:
            hdr = table.row(style=HEADER_STYLE)
            for h in ("No", "NIS", "Nama Peserta Didik", "L/P", *[str(d) for d in range(1, 13)], "H", "S", "I", "A"):
                hdr.cell(h)
            for no, nis, nama, lp in rows_src:
                r = table.row()
                r.cell(str(no))
                r.cell(_ascii_safe(nis))
                r.cell(_ascii_safe(nama[:34]))
                r.cell(_ascii_safe(lp))
                for _ in range(16):
                    r.cell("")

    def _build_daftar_nilai(
        self,
        pdf: FPDF,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        teacher: TeacherProfile,
    ) -> None:
        ov = request.custom_overrides
        rombel = (ov.nama_rombel if (ov and ov.nama_rombel) else None) or f"Kelas {subject.kelas}"
        kktp = (ov.nilai_kktp if (ov and ov.nilai_kktp is not None) else None) or 75
        self._add_doc_title(
            pdf,
            "BUKU PENGOLAHAN DAFTAR NILAI PESERTA DIDIK",
            f"{subject.nama_mapel} | {rombel} | Semester {request.semester} | KKTP: {kktp}",
        )
        students = (ov.students if (ov and ov.students) else None) or []
        rows_src = [
            (idx, getattr(s, "nis", "-") or "-", getattr(s, "nama", f"Peserta Didik {idx}"), getattr(s, "jenis_kelamin", "L") or "L")
            for idx, s in enumerate(students, start=1)
        ] or [(i, f"2026{i:03d}", f"Peserta Didik {i}", "L" if i % 2 else "P") for i in range(1, 16)]

        pdf.set_font("Helvetica", size=7.5)
        col_widths = (10, 22, 60, 10, 14, 14, 14, 14, 16, 16, 16, 18, 26)
        with pdf.table(col_widths=col_widths, line_height=4.8) as table:
            hdr = table.row(style=HEADER_STYLE)
            for h in ("No", "NIS", "Nama Peserta Didik", "L/P", "TP 1", "TP 2", "TP 3", "TP 4", "Formatif", "STS", "SAS", "NA", "Ketuntasan"):
                hdr.cell(h)
            for no, nis, nama, lp in rows_src:
                r = table.row()
                r.cell(str(no))
                r.cell(_ascii_safe(nis))
                r.cell(_ascii_safe(nama[:34]))
                r.cell(_ascii_safe(lp))
                for _ in range(9):
                    r.cell("")

    def _add_lembar_pengesahan(self, pdf: FPDF, teacher: TeacherProfile) -> None:
        pdf.add_page()
        pengesahan = teacher.get_lembar_pengesahan()
        pdf.ln(6)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.cell(0, 5, _ascii_safe(pengesahan["titimangsa"]), new_x="LMARGIN", new_y="NEXT", align="R")
        pdf.ln(2)

        col_w = (pdf.w - pdf.l_margin - pdf.r_margin) / 2.0
        pdf.set_font("Helvetica", "", 9.5)
        pdf.cell(col_w, 5, "Mengetahui, Kepala Sekolah", align="C")
        pdf.cell(col_w, 5, _ascii_safe(pengesahan["jabatan_guru"]), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(15)

        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(col_w, 5, _ascii_safe(pengesahan["nama_kepala_sekolah"]), align="C")
        pdf.cell(col_w, 5, _ascii_safe(pengesahan["nama_guru"]), new_x="LMARGIN", new_y="NEXT", align="C")

        pdf.set_font("Helvetica", "", 9)
        pdf.cell(col_w, 5, _ascii_safe(pengesahan["nip_kepala_sekolah"]), align="C")
        pdf.cell(col_w, 5, _ascii_safe(pengesahan["nip_guru"]), new_x="LMARGIN", new_y="NEXT", align="C")
