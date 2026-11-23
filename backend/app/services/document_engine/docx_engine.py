import io
import re
from typing import Optional, List, Dict, Any
from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

from app.core.exceptions import DocumentGenerationError
from app.models.curriculum import CurriculumSubject, ChapterTopic, LearningObjective
from app.models.teacher import TeacherProfile
from app.schemas.generation import DocumentGenerateRequest, ServiceIdEnum
from app.services.document_engine.base_engine import DocumentEngine
from app.services.document_engine.question_blueprint import QuestionBlueprintEngine


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


class DocxDocumentEngine(DocumentEngine):
    """Engine responsible for generating official Microsoft Word (.docx) documents matching the Live Preview layout 1:1."""

    def generate(
        self,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
        raw_template: Optional[dict] = None,
    ) -> bytes:
        try:
            doc = Document()

            section = doc.sections[0]
            if request.paper_size.value == "F4":
                section.page_width = Mm(self.F4_WIDTH_MM)
                section.page_height = Mm(self.F4_HEIGHT_MM)
            else:
                section.page_width = Mm(self.A4_WIDTH_MM)
                section.page_height = Mm(self.A4_HEIGHT_MM)

            section.top_margin = Mm(self.MARGIN_TOP_MM)
            section.bottom_margin = Mm(self.MARGIN_BOTTOM_MM)
            section.left_margin = Mm(self.MARGIN_LEFT_MM)
            section.right_margin = Mm(self.MARGIN_RIGHT_MM)

            # 1. Normal Style (Arial 10pt, Line Spacing 1.15, Space After 4pt)
            normal_style = doc.styles["Normal"]
            normal_font = normal_style.font
            normal_font.name = "Arial"
            normal_font.size = Pt(10)
            normal_font.color.rgb = RGBColor(15, 23, 42)
            normal_style.paragraph_format.line_spacing = 1.15
            normal_style.paragraph_format.space_after = Pt(4)

            # 2. Heading 1 Style (Navigation Pane compatible)
            try:
                h1_style = doc.styles["Heading 1"]
            except KeyError:
                h1_style = doc.styles.add_style("Heading 1", WD_STYLE_TYPE.PARAGRAPH)
            h1_font = h1_style.font
            h1_font.name = "Arial"
            h1_font.size = Pt(12)
            h1_font.bold = True
            h1_font.color.rgb = RGBColor(15, 23, 42)
            h1_style.paragraph_format.space_before = Pt(10)
            h1_style.paragraph_format.space_after = Pt(3)
            h1_style.paragraph_format.keep_with_next = True

            # 3. Heading 2 Style (Sub-heading Navigation Pane)
            try:
                h2_style = doc.styles["Heading 2"]
            except KeyError:
                h2_style = doc.styles.add_style("Heading 2", WD_STYLE_TYPE.PARAGRAPH)
            h2_font = h2_style.font
            h2_font.name = "Arial"
            h2_font.size = Pt(11)
            h2_font.bold = True
            h2_font.color.rgb = RGBColor(30, 58, 138)
            h2_style.paragraph_format.space_before = Pt(8)
            h2_style.paragraph_format.space_after = Pt(2)
            h2_style.paragraph_format.keep_with_next = True

            # 4. Standard Footer Page Number
            self._add_page_number_to_footer(section)

            tpl = raw_template or (chapter.modul_ajar_template if chapter else None)
            if request.service_id == ServiceIdEnum.MODUL_AJAR:
                self._build_modul_ajar(doc, request, subject, chapter, teacher, tpl)
            elif request.service_id == ServiceIdEnum.ATP:
                self._build_atp(doc, request, subject, chapter, teacher)
            elif request.service_id == ServiceIdEnum.CP_TP:
                self._build_cp_tp(doc, request, subject, chapter, teacher)
            elif request.service_id == ServiceIdEnum.PROTA:
                self._build_prota(doc, request, subject, chapter, teacher)
            elif request.service_id == ServiceIdEnum.PROMES:
                self._build_promes(doc, request, subject, chapter, teacher)
            elif request.service_id == ServiceIdEnum.KKTP:
                self._build_kktp(doc, request, subject, chapter, teacher)
            elif request.service_id == ServiceIdEnum.LKPD:
                self._build_lkpd(doc, request, subject, chapter, teacher, tpl)
            elif request.service_id in (ServiceIdEnum.KUIS, ServiceIdEnum.SUMATIF_BAB, ServiceIdEnum.STS_SAS):
                self._build_exam_document(doc, request, subject, chapter, teacher)

            self._add_lembar_pengesahan(doc, teacher)

            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            raise DocumentGenerationError(f"Failed to generate Word document: {str(e)}")

    def _add_kop_surat(self, doc: Document, teacher: TeacherProfile):
        kop = teacher.get_formatted_kop()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)

        run_instansi = p.add_run(f"PEMERINTAH {kop['kabupaten_kota'].upper()} — DINAS PENDIDIKAN\n")
        run_instansi.bold = True
        run_instansi.font.size = Pt(10.5)

        run_sekolah = p.add_run(f"{kop['nama_sekolah']}\n")
        run_sekolah.bold = True
        run_sekolah.font.size = Pt(13.5)

        run_alamat = p.add_run(f"NPSN: {kop['npsn']} • {kop['kabupaten_kota']}, Provinsi {kop['provinsi']}\n")
        run_alamat.font.size = Pt(9)
        run_alamat.font.italic = True

        p_pr = p._p.get_or_add_pPr()
        p_bdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="double" w:sz="12" w:space="4" w:color="0F172A"/></w:pBdr>')
        p_pr.append(p_bdr)
        p.paragraph_format.space_after = Pt(12)

    def _add_cp_fase_and_elemen_block(self, doc: Document, subject: CurriculumSubject):
        """Renders the official CAPAIAN PEMBELAJARAN FASE and Fase Berdasarkan Elemen table."""
        self._add_section_heading(doc, f"Capaian Pembelajaran Fase {subject.fase} Berdasarkan Elemen")
        elems = getattr(subject, "elemen_cp_resmi", []) or []
        tbl = doc.add_table(rows=1, cols=2)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.rows[0].cells[0].text = "Elemen"
        tbl.rows[0].cells[1].text = "Capaian Pembelajaran"
        self._format_header_cell(tbl.rows[0].cells[0], width_mm=40)
        self._format_header_cell(tbl.rows[0].cells[1], width_mm=120)

        if elems:
            for e in elems:
                rc = tbl.add_row().cells
                rc[0].text = str(e.get("nama_elemen", "-"))
                rc[1].text = str(e.get("deskripsi_cp", "-"))
                rc[0].paragraphs[0].runs[0].bold = True
        else:
            for ch in subject.bab_list[:3]:
                rc = tbl.add_row().cells
                rc[0].text = getattr(ch, "elemen_cp", "Pemahaman Konsep")
                rc[1].text = "; ".join(tp.deskripsi for tp in ch.tujuan_pembelajaran)
                rc[0].paragraphs[0].runs[0].bold = True
        self._style_data_table(tbl, [40, 120], has_header_row=True)
        doc.add_paragraph()

    # =========================================================================
    # 1. SERVICE 03: CAPAIAN PEMBELAJARAN & PEMETAAN CP-TP (1:1 with Live Preview)
    # =========================================================================
    def _build_cp_tp(
        self,
        doc: Document,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        selected_chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
    ):
        self._add_kop_surat(doc, teacher)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(8)
        r1 = p.add_run("CAPAIAN PEMBELAJARAN DAN TUJUAN PEMBELAJARAN\n")
        r1.bold = True
        r1.font.size = Pt(12)
        r2 = p.add_run(f"MATA PELAJARAN {subject.nama_mapel.upper()} — FASE {subject.fase} (KELAS {subject.kelas})")
        r2.bold = True
        r2.font.size = Pt(11)

        # Identitas Dokumen
        durasi_menit = getattr(subject, "durasi_1_jp_menit", 40)
        total_jp_tahun = subject.total_alokasi_jp_tahun or (subject.alokasi_jp_mingguan * 36)
        id_table = doc.add_table(rows=0, cols=2)
        id_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        id_rows = [
            ("Mata Pelajaran", subject.nama_mapel),
            ("Jenjang / Fase / Kelas", f"{subject.jenjang} / Fase {subject.fase} / Kelas {subject.kelas}"),
            ("Alokasi Waktu", f"{total_jp_tahun} JP/Tahun ({subject.alokasi_jp_mingguan} JP/Minggu × {durasi_menit} Menit)"),
            ("Dasar Hukum", "Kepka BSKAP Kemendikdasmen No. 046/H/KR/2025 & Permendikdasmen No. 13/2025"),
        ]
        for k, v in id_rows:
            rc = id_table.add_row().cells
            rc[0].text = k
            rc[1].text = str(v)
            self._format_header_cell(rc[0], width_mm=45)
        self._style_data_table(id_table, [45, 115], has_header_row=False)

        # 1. Rasional
        self._add_section_heading(doc, f"1. Rasional Mata Pelajaran {subject.nama_mapel}")
        rasional = getattr(subject, "rasional_bskap", "") or (
            f"Mata pelajaran {subject.nama_mapel} membekali peserta didik dengan kemampuan berpikir kritis, analitis, "
            f"kreatif, serta keterampilan pemecahan masalah secara sistematis sesuai perkembangan ilmu pengetahuan dan teknologi."
        )
        doc.add_paragraph(rasional)

        # 2. Tujuan Mata Pelajaran
        self._add_section_heading(doc, f"2. Tujuan Mata Pelajaran {subject.nama_mapel}")
        aims_list = _split_numbered_aims(getattr(subject, "tujuan_bskap", ""), subject.nama_mapel)
        t_aims = doc.add_table(rows=1, cols=2)
        t_aims.alignment = WD_TABLE_ALIGNMENT.CENTER
        t_aims.rows[0].cells[0].text = "No"
        t_aims.rows[0].cells[1].text = "Rumusan Tujuan Mata Pelajaran"
        self._format_header_cell(t_aims.rows[0].cells[0], width_mm=12)
        self._format_header_cell(t_aims.rows[0].cells[1], width_mm=148)
        for idx, aim_str in enumerate(aims_list, start=1):
            rc = t_aims.add_row().cells
            rc[0].text = str(idx)
            rc[1].text = aim_str
            rc[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            rc[0].paragraphs[0].runs[0].bold = True
        self._style_data_table(t_aims, [12, 148], has_header_row=True)

        # 3. Karakteristik & 4. Capaian Pembelajaran Fase Berdasarkan Elemen
        self._add_section_heading(doc, f"3. Karakteristik Mata Pelajaran & 4. Capaian Pembelajaran Fase {subject.fase} Berdasarkan Elemen", level=2)
        karakteristik = getattr(subject, "karakteristik_bskap", "") or (
            f"Mata pelajaran {subject.nama_mapel} menerapkan pendekatan pembelajaran mendalam (Deep Learning 3M) yang mengintegrasikan "
            f"pemahaman konsep, keterampilan proses, dan refleksi kontekstual."
        )
        doc.add_paragraph(karakteristik)

        elems = _resolve_effective_cp_elements(subject, request)
        t_kar = doc.add_table(rows=1, cols=2)
        t_kar.alignment = WD_TABLE_ALIGNMENT.CENTER
        t_kar.rows[0].cells[0].text = "Elemen"
        t_kar.rows[0].cells[1].text = "Deskripsi Capaian Pembelajaran Resmi (BSKAP 046/2025)"
        self._format_header_cell(t_kar.rows[0].cells[0], width_mm=40)
        self._format_header_cell(t_kar.rows[0].cells[1], width_mm=120)
        for e in elems:
            rc = t_kar.add_row().cells
            rc[0].text = str(e.get("nama_elemen", "-"))
            rc[1].text = str(e.get("deskripsi_cp", "-"))
            rc[0].paragraphs[0].runs[0].bold = True
        self._style_data_table(t_kar, [40, 120], has_header_row=True)

        # 5. Pemetaan Capaian dan Tujuan Pembelajaran Semester (Tabel KATEGORI | RUMUSAN)
        self._add_section_heading(doc, f"5. Pemetaan Capaian dan Tujuan Pembelajaran Semester {request.semester}")
        chapters = subject.get_chapters_by_semester(request.semester) or subject.bab_list
        for bab in chapters:
            is_current = selected_chapter and bab.id == selected_chapter.id
            bab_tps = _resolve_effective_tps(bab, request) if is_current else bab.tujuan_pembelajaran
            bab_jp = _resolve_effective_alokasi_jp(bab, request) if is_current else bab.alokasi_jp

            p_b = doc.add_paragraph()
            p_b.paragraph_format.space_before = Pt(8)
            rb = p_b.add_run(f"BAB {bab.nomor_bab}: {bab.judul_bab.upper()} (Semester {bab.semester})")
            rb.bold = True
            rb.font.color.rgb = RGBColor(30, 58, 138)

            t_bab = doc.add_table(rows=1, cols=2)
            t_bab.alignment = WD_TABLE_ALIGNMENT.CENTER
            t_bab.rows[0].cells[0].text = "KATEGORI"
            t_bab.rows[0].cells[1].text = "RUMUSAN"
            self._format_header_cell(t_bab.rows[0].cells[0], width_mm=40)
            self._format_header_cell(t_bab.rows[0].cells[1], width_mm=120)

            # Row 1: Elemen
            r1 = t_bab.add_row().cells
            r1[0].text = "Elemen"
            r1[1].text = bab.elemen_cp or (elems[0]["nama_elemen"] if elems else "Pemahaman Konsep")
            r1[0].paragraphs[0].runs[0].bold = True

            # Row 2: Kalimat CP
            r2 = t_bab.add_row().cells
            r2[0].text = "Kalimat CP"
            r2[1].text = (
                f"Peserta didik mampu menguasai konsep {bab.judul_bab} pada elemen "
                f"{bab.elemen_cp or (elems[0]['nama_elemen'] if elems else 'Pemahaman Konsep')} serta menerapkannya secara kontekstual."
            )
            r2[0].paragraphs[0].runs[0].bold = True

            # Row 3: Tujuan Pembelajaran
            r3 = t_bab.add_row().cells
            r3[0].text = "Tujuan Pembelajaran"
            r3[0].paragraphs[0].runs[0].bold = True
            tp_lines = "\n".join(f"{i}. [{t.code}] {t.deskripsi} ({t.alokasi_jp} JP)" for i, t in enumerate(bab_tps, start=1))
            r3[1].text = tp_lines

            # Row 4: Alokasi Waktu
            r4 = t_bab.add_row().cells
            r4[0].text = "Alokasi Waktu"
            r4[1].text = f"{bab_jp} Jam Pelajaran (JP)"
            r4[0].paragraphs[0].runs[0].bold = True
            r4[1].paragraphs[0].runs[0].bold = True

            self._style_data_table(t_bab, [40, 120], has_header_row=True)

        if request.custom_overrides and request.custom_overrides.catatan_khusus:
            self._add_section_heading(doc, "Catatan Khusus Pemetaan")
            doc.add_paragraph(request.custom_overrides.catatan_khusus)

    # =========================================================================
    # 2. SERVICE 04: ALUR TUJUAN PEMBELAJARAN / ATP (1:1 with Live Preview)
    # =========================================================================
    def _build_atp(
        self,
        doc: Document,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        selected_chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
    ):
        self._add_kop_surat(doc, teacher)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(8)
        r1 = p.add_run("ALUR TUJUAN PEMBELAJARAN (ATP)\n")
        r1.bold = True
        r1.font.size = Pt(12)
        r2 = p.add_run(f"MATA PELAJARAN {subject.nama_mapel.upper()} — FASE {subject.fase} KELAS {subject.kelas}")
        r2.bold = True
        r2.font.size = Pt(11)

        # 1. Capaian Pembelajaran Fase Berdasarkan Elemen
        self._add_cp_fase_and_elemen_block(doc, subject)

        # 2. Rincian Alur Tujuan Pembelajaran Semester
        self._add_section_heading(doc, f"RINCIAN ALUR TUJUAN PEMBELAJARAN SEMESTER {request.semester}")
        chapters = subject.get_chapters_by_semester(request.semester) or subject.bab_list
        durasi_menit = getattr(subject, "durasi_1_jp_menit", 40)
        jp_per_minggu = max(1, subject.alokasi_jp_mingguan)
        ov = request.custom_overrides

        for bab in chapters:
            is_current = selected_chapter and bab.id == selected_chapter.id
            bab_tps = _resolve_effective_tps(bab, request) if is_current else bab.tujuan_pembelajaran
            bab_jp = _resolve_effective_alokasi_jp(bab, request) if is_current else bab.alokasi_jp
            pertemuan = max(1, round(bab_jp / jp_per_minggu))

            tpl_ch = getattr(bab, "modul_ajar_template", {}) or {}
            desain = tpl_ch.get("desain_pembelajaran", {})
            lamp = tpl_ch.get("lampiran", {})
            ident = tpl_ch.get("identifikasi", {})

            table = doc.add_table(rows=0, cols=2)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER

            # Header row (Title Bab)
            hdr_cell = table.add_row().cells
            hdr_cell[0].merge(hdr_cell[1])
            hdr_cell[0].text = f"BAB {bab.nomor_bab}: {bab.judul_bab.upper()} (SEMESTER {bab.semester})"
            self._format_header_cell(hdr_cell[0], width_mm=160)

            # Block Rows
            tp_list_str = "\n".join(f"{i}. {t.code}: {t.deskripsi} ({t.alokasi_jp} JP)" for i, t in enumerate(bab_tps, start=1))
            kata_kunci = lamp.get("kata_kunci") or f"{bab.judul_bab}, {bab.elemen_cp or 'Konsep Inti'}, Analisis Kontekstual"
            topik_kontekstual = (ov.topik_kontekstual if (is_current and ov and ov.topik_kontekstual) else None) or desain.get("topik_pembelajaran_kontekstual") or bab.judul_bab
            glosarium = lamp.get("glosarium") or f"{bab.judul_bab}: Lingkup kompetensi utama pada mata pelajaran {subject.nama_mapel} Kelas {subject.kelas}."
            dpl_str = ", ".join(bab.dimensi_profil_lulusan or ["Penalaran Kritis", "Kreativitas", "Kemandirian"])

            rows_data = [
                ("Elemen", bab.elemen_cp or "Pemahaman Konsep"),
                ("Capaian Pembelajaran Pertahun", f"Memahami, menerapkan, dan mengevaluasi konsep {bab.judul_bab} pada {subject.nama_mapel} Kelas {subject.kelas}."),
                (f"Fase {subject.fase} / Alur Tujuan Pembelajaran", tp_list_str),
                ("Jumlah Jam", f"{bab_jp} JP ({pertemuan} Pertemuan)"),
                ("Kata Kunci", kata_kunci),
                ("Topik / Konten Inti", topik_kontekstual),
                ("Glosarium", glosarium),
                ("Dimensi Profil Lulusan", dpl_str),
            ]

            for k, v in rows_data:
                rc = table.add_row().cells
                rc[0].text = k
                rc[1].text = str(v)
                self._format_header_cell(rc[0], width_mm=45)

            self._style_data_table(table, [45, 115], has_header_row=True)
            doc.add_paragraph()

        # Rasional & Catatan Khusus ATP
        p_ras = doc.add_paragraph()
        r_rh = p_ras.add_run("Rasional Penyusunan Alur Tujuan Pembelajaran: ")
        r_rh.bold = True
        p_ras.add_run(
            f"Penyusunan ATP {subject.nama_mapel} Kelas {subject.kelas} dilakukan secara berjenjang dari kompetensi "
            f"fondasi menuju aplikasi kontekstual dan evaluasi reflektif berbasis pendekatan Deep Learning 3M."
        )

        p_cat = doc.add_paragraph()
        r_ch = p_cat.add_run("Catatan khusus penggunaan alur tujuan pembelajaran: ")
        r_ch.bold = True
        cat_txt = (ov.catatan_khusus if (ov and ov.catatan_khusus) else None) or (
            "Penggunaan ATP ini dirancang fleksibel menyesuaikan diferensiasi kesiapan murid dan sarana penunjang di satuan pendidikan."
        )
        p_cat.add_run(cat_txt)

    # =========================================================================
    # 3. SERVICE 08: MODUL AJAR DEEP LEARNING (1:1 with Live Preview)
    # =========================================================================
    def _build_modul_ajar(
        self,
        doc: Document,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
        raw_template: Optional[dict],
    ):
        self._add_kop_surat(doc, teacher)

        ch = chapter or (subject.bab_list[0] if subject.bab_list else None)
        tpl = raw_template if isinstance(raw_template, dict) else (ch.modul_ajar_template if ch else {}) or {}
        ov = request.custom_overrides

        ident = tpl.get("identifikasi", {})
        desain = tpl.get("desain_pembelajaran", {})
        inti = tpl.get("komponen_inti", {})
        asesmen = tpl.get("asesmen", {})

        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_title.paragraph_format.space_after = Pt(8)
        run_title1 = p_title.add_run("MODUL AJAR DEEP LEARNING\n")
        run_title1.bold = True
        run_title1.font.size = Pt(12)
        run_title2 = p_title.add_run(
            f"{subject.nama_mapel.upper()} — BAB {ch.nomor_bab if ch else 1}: {(ch.judul_bab if ch else subject.nama_mapel).upper()}"
        )
        run_title2.bold = True
        run_title2.font.size = Pt(11)

        # A. Identitas Modul
        self._add_section_heading(doc, "A. Identitas Modul")
        alokasi_jp = _resolve_effective_alokasi_jp(ch, request)
        durasi_menit = getattr(subject, "durasi_1_jp_menit", 40)
        jp_per_minggu = max(1, subject.alokasi_jp_mingguan)
        tps_effective = _resolve_effective_tps(ch, request)
        pertemuan_count = max(len(tps_effective), max(1, round(alokasi_jp / jp_per_minggu)))

        id_table = doc.add_table(rows=0, cols=2)
        id_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        id_rows = [
            ("Nama Penyusun", f"{teacher.nama_guru} (NIP. {teacher.nip_guru})"),
            ("Institusi / Sekolah", teacher.nama_sekolah),
            ("Tahun Penyusunan / Semester", f"Tahun Ajaran 2025/2026 / Semester {request.semester} ({'Ganjil' if request.semester == 1 else 'Genap'})"),
            ("Jenjang / Fase / Kelas", f"{subject.jenjang} / Fase {subject.fase} / Kelas {subject.kelas}"),
            ("Mata Pelajaran", subject.nama_mapel),
            ("Bab / Materi Pokok", f"Bab {ch.nomor_bab if ch else 1}: {ch.judul_bab if ch else subject.nama_mapel}"),
            ("Alokasi Waktu", f"{alokasi_jp} JP ({pertemuan_count} Pertemuan × {jp_per_minggu} JP @ {durasi_menit} Menit)"),
        ]
        for k, v in id_rows:
            rc = id_table.add_row().cells
            rc[0].text = k
            rc[1].text = str(v)
            self._format_header_cell(rc[0], width_mm=45)
        self._style_data_table(id_table, [45, 115], has_header_row=False)

        # B. Identifikasi Kesiapan Peserta Didik
        self._add_section_heading(doc, "B. Identifikasi Kesiapan Peserta Didik")
        kesiapan_txt = (ov.kesiapan_murid if (ov and ov.kesiapan_murid) else None) or ident.get(
            "kesiapan_murid",
            f"Peserta didik Kelas {subject.kelas} (Fase {subject.fase}) umumnya telah memiliki pengetahuan dasar "
            f"terkait konsep {ch.judul_bab if ch else subject.nama_mapel}.",
        )
        doc.add_paragraph(kesiapan_txt)

        # C. Karakteristik Materi Pelajaran
        self._add_section_heading(doc, "C. KARAKTERISTIK MATERI PELAJARAN")
        karakteristik_txt = (ov.karakteristik_materi if (ov and ov.karakteristik_materi) else None) or ident.get(
            "karakteristik_materi",
            f"Materi '{ch.judul_bab if ch else subject.nama_mapel}' mencakup pengetahuan konseptual, prosedural, dan metakognitif yang aplikatif.",
        )
        doc.add_paragraph(karakteristik_txt)

        # D. Dimensi Profil Lulusan Pembelajaran
        self._add_section_heading(doc, "D. Dimensi Profil Lulusan Pembelajaran")
        active_dimensions = (ch.dimensi_profil_lulusan if ch else None) or ["Penalaran Kritis", "Kreativitas", "Kolaborasi", "Kemandirian"]
        d_table = doc.add_table(rows=1, cols=2)
        d_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        d_table.rows[0].cells[0].text = "Dimensi Profil Lulusan"
        d_table.rows[0].cells[1].text = "Implementasi pada Pembelajaran Bab Ini"
        self._format_header_cell(d_table.rows[0].cells[0], width_mm=45)
        self._format_header_cell(d_table.rows[0].cells[1], width_mm=115)
        for dim in active_dimensions:
            rc = d_table.add_row().cells
            rc[0].text = dim
            rc[1].text = f"Dikembangkan melalui aktivitas diskusi, eksplorasi konsep {ch.judul_bab if ch else subject.nama_mapel}, dan refleksi pemecahan masalah."
            rc[0].paragraphs[0].runs[0].bold = True
        self._style_data_table(d_table, [45, 115], has_header_row=True)

        # DESAIN PEMBELAJARAN
        self._add_section_heading(doc, "DESAIN PEMBELAJARAN")
        des_table = doc.add_table(rows=0, cols=2)
        des_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # A. Capaian Pembelajaran (CP)
        cp_bab_str = desain.get("capaian_pembelajaran_bab") or (
            subject.elemen_cp_resmi[0]["deskripsi_cp"] if getattr(subject, "elemen_cp_resmi", None) else f"Peserta didik mampu menguasai materi {ch.judul_bab if ch else subject.nama_mapel}."
        )
        elemen_name = ch.elemen_cp if ch else "Pemahaman Konsep"
        rc_cp = des_table.add_row().cells
        rc_cp[0].text = "A. Capaian Pembelajaran (CP)"
        rc_cp[1].text = f"Elemen {elemen_name}: {cp_bab_str}"
        self._format_header_cell(rc_cp[0], width_mm=45)
        rc_cp[1].width = Mm(115)

        # B. Lintas Disiplin Ilmu
        lintas_txt = (ov.lintas_disiplin_ilmu if (ov and ov.lintas_disiplin_ilmu) else None) or desain.get(
            "lintas_disiplin_ilmu",
            "Bahasa Indonesia (literasi & presentasi); Matematika (logika berpikir & kalkulasi); Sains & IPS (konteks sosial & etika teknologi).",
        )
        rc_ld = des_table.add_row().cells
        rc_ld[0].text = "B. LINTAS DISIPLIN ILMU YANG RELEVAN"
        rc_ld[1].text = lintas_txt
        self._format_header_cell(rc_ld[0], width_mm=45)
        rc_ld[1].width = Mm(115)

        # C. Tujuan Pembelajaran (TP)
        tp_lines = "\n".join(f"{idx}. Pertemuan {idx} [{tp.code}]: {tp.deskripsi} ({tp.alokasi_jp} JP)" for idx, tp in enumerate(tps_effective, start=1))
        rc_tp = des_table.add_row().cells
        rc_tp[0].text = "C. Tujuan Pembelajaran (TP)"
        rc_tp[1].text = tp_lines
        self._format_header_cell(rc_tp[0], width_mm=45)
        rc_tp[1].width = Mm(115)

        # D. Topik Pembelajaran Kontekstual
        topik_txt = (ov.topik_kontekstual if (ov and ov.topik_kontekstual) else None) or desain.get(
            "topik_pembelajaran_kontekstual",
            f"Penerapan nyata materi {ch.judul_bab if ch else subject.nama_mapel} dalam memecahkan persoalan kontekstual sehari-hari.",
        )
        rc_tk = des_table.add_row().cells
        rc_tk[0].text = "D. TOPIK PEMBELAJARAN KONTEKSTUAL"
        rc_tk[1].text = topik_txt
        self._format_header_cell(rc_tk[0], width_mm=45)
        rc_tk[1].width = Mm(115)

        # E. Kerangka Pembelajaran
        pemantik_list = (ov.pertanyaan_pemantik if (ov and ov.pertanyaan_pemantik) else None) or inti.get("pertanyaan_pemantik", [
            f"Bagaimana konsep {ch.judul_bab if ch else subject.nama_mapel} dapat membantu menyelesaikan persoalan di dunia nyata?"
        ])
        model_pedagogis = request.model_pembelajaran or "Inquiry Based Learning (Mendalam/DL)"
        rc_kp = des_table.add_row().cells
        rc_kp[0].text = "E. Kerangka Pembelajaran"
        rc_kp[1].text = f"Model Pedagogis: {model_pedagogis}\nPertanyaan Pemantik: {' | '.join(pemantik_list)}"
        self._format_header_cell(rc_kp[0], width_mm=45)
        self._style_data_table(des_table, [45, 115], has_header_row=False)

        # F. Langkah-Langkah Pembelajaran Berdiferensiasi (Deep Learning 3M)
        self._add_section_heading(doc, "F. LANGKAH-LANGKAH PEMBELAJARAN BERDIFERENSIASI (PENDEKATAN DEEP LEARNING 3M)")
        pb = inti.get("pengalaman_belajar", {})
        memahami_steps = (ov.langkah_memahami if (ov and ov.langkah_memahami) else None) or (ov.langkah_inti_memahami if (ov and ov.langkah_inti_memahami) else None) or pb.get("tahap_memahami", [f"Peserta didik mengeksplorasi konsep dan literatur terkait {ch.judul_bab if ch else subject.nama_mapel}."])
        mengaplikasi_steps = (ov.langkah_mengaplikasi if (ov and ov.langkah_mengaplikasi) else None) or (ov.langkah_inti_mengaplikasi if (ov and ov.langkah_inti_mengaplikasi) else None) or pb.get("tahap_mengaplikasi", [f"Peserta didik bekerja dalam kelompok mengerjakan studi kasus / LKPD tentang {ch.judul_bab if ch else subject.nama_mapel}."])
        merefleksi_steps = (ov.langkah_merefleksi if (ov and ov.langkah_merefleksi) else None) or (ov.langkah_inti_merefleksi if (ov and ov.langkah_inti_merefleksi) else None) or pb.get("tahap_merefleksi", ["Kelompok mempresentasikan hasil karya dan melakukan evaluasi pemahaman bersama guru."])

        for idx, tp in enumerate(tps_effective):
            q_pemantik = pemantik_list[idx % len(pemantik_list)]
            step_m = memahami_steps[idx % len(memahami_steps)]
            step_a = mengaplikasi_steps[idx % len(mengaplikasi_steps)]
            step_r = merefleksi_steps[idx % len(merefleksi_steps)]

            t_step = doc.add_table(rows=0, cols=2)
            t_step.alignment = WD_TABLE_ALIGNMENT.CENTER

            # Header Pertemuan
            hdr = t_step.add_row().cells
            hdr[0].merge(hdr[1])
            hdr[0].text = f"PERTEMUAN {idx + 1} — Fokus TP: [{tp.code}] {tp.deskripsi} ({tp.alokasi_jp} JP)"
            self._format_header_cell(hdr[0], width_mm=160)

            # Row 1: Pendahuluan
            r_pend = t_step.add_row().cells
            r_pend[0].text = "1. Kegiatan Pendahuluan (15%)"
            r_pend[1].text = (
                f"Guru membuka kelas dengan salam, doa, presensi, apersepsi mengaitkan pengalaman nyata siswa "
                f"dengan topik {ch.judul_bab if ch else subject.nama_mapel}, serta menyampaikan pertanyaan pemantik: \"{q_pemantik}\"."
            )
            self._format_header_cell(r_pend[0], width_mm=45)
            r_pend[1].width = Mm(115)

            # Row 2: Inti 3M
            r_inti = t_step.add_row().cells
            r_inti[0].text = "2. Kegiatan Inti — Memahami, Mengaplikasi, Merefleksi (70%)"
            r_inti[1].text = (
                f"• Memahami (Mindful Learning): {step_m}\n"
                f"• Mengaplikasi (Meaningful Learning): {step_a}\n"
                f"• Merefleksi (Joyful Learning): {step_r}"
            )
            self._format_header_cell(r_inti[0], width_mm=45)
            r_inti[1].width = Mm(115)

            # Row 3: Penutup
            r_pen = t_step.add_row().cells
            r_pen[0].text = "3. Kegiatan Penutup (15%)"
            r_pen[1].text = (
                f"Peserta didik bersama guru menyimpulkan poin penting pertemuan {idx + 1}, "
                f"melakukan refleksi singkat, dan menerima informasi materi pertemuan berikutnya."
            )
            self._format_header_cell(r_pen[0], width_mm=45)

            self._style_data_table(t_step, [45, 115], has_header_row=True)
            doc.add_paragraph()

        # G. Asesmen Pembelajaran & Butir Soal
        if request.include_asesmen:
            self._add_section_heading(doc, "G. Asesmen Pembelajaran & Butir Soal")
            t_as = doc.add_table(rows=1, cols=2)
            t_as.alignment = WD_TABLE_ALIGNMENT.CENTER
            t_as.rows[0].cells[0].text = "Jenis Asesmen"
            t_as.rows[0].cells[1].text = "Teknik & Butir Soal Instrumen"
            self._format_header_cell(t_as.rows[0].cells[0], width_mm=45)
            self._format_header_cell(t_as.rows[0].cells[1], width_mm=115)

            soal_awal = (ov.soal_asesmen_awal if (ov and ov.soal_asesmen_awal) else None) or asesmen.get("soal_asesmen_awal", [
                f"Apa yang kamu ketahui mengenai konsep {ch.judul_bab if ch else subject.nama_mapel}?",
                "Sebutkan contoh penerapan nyata materi ini yang pernah kamu amati di lingkungan sekitarmu!",
            ])
            soal_proses = (ov.soal_asesmen_proses if (ov and ov.soal_asesmen_proses) else None) or asesmen.get("soal_asesmen_proses", [
                f"Kerjakan investigasi kelompok pada LKPD materi {ch.judul_bab if ch else subject.nama_mapel}!",
                "Diskusikan argumen pemecahan masalah dan presentasikan di depan kelas!",
            ])
            soal_akhir = (ov.soal_asesmen_akhir if (ov and ov.soal_asesmen_akhir) else None) or asesmen.get("soal_asesmen_akhir", [
                f"Evaluasi komparatif studi kasus implementasi {ch.judul_bab if ch else subject.nama_mapel}!",
                "Simpulkan solusi optimal berdasarkan hasil analisis data!",
            ])

            r_a1 = t_as.add_row().cells
            r_a1[0].text = "1. Asesmen Awal (Diagnostik)"
            r_a1[1].text = "Soal Asesmen Awal:\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(soal_awal, start=1))
            r_a1[0].paragraphs[0].runs[0].bold = True

            r_a2 = t_as.add_row().cells
            r_a2[0].text = "2. Asesmen Proses (Formatif)"
            r_a2[1].text = "Soal Asesmen Proses:\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(soal_proses, start=1))
            r_a2[0].paragraphs[0].runs[0].bold = True

            r_a3 = t_as.add_row().cells
            r_a3[0].text = "3. Asesmen Akhir (Sumatif)"
            r_a3[1].text = "Soal Asesmen Akhir Bab:\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(soal_akhir, start=1))
            r_a3[0].paragraphs[0].runs[0].bold = True

            self._style_data_table(t_as, [45, 115], has_header_row=True)

        # H. Lampiran 1: Lembar Kerja Peserta Didik (LKPD)
        lampiran = tpl.get("lampiran", {})
        if request.include_lkpd:
            doc.add_page_break()
            self._add_section_heading(doc, "H. Lampiran 1: Lembar Kerja Peserta Didik (LKPD)", level=1)
            lkpd = lampiran.get("lkpd", {})
            judul_lkpd = (ov.judul_lkpd if (ov and ov.judul_lkpd) else None) or lkpd.get("judul_lkpd") or f"LKPD: {ch.judul_bab if ch else subject.nama_mapel} (Deep Learning 3M)"
            tujuan_lkpd = (ov.tujuan_lkpd if (ov and ov.tujuan_lkpd) else None) or lkpd.get("tujuan_aktivitas") or f"Mengembangkan penguasaan konsep dan pemecahan masalah materi {ch.judul_bab if ch else subject.nama_mapel}."

            p_lk = doc.add_paragraph()
            p_lk.add_run(f"Judul LKPD: {judul_lkpd}\n").bold = True
            p_lk.add_run(f"Tujuan: {tujuan_lkpd}\n")
            langkah_kustom = (ov.langkah_lkpd if (ov and ov.langkah_lkpd) else None) or lkpd.get("langkah_kerja")
            if langkah_kustom:
                p_lk.add_run("Langkah Kerja:\n")
                for s in langkah_kustom:
                    doc.add_paragraph(f"• {s}")

            # Identitas LKPD
            t_id = doc.add_table(rows=2, cols=4)
            r_id0 = t_id.rows[0].cells
            r_id0[0].text = "Nama Kelompok / Kelas"
            r_id0[1].text = f"......................... / Kelas {request.kelas}"
            r_id0[2].text = "Hari, Tanggal"
            r_id0[3].text = "........................."
            r_id1 = t_id.rows[1].cells
            r_id1[0].text = "Anggota Kelompok"
            r_id1[1].text = "1. ..................... 2. ..................... 3. ..................... 4. ....................."
            r_id1[1].merge(r_id1[2])
            r_id1[1].merge(r_id1[3])
            r_id0[0].paragraphs[0].runs[0].bold = True
            r_id0[2].paragraphs[0].runs[0].bold = True
            r_id1[0].paragraphs[0].runs[0].bold = True
            self._style_data_table(t_id, [40, 40, 40, 40], has_header_row=False)

            petunjuk_text = (ov.petunjuk_lkpd if (ov and ov.petunjuk_lkpd) else None)
            p_petunjuk = doc.add_paragraph()
            p_petunjuk.add_run("\nPetunjuk Pengerjaan:\n").bold = True
            if petunjuk_text:
                for line in petunjuk_text.split("\n"):
                    if line.strip():
                        p_petunjuk.add_run(f"{line.strip()}\n")
            else:
                p_petunjuk.add_run("1. Berdoalah sebelum memulai kegiatan bersama anggota kelompok Anda.\n")
                p_petunjuk.add_run("2. Bacalah dengan cermat instruksi pemecahan masalah dan bahan ajar yang diberikan.\n")
                p_petunjuk.add_run("3. Bekerjasamalah secara aktif dan selesaikan tugas-tugas di bawah ini dengan tepat waktu.\n")

            # Tabel Tugas Aktivitas LKPD 3M
            t_lkpd = doc.add_table(rows=4, cols=3)
            hdr_lk = t_lkpd.rows[0].cells
            hdr_lk[0].text = "No"
            hdr_lk[1].text = "Tahap Aktivitas (3M)"
            hdr_lk[2].text = "Instruksi Tugas & Lembar Kerja Siswa"
            for c in hdr_lk:
                c.paragraphs[0].runs[0].bold = True

            tahap1_instruksi = (
                (ov.tugas_lkpd_memahami if ov and ov.tugas_lkpd_memahami else None)
                or (ov.langkah_inti_memahami[0] if ov and ov.langkah_inti_memahami else None)
                or (tpl.get("pembelajaran_mendalam_3m", {}).get("memahami") if tpl else None)
                or f"Pahamilah konsep dasar materi {ch.judul_bab if ch else subject.nama_mapel}. Tuliskan intisari pengertian dan prinsip utamanya!"
            )

            tahap2_instruksi = (
                (ov.tugas_lkpd_mengaplikasi if ov and ov.tugas_lkpd_mengaplikasi else None)
                or (ov.langkah_inti_mengaplikasi[0] if ov and ov.langkah_inti_mengaplikasi else None)
                or (tpl.get("pembelajaran_mendalam_3m", {}).get("mengaplikasi") if tpl else None)
                or f"Diskusikan bersama kelompok studi kasus kontekstual penerapan {ch.judul_bab if ch else subject.nama_mapel}. Tuliskan langkah-langkah solusinya!"
            )

            tahap3_instruksi = (
                (ov.tugas_lkpd_merefleksi if ov and ov.tugas_lkpd_merefleksi else None)
                or (ov.langkah_inti_merefleksi[0] if ov and ov.langkah_inti_merefleksi else None)
                or (tpl.get("pembelajaran_mendalam_3m", {}).get("merefleksi") if tpl else None)
                or "Simpulkan manfaat pembelajaran hari ini dan hal apa yang masih perlu diperdalam pada pertemuan selanjutnya!"
            )

            r_lk1 = t_lkpd.rows[1].cells
            r_lk1[0].text = "1"
            r_lk1[1].text = "Memahami\n(Eksplorasi Konsep)"
            r_lk1[2].text = f"{tahap1_instruksi}\n\n[Ruang Jawaban / Intisari Konsep Siswa]\n................................................................................................."

            r_lk2 = t_lkpd.rows[2].cells
            r_lk2[0].text = "2"
            r_lk2[1].text = "Mengaplikasi\n(Praktik & Kasus)"
            r_lk2[2].text = f"{tahap2_instruksi}\n\n[Ruang Analisis & Langkah Solusi Siswa]\n................................................................................................."

            r_lk3 = t_lkpd.rows[3].cells
            r_lk3[0].text = "3"
            r_lk3[1].text = "Merefleksi\n(Evaluasi Diri)"
            r_lk3[2].text = f"{tahap3_instruksi}\n\n[Ruang Refleksi & Kesimpulan Siswa]\n................................................................................................."

            self._style_data_table(t_lkpd, [15, 45, 100], has_header_row=True)

        # I. Lampiran 2: Rubrik Asesmen 8 Dimensi Profil Lulusan (Permendikdasmen No. 10/2025)
        if request.include_rubrik:
            doc.add_page_break()
            self._add_section_heading(doc, "I. Lampiran 2: Rubrik Asesmen 8 Dimensi Profil Lulusan (Permendikdasmen No. 10/2025)", level=1)
            p_desc = doc.add_paragraph()
            p_desc.add_run("Rubrik Observasi Ketercapaian Standar Kompetensi Lulusan (8 Dimensi Profil Lulusan):\n").bold = True

            default_dpl = [
                ("1", "Keimanan & Ketakwaan terhadap Tuhan YME", "Berdoa sebelum/sesudah belajar, bersikap jujur, dan peduli lingkungan sekitar."),
                ("2", "Kewargaan & Cinta Tanah Air", "Menghargai keberagaman budaya, menaati kesepakatan kelas, dan toleran."),
                ("3", "Penalaran Kritis", "Berpikir logis, analitis, mengolah data objektif, dan menarik kesimpulan berbasis bukti."),
                ("4", "Kreativitas", "Menghasilkan gagasan inovatif, fleksibel, serta menyajikan karya pemecahan masalah orisinal."),
                ("5", "Kolaborasi", "Bekerja sama secara aktif dalam kelompok, berbagi peran adil, dan saling membantu rekan."),
                ("6", "Kemandirian", "Bertanggung jawab atas proses belajar sendiri, inisiatif tinggi, dan tuntas tepat waktu."),
                ("7", "Kesehatan & Kebugaran", "Menjaga kebersihan dan keselamatan saat praktik, serta mengelola emosi secara positif."),
                ("8", "Komunikasi", "Menyimak aktif, mempresentasikan hasil karya secara runtut, dan menanggapi dengan santun."),
            ]

            active_dpl = []
            if ov and ov.custom_rubrik_dpl:
                for item in ov.custom_rubrik_dpl:
                    if item.is_active:
                        active_dpl.append((str(item.no), item.nama_dimensi, item.indikator))
            if not active_dpl:
                active_dpl = default_dpl

            t_dpl = doc.add_table(rows=len(active_dpl) + 1, cols=7)
            hdr_d = t_dpl.rows[0].cells
            hdr_d[0].text = "No"
            hdr_d[1].text = "Dimensi Profil Lulusan"
            hdr_d[2].text = "Indikator Perilaku Amatan di Kelas"
            hdr_d[3].text = "MB"
            hdr_d[4].text = "B"
            hdr_d[5].text = "BSH"
            hdr_d[6].text = "SB"
            for c in hdr_d:
                c.paragraphs[0].runs[0].bold = True
                self._format_header_cell(c, width_mm=10)
            self._format_header_cell(hdr_d[1], width_mm=45)
            self._format_header_cell(hdr_d[2], width_mm=65)

            for idx, (no_str, nama_dim, ind_dim) in enumerate(active_dpl, start=1):
                r_d = t_dpl.rows[idx].cells
                r_d[0].text = no_str
                r_d[1].text = nama_dim
                r_d[2].text = ind_dim
                r_d[3].text = "[  ]"
                r_d[4].text = "[  ]"
                r_d[5].text = "[  ]"
                r_d[6].text = "[  ]"
                r_d[1].paragraphs[0].runs[0].bold = True
                for ci in [0, 3, 4, 5, 6]:
                    r_d[ci].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

            self._style_data_table(t_dpl, [10, 45, 65, 10, 10, 10, 10], has_header_row=True)

            p_ket = doc.add_paragraph()
            p_ket.add_run("* Keterangan Skala Observasi Guru: MB = Mulai Berkembang (1), B = Berkembang (2), BSH = Berkembang Sesuai Harapan (3), SB = Sangat Berkembang (4).").italic = True
            p_cat = doc.add_paragraph()
            p_cat.add_run("Catatan Observasi Guru: ......................................................................................................................................").italic = True

        # Glosarium & Bahan Bacaan (jika tersedia)
        if lampiran.get("glosarium") or lampiran.get("bahan_bacaan_guru_dan_siswa"):
            p_sup = doc.add_paragraph()
            if lampiran.get("glosarium"):
                p_sup.add_run("\nGlosarium: ").bold = True
                p_sup.add_run(str(lampiran["glosarium"]) + "\n")
            if lampiran.get("bahan_bacaan_guru_dan_siswa"):
                p_sup.add_run("Bahan Bacaan Guru & Siswa: ").bold = True
                p_sup.add_run(str(lampiran["bahan_bacaan_guru_dan_siswa"]) + "\n")

    # =========================================================================
    # 4. SERVICE 05: PROGRAM TAHUNAN / PROTA (1:1 with Live Preview)
    # =========================================================================
    def _build_prota(
        self,
        doc: Document,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        selected_chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
    ):
        self._add_kop_surat(doc, teacher)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(8)
        r1 = p.add_run("PROGRAM TAHUNAN (PROTA)\n")
        r1.bold = True
        r1.font.size = Pt(12)
        r2 = p.add_run(
            f"MATA PELAJARAN {subject.nama_mapel.upper()} — KELAS {subject.kelas} (FASE {subject.fase}) TAHUN AJARAN 2025/2026"
        )
        r2.bold = True
        r2.font.size = Pt(11)

        # 1. Capaian Pembelajaran Fase Berdasarkan Elemen
        self._add_cp_fase_and_elemen_block(doc, subject)

        # 2. Tabel Distribusi Alokasi Waktu Tahunan (5 Kolom)
        self._add_section_heading(doc, "DISTRIBUSI ALOKASI WAKTU TAHUNAN (SEMESTER 1 & SEMESTER 2)")
        table = doc.add_table(rows=1, cols=5)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        headers = ["SEMESTER", "NO", "MATERI POKOK / JUDUL BAB & TUJUAN PEMBELAJARAN", "ALOKASI (JP)", "KETERANGAN"]
        widths = [20, 10, 84, 22, 24]
        for i, (h, w) in enumerate(zip(headers, widths)):
            table.rows[0].cells[i].text = h
            self._format_header_cell(table.rows[0].cells[i], width_mm=w)
            if i in (0, 1, 3, 4):
                table.rows[0].cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        total_jp = 0
        jp_per_minggu = max(1, subject.alokasi_jp_mingguan)
        ov = request.custom_overrides

        for idx, bab in enumerate(subject.bab_list, start=1):
            is_current = selected_chapter and bab.id == selected_chapter.id
            bab_tps = _resolve_effective_tps(bab, request) if is_current else bab.tujuan_pembelajaran
            bab_jp = _resolve_effective_alokasi_jp(bab, request) if is_current else bab.alokasi_jp
            pertemuan = max(1, round(bab_jp / jp_per_minggu))
            total_jp += bab_jp

            rc = table.add_row().cells
            rc[0].text = f"SEMESTER {bab.semester}"
            rc[1].text = str(idx)

            tp_lines = "\n".join(f"• [{t.code}] {t.deskripsi} ({t.alokasi_jp} JP)" for t in bab_tps)
            rc[2].text = f"Bab {bab.nomor_bab}: {bab.judul_bab}\n{tp_lines}"
            rc[3].text = f"{bab_jp} JP"
            rc[4].text = f"{pertemuan} Pertemuan"

            rc[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            rc[0].paragraphs[0].runs[0].bold = True
            rc[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            rc[1].paragraphs[0].runs[0].bold = True
            rc[2].paragraphs[0].runs[0].bold = True
            rc[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            rc[3].paragraphs[0].runs[0].bold = True
            rc[4].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Cadangan JP Row
        cadangan_jp = (ov.cadangan_jp if (ov and ov.cadangan_jp is not None) else 0)
        rc_cad = table.add_row().cells
        rc_cad[0].text = ""
        rc_cad[1].text = ""
        rc_cad[2].text = "Cadangan Jam Pelajaran"
        rc_cad[3].text = f"{cadangan_jp} JP"
        rc_cad[4].text = "Pengayaan / STS / SAS"

        rc_cad[2].paragraphs[0].runs[0].bold = True
        rc_cad[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        rc_cad[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        rc_cad[3].paragraphs[0].runs[0].bold = True
        rc_cad[4].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Total JP Row
        rc_tot = table.add_row().cells
        rc_tot[0].text = ""
        rc_tot[1].text = ""
        rc_tot[2].text = "Jumlah Jam Pelajaran Tahunan"
        rc_tot[3].text = f"{total_jp + cadangan_jp} JP"
        rc_tot[4].text = "1 Tahun Ajaran"

        for c in rc_tot:
            self._format_header_cell(c)
        rc_tot[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        rc_tot[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        rc_tot[4].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._style_data_table(table, [20, 10, 84, 22, 24], has_header_row=True)

    # =========================================================================
    # 5. SERVICE 06: PROGRAM SEMESTER / PROMES (1:1 with Live Preview)
    # =========================================================================
    def _build_promes(
        self,
        doc: Document,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        selected_chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
    ):
        self._add_kop_surat(doc, teacher)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(8)
        r1 = p.add_run(
            f"PROGRAM SEMESTER (PROMES) — SEMESTER {request.semester} ({'GANJIL' if request.semester == 1 else 'GENAP'})\n"
        )
        r1.bold = True
        r1.font.size = Pt(12)
        r2 = p.add_run(
            f"MATA PELAJARAN {subject.nama_mapel.upper()} — KELAS {subject.kelas} (FASE {subject.fase}) TAHUN AJARAN 2025/2026"
        )
        r2.bold = True
        r2.font.size = Pt(11)

        # 1. Capaian Pembelajaran Fase Berdasarkan Elemen
        self._add_cp_fase_and_elemen_block(doc, subject)

        # 2. Matriks Distribusi Minggu Efektif Semester
        self._add_section_heading(doc, f"MATRIKS DISTRIBUSI MINGGU EFEKTIF SEMESTER {request.semester}")
        months = ["JUL", "AGU", "SEP", "OKT", "NOV", "DES"] if request.semester == 1 else ["JAN", "FEB", "MAR", "APR", "MEI", "JUN"]
        table = doc.add_table(rows=1, cols=3 + len(months) + 1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        headers = ["NO", "BAB / TUJUAN PEMBELAJARAN (TP)", "JP"] + months + ["KET"]
        for i, h in enumerate(headers):
            table.rows[0].cells[i].text = h
            self._format_header_cell(table.rows[0].cells[i])
            if i != 1:
                table.rows[0].cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        chapters = subject.get_chapters_by_semester(request.semester) or subject.bab_list
        for b_idx, bab in enumerate(chapters):
            is_current = selected_chapter and bab.id == selected_chapter.id
            bab_tps = _resolve_effective_tps(bab, request) if is_current else bab.tujuan_pembelajaran
            bab_jp = _resolve_effective_alokasi_jp(bab, request) if is_current else bab.alokasi_jp

            # Bab Subheader Row
            r_bab = table.add_row().cells
            r_bab[0].text = str(b_idx + 1)
            r_bab[1].text = f"BAB {bab.nomor_bab}: {bab.judul_bab.upper()}"
            r_bab[2].text = str(bab_jp)
            for m_i in range(len(months)):
                r_bab[3 + m_i].text = ""
            r_bab[-1].text = "Intrakurikuler"

            for c in r_bab:
                self._format_header_cell(c)
            r_bab[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_bab[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_bab[-1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

            # TP Rows
            for t_idx, tp in enumerate(bab_tps):
                target_month_idx = (b_idx * 2 + t_idx) % len(months)
                r_tp = table.add_row().cells
                r_tp[0].text = f"{b_idx + 1}.{t_idx + 1}"
                r_tp[1].text = f"[{tp.code}] {tp.deskripsi}"
                r_tp[2].text = str(tp.alokasi_jp)

                for m_i in range(len(months)):
                    r_tp[3 + m_i].text = str(tp.alokasi_jp) if m_i == target_month_idx else "-"
                    r_tp[3 + m_i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

                r_tp[-1].text = "TM"
                r_tp[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_tp[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_tp[-1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        self._style_data_table(table, [10, 68, 12, 10, 10, 10, 10, 10, 10, 10], has_header_row=True)

    def _add_doc_title(self, doc: Document, title: str, subtitle: str) -> None:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(8)
        r1 = p.add_run(f"{title}\n")
        r1.bold = True
        r1.font.size = Pt(12)
        r2 = p.add_run(subtitle)
        r2.bold = True
        r2.font.size = Pt(11)

    def _build_kktp(
        self,
        doc: Document,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
    ):
        """Builds Service 07: Kriteria Ketercapaian Tujuan Pembelajaran (KKTP) PPA Revisi 2025."""
        self._add_kop_surat(doc, teacher)
        fase_label = subject.fase
        self._add_doc_title(
            doc,
            "KRITERIA KETERCAPAIAN TUJUAN PEMBELAJARAN (KKTP)",
            f"MATA PELAJARAN {subject.nama_mapel.upper()} — FASE {fase_label} (KELAS {subject.kelas})",
        )

        # Identitas Dokumen
        id_table = doc.add_table(rows=4, cols=2)
        id_rows = [
            ("Nama Penyusun", f"{teacher.nama_guru} (NIP. {teacher.nip_guru})"),
            ("Satuan Pendidikan", teacher.nama_sekolah),
            ("Mata Pelajaran / Kelas", f"{subject.nama_mapel} / Kelas {subject.kelas} (Fase {fase_label})"),
            ("Semester / Tahun Ajaran", f"Semester {request.semester} / 2025–2026"),
        ]
        for idx, (k, v) in enumerate(id_rows):
            id_table.rows[idx].cells[0].text = k
            id_table.rows[idx].cells[1].text = v
            for p in id_table.rows[idx].cells[0].paragraphs:
                for r in p.runs:
                    r.bold = True
        self._style_data_table(id_table, [45, 115], has_header_row=False)

        # A. Interval Nilai 4 Skala PPA Revisi 2025
        self._add_section_heading(doc, "A. Pendekatan Interval Nilai (4 Skala PPA Revisi 2025)")
        intervals = [
            ("0 – 60", "Perlu Bimbingan (D)", "Belum mencapai ketuntasan, memerlukan remedial di seluruh bagian."),
            ("61 – 74", "Cukup (C)", "Belum mencapai ketuntasan, remedial di bagian yang diperlukan."),
            ("75 – 87", "Baik (B)", "Sudah mencapai ketuntasan (KKTP), tidak perlu remedial."),
            ("88 – 100", "Sangat Baik (A)", "Sudah mencapai ketuntasan sangat baik, perlu pengayaan atau tantangan lebih."),
        ]
        int_tbl = doc.add_table(rows=len(intervals) + 1, cols=3)
        int_headers = ["Interval Nilai", "Predikat / Kriteria", "Tindak Lanjut & Deskripsi Rapor"]
        for c_i, h in enumerate(int_headers):
            int_tbl.rows[0].cells[c_i].text = h
        for idx, (rng, pred, tl) in enumerate(intervals, start=1):
            int_tbl.rows[idx].cells[0].text = rng
            int_tbl.rows[idx].cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            int_tbl.rows[idx].cells[1].text = pred
            int_tbl.rows[idx].cells[2].text = tl
        self._style_data_table(int_tbl, [30, 44, 86], has_header_row=True)

        # B. Rubrik Kriteria Ketercapaian per Tujuan Pembelajaran (TP)
        self._add_section_heading(doc, "B. Rubrik Kriteria Ketercapaian per Tujuan Pembelajaran (TP)")
        target_chapters = [chapter] if chapter else [c for c in subject.bab_list if c.semester == request.semester]
        if not target_chapters:
            target_chapters = subject.bab_list[:2]

        tp_rows = []
        for ch in target_chapters:
            for tp in _resolve_effective_tps(ch, request):
                tp_rows.append((ch.nomor_bab, tp.code, tp.deskripsi))

        rub_tbl = doc.add_table(rows=len(tp_rows) + 1, cols=5)
        rub_headers = [
            "Kode & Rumusan TP",
            "Baru Berkembang (0–60)",
            "Layak (61–74)",
            "Cakap (75–87)",
            "Mahir (88–100)",
        ]
        for c_i, h in enumerate(rub_headers):
            rub_tbl.rows[0].cells[c_i].text = h
        for idx, (no_bab, code, desc) in enumerate(tp_rows, start=1):
            rub_tbl.rows[idx].cells[0].text = f"[{code}] (Bab {no_bab}) {desc}"
            rub_tbl.rows[idx].cells[1].text = "Memerlukan bimbingan penuh dalam memahami konsep dasar."
            rub_tbl.rows[idx].cells[2].text = "Mampu menjelaskan konsep dasar namun belum konsisten."
            rub_tbl.rows[idx].cells[3].text = "Mampu menerapkan konsep secara mandiri dan tepat (Tuntas)."
            rub_tbl.rows[idx].cells[4].text = "Mampu menganalisis, mengevaluasi, dan memecahkan kasus kompleks."
        self._style_data_table(rub_tbl, [44, 29, 29, 29, 29], has_header_row=True)

    def _build_lkpd(
        self,
        doc: Document,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
        tpl: Optional[dict] = None,
    ):
        """Builds Service 09: Lembar Kerja Peserta Didik Mandiri (LKPD)."""
        self._add_kop_surat(doc, teacher)
        ch = chapter or (subject.bab_list[0] if subject.bab_list else None)
        fase_label = subject.fase
        bab_title = ch.judul_bab if ch else subject.nama_mapel
        self._add_doc_title(
            doc,
            "LEMBAR KERJA PESERTA DIDIK (LKPD) MANDIRI",
            f"MATA PELAJARAN {subject.nama_mapel.upper()} — FASE {fase_label} (KELAS {subject.kelas})",
        )

        # Kotak Identitas Siswa
        stu_tbl = doc.add_table(rows=4, cols=2)
        stu_rows = [
            ("Nama Peserta Didik", "............................................................"),
            ("Kelas / No. Absen", f"Kelas {subject.kelas} / No. Absen: ........"),
            ("Bab / Materi Pokok", f"Bab {ch.nomor_bab}: {bab_title}" if ch else bab_title),
            ("Guru Pengampu", f"{teacher.nama_guru} ({teacher.nama_sekolah})"),
        ]
        for idx, (k, v) in enumerate(stu_rows):
            stu_tbl.rows[idx].cells[0].text = k
            stu_tbl.rows[idx].cells[1].text = v
            for p in stu_tbl.rows[idx].cells[0].paragraphs:
                for r in p.runs:
                    r.bold = True
        self._style_data_table(stu_tbl, [45, 115], has_header_row=False)

        # A. Tujuan Pembelajaran
        self._add_section_heading(doc, "A. Tujuan Pembelajaran")
        tps = _resolve_effective_tps(ch, request) if ch else []
        tp_tbl = doc.add_table(rows=max(1, len(tps)) + 1, cols=2)
        tp_tbl.rows[0].cells[0].text = "Kode TP"
        tp_tbl.rows[0].cells[1].text = "Rumusan Tujuan Pembelajaran"
        if tps:
            for idx, tp in enumerate(tps, start=1):
                tp_tbl.rows[idx].cells[0].text = tp.code
                tp_tbl.rows[idx].cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                tp_tbl.rows[idx].cells[1].text = tp.deskripsi
        else:
            tp_tbl.rows[1].cells[0].text = "TP.1"
            tp_tbl.rows[1].cells[1].text = f"Peserta didik mampu memahami dan menerapkan materi {bab_title}."
        self._style_data_table(tp_tbl, [25, 135], has_header_row=True)

        # B. Petunjuk Pengerjaan & Aktivitas 3M
        self._add_section_heading(doc, "B. Petunjuk Belajar & Langkah Aktivitas (3M)")
        ov = request.custom_overrides
        topik = (ov.topik_kontekstual if ov and ov.topik_kontekstual else None) or (
            tpl.get("topik_kontekstual") if tpl else None
        ) or f"Penerapan materi {bab_title} dalam kehidupan sehari-hari."
        lkpd_steps = (ov.langkah_lkpd if ov and ov.langkah_lkpd else None) or (
            tpl.get("langkah_lkpd") if tpl else None
        ) or [
            f"1. Memahami: Baca dan amati topik kontekstual '{topik}' secara cermat.",
            "2. Mengaplikasi: Diskusikan bersama kelompok atau kerjakan langkah pemecahan masalah pada lembar berikut.",
            "3. Merefleksi: Tuliskan kesimpulan dan refleksi pemahaman Anda setelah menyelesaikan aktivitas.",
        ]

        act_tbl = doc.add_table(rows=len(lkpd_steps) + 2, cols=2)
        act_tbl.rows[0].cells[0].text = "Tahap / Komponen"
        act_tbl.rows[0].cells[1].text = "Uraian Aktivitas & Ruang Jawaban Siswa"
        act_tbl.rows[1].cells[0].text = "Topik Kontekstual"
        act_tbl.rows[1].cells[1].text = topik
        for idx, step in enumerate(lkpd_steps, start=2):
            act_tbl.rows[idx].cells[0].text = f"Langkah {idx - 1}"
            act_tbl.rows[idx].cells[1].text = f"{step}\n\nJawaban / Catatan Siswa:\n............................................................................................"
        self._style_data_table(act_tbl, [40, 120], has_header_row=True)

        # C. Soal Latihan / Asesmen Mandiri
        self._add_section_heading(doc, "C. Pertanyaan Pemahaman & Latihan Mandiri")
        soal_list = (ov.soal_asesmen_proses if ov and ov.soal_asesmen_proses else None) or (
            tpl.get("soal_asesmen_proses") if tpl else None
        ) or [
            f"Jelaskan konsep utama dari materi {bab_title} dengan bahasa Anda sendiri!",
            f"Berikan satu contoh penerapan nyata {bab_title} di lingkungan sekitar Anda!",
        ]
        soal_tbl = doc.add_table(rows=len(soal_list) + 1, cols=2)
        soal_tbl.rows[0].cells[0].text = "No."
        soal_tbl.rows[0].cells[1].text = "Pertanyaan & Lembar Jawaban"
        for idx, q in enumerate(soal_list, start=1):
            soal_tbl.rows[idx].cells[0].text = str(idx)
            soal_tbl.rows[idx].cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            soal_tbl.rows[idx].cells[1].text = f"{q}\nJawaban: ......................................................................................."
        self._style_data_table(soal_tbl, [14, 146], has_header_row=True)

    def _add_page_number_to_footer(self, section):
        """Adds standard right-aligned 'Halaman X' page number field to section footer."""
        footer = section.footer
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)

        r = p.add_run("Halaman ")
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.font.italic = True
        r.font.color.rgb = RGBColor(100, 116, 139)

        fldSimple = parse_xml(
            f'<w:fldSimple {nsdecls("w")} w:instr="PAGE">'
            f'<w:r>'
            f'<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="18"/><w:i/></w:rPr>'
            f'<w:t>1</w:t>'
            f'</w:r>'
            f'</w:fldSimple>'
        )
        p._p.append(fldSimple)

    def _add_section_heading(self, doc: Document, title: str, level: Optional[int] = None):
        """Adds official Heading 1 or Heading 2 paragraph compatible with Microsoft Word & WPS Navigation Pane."""
        if level is None:
            if any(k in title.upper() for k in ["LAMPIRAN", "DESAIN PEMBELAJARAN", "INFORMASI UMUM", "RINCIAN ALUR", "DISTRIBUSI ALOKASI", "MATRIKS DISTRIBUSI", "LANGKAH-LANGKAH PEMBELAJARAN"]):
                level = 1
            elif re.match(r"^[A-Z]\.\s", title) or re.match(r"^\d+\.\s", title):
                level = 2
            else:
                level = 1

        style_name = f"Heading {level}" if level in (1, 2) else "Heading 1"
        p = doc.add_paragraph(style=style_name)
        p.paragraph_format.space_before = Pt(10 if level == 1 else 8)
        p.paragraph_format.space_after = Pt(3 if level == 1 else 2)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(12 if level == 1 else 11)
        r.font.color.rgb = RGBColor(15, 23, 42) if level == 1 else RGBColor(30, 58, 138)
        return p

    def _add_lembar_pengesahan(self, doc: Document, teacher: TeacherProfile):
        doc.add_page_break()
        pengesahan = teacher.get_lembar_pengesahan()

        p_titi = doc.add_paragraph()
        p_titi.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_titi.paragraph_format.space_after = Pt(4)
        p_titi.add_run(pengesahan["titimangsa"])

        table = doc.add_table(rows=3, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        table.rows[0].cells[0].text = pengesahan["jabatan_kepala"]
        table.rows[0].cells[1].text = pengesahan["jabatan_guru"]
        table.rows[1].cells[0].text = "\n\n\n"
        table.rows[1].cells[1].text = "\n\n\n"
        table.rows[2].cells[0].text = f"{pengesahan['nama_kepala_sekolah']}\n{pengesahan['nip_kepala_sekolah']}"
        table.rows[2].cells[1].text = f"{pengesahan['nama_guru']}\n{pengesahan['nip_guru']}"
        for row in table.rows:
            for c_idx, cell in enumerate(row.cells):
                cell.width = Mm(78)
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(2)

    def _style_data_table(self, table, col_widths_mm: List[float], has_header_row: bool = True):
        """Applies crisp XML borders, cell padding, fixed column widths, and tight paragraph spacing to content tables."""
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        tbl_pr = table._tbl.tblPr
        # Set total table width and fixed layout
        total_dxa = int(sum(col_widths_mm) * 56.6929)
        for tag in ("w:tblW", "w:tblLayout", "w:tblBorders"):
            existing = tbl_pr.find(qn(tag))
            if existing is not None:
                tbl_pr.remove(existing)

        tbl_pr.append(parse_xml(f'<w:tblW {nsdecls("w")} w:w="{total_dxa}" w:type="dxa"/>'))
        tbl_pr.append(parse_xml(f'<w:tblLayout {nsdecls("w")} w:type="fixed"/>'))
        tbl_pr.append(
            parse_xml(
                f'<w:tblBorders {nsdecls("w")}>'
                f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="94A3B8"/>'
                f'  <w:left w:val="single" w:sz="4" w:space="0" w:color="94A3B8"/>'
                f'  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="94A3B8"/>'
                f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="94A3B8"/>'
                f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="94A3B8"/>'
                f'  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="94A3B8"/>'
                f'</w:tblBorders>'
            )
        )

        # Enforce tblGrid exact column widths
        tbl_grid = table._tbl.tblGrid
        if tbl_grid is not None:
            for gcol in list(tbl_grid):
                tbl_grid.remove(gcol)
            for w_mm in col_widths_mm:
                w_dxa = int(w_mm * 56.6929)
                tbl_grid.append(parse_xml(f'<w:gridCol {nsdecls("w")} w:w="{w_dxa}"/>'))

        for r_idx, row in enumerate(table.rows):
            tr_pr = row._tr.get_or_add_trPr()
            if tr_pr.find(qn("w:cantSplit")) is None:
                tr_pr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
            if has_header_row and r_idx == 0 and tr_pr.find(qn("w:tblHeader")) is None:
                tr_pr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

            seen_tcs = set()
            for c_idx, cell in enumerate(row.cells):
                tc_id = id(cell._tc)
                if tc_id in seen_tcs:
                    continue
                seen_tcs.add(tc_id)

                # Calculate spanned width if merged across columns
                tc_pr = cell._tc.get_or_add_tcPr()
                grid_span_el = tc_pr.find(qn("w:gridSpan"))
                span = int(grid_span_el.get(qn("w:val"))) if grid_span_el is not None else 1
                w_slice = col_widths_mm[c_idx : c_idx + span]
                if w_slice:
                    w_dxa = int(sum(w_slice) * 56.6929)
                    existing_w = tc_pr.find(qn("w:tcW"))
                    if existing_w is not None:
                        tc_pr.remove(existing_w)
                    tc_pr.append(parse_xml(f'<w:tcW {nsdecls("w")} w:w="{w_dxa}" w:type="dxa"/>'))

                cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
                existing_mar = tc_pr.find(qn("w:tcMar"))
                if existing_mar is not None:
                    tc_pr.remove(existing_mar)
                tc_pr.append(
                    parse_xml(
                        f'<w:tcMar {nsdecls("w")}>'
                        f'  <w:top w:w="90" w:type="dxa"/>'
                        f'  <w:left w:w="130" w:type="dxa"/>'
                        f'  <w:bottom w:w="90" w:type="dxa"/>'
                        f'  <w:right w:w="130" w:type="dxa"/>'
                        f'</w:tcMar>'
                    )
                )

                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(2)
                    p.paragraph_format.line_spacing = 1.15
                    for r in p.runs:
                        if r.font.size is None:
                            r.font.size = Pt(9.5)

    def _format_header_cell(self, cell, width_mm: Optional[int] = None):
        if width_mm:
            cell.width = Mm(width_mm)
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="E2E8F0"/>')
        tcPr.append(shd)
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(9.5)

    def _build_exam_document(
        self,
        doc: Document,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
    ):
        """Builds Word document for Service 10 (Kuis), 11 (Sumatif Bab), and 12 (STS/SAS)."""
        bp = QuestionBlueprintEngine.build_blueprint(request, subject, chapter)
        letters = QuestionBlueprintEngine.OPTION_LETTERS

        if request.service_id == ServiceIdEnum.KUIS:
            main_title = "KUIS HARIAN & PENILAIAN FORMATIF"
        elif request.service_id == ServiceIdEnum.SUMATIF_BAB:
            main_title = "ASESMEN SUMATIF LINGKUP MATERI (BAB)"
        else:
            main_title = f"PENILAIAN {bp['jenis_ujian']} (SUMATIF SEMESTER) — PAKET {bp['paket_soal']}"

        self._add_doc_title(doc, main_title, f"{subject.nama_mapel} | {subject.jenjang} Kelas {subject.kelas} | Semester {request.semester}")

        # Identitas Ujian
        id_table = doc.add_table(rows=4, cols=2)
        id_rows = [
            ("Mata Pelajaran / Fase", f"{subject.nama_mapel} ({subject.fase})"),
            ("Lingkup Materi / Bab", ", ".join(c.judul_bab for c in bp["chapters"][:3]) or subject.nama_mapel),
            ("Alokasi Waktu / Paket", f"{bp['alokasi_waktu_menit']} Menit | Paket {bp['paket_soal']} ({bp['pg_count']} PG, {bp['uraian_count']} Uraian)"),
            ("Nama Siswa / Kelas", ".................................................... / Kelas ......................"),
        ]
        for idx, (k, v) in enumerate(id_rows):
            id_table.cell(idx, 0).text = k
            id_table.cell(idx, 1).text = v
        self._style_data_table(id_table, [50, 110], has_header_row=False)

        # Kisi-Kisi 7 Kolom (S11 & S12)
        if request.service_id in (ServiceIdEnum.SUMATIF_BAB, ServiceIdEnum.STS_SAS):
            self._add_section_heading(doc, "A. Kisi-Kisi Penulisan Soal (7 Kolom)")
            k_table = doc.add_table(rows=len(bp["kisi_kisi"]) + 1, cols=7)
            k_headers = ["No", "TP", "Materi", "Indikator Soal", "Level", "Bentuk", "No Soal"]
            for c_i, h_text in enumerate(k_headers):
                k_table.cell(0, c_i).text = h_text
                self._format_header_cell(k_table.cell(0, c_i))
            for r_i, row in enumerate(bp["kisi_kisi"], start=1):
                k_table.cell(r_i, 0).text = str(row["no"])
                k_table.cell(r_i, 1).text = row["tp_code"]
                k_table.cell(r_i, 2).text = row["materi"][:35]
                k_table.cell(r_i, 3).text = row["indikator"][:65]
                k_table.cell(r_i, 4).text = row["level_kognitif"]
                k_table.cell(r_i, 5).text = row["bentuk_soal"]
                k_table.cell(r_i, 6).text = row["nomor_soal"]
            self._style_data_table(k_table, [10, 20, 28, 52, 18, 18, 14], has_header_row=True)

        # Kartu Soal (khusus S12)
        if request.service_id == ServiceIdEnum.STS_SAS and bp["questions"]:
            self._add_section_heading(doc, "B. Kartu Soal & Telaah Butir")
            ks_table = doc.add_table(rows=min(len(bp["questions"]), 10) + 1, cols=4)
            for c_i, h_text in enumerate(["No", "TP & Level", "Rumusan Indikator", "Kunci & Skor"]):
                ks_table.cell(0, c_i).text = h_text
                self._format_header_cell(ks_table.cell(0, c_i))
            for r_i, q in enumerate(bp["questions"][:10], start=1):
                ks_table.cell(r_i, 0).text = str(q["no"])
                ks_table.cell(r_i, 1).text = f"{q['tp_code']}\n({q['level_kognitif']})"
                ks_table.cell(r_i, 2).text = q["indikator"][:90]
                ks_table.cell(r_i, 3).text = f"Kunci: {q['kunci_jawaban'][:25]}\nSkor: {q['bobot_skor']}"
            self._style_data_table(ks_table, [12, 34, 78, 36], has_header_row=True)

        # Naskah Soal (Terpisah: A. Soal Pilihan Ganda & B. Soal Essai)
        doc.add_page_break()
        self._add_section_heading(doc, "Naskah Soal Evaluasi")
        p_petunjuk = doc.add_paragraph("Petunjuk Umum: Berdoalah sebelum mengerjakan. Pilih jawaban yang paling tepat pada Bagian A dan jawablah secara runtut pada Bagian B.")
        p_petunjuk.paragraph_format.space_after = Pt(6)

        if bp["pg_questions"]:
            self._add_section_heading(doc, "A. Soal Pilihan Ganda", level=2)
            for q in bp["pg_questions"]:
                if q.get("stimulus"):
                    p_stim = doc.add_paragraph(q["stimulus"])
                    p_stim.paragraph_format.space_after = Pt(2)

                p_q = doc.add_paragraph()
                r_no = p_q.add_run(f"{q['section_no']}. ")
                r_no.bold = True
                p_q.add_run(q["pertanyaan"])
                p_q.paragraph_format.space_after = Pt(2)

                for o_idx, opt_text in enumerate(q.get("opsi") or []):
                    letter = letters[o_idx] if o_idx < len(letters) else str(o_idx + 1)
                    p_opt = doc.add_paragraph(f"    {letter}. {opt_text}")
                    p_opt.paragraph_format.space_after = Pt(1)

        if bp["essai_questions"]:
            self._add_section_heading(doc, "B. Soal Essai", level=2)
            for q in bp["essai_questions"]:
                if q.get("stimulus"):
                    p_stim = doc.add_paragraph(q["stimulus"])
                    p_stim.paragraph_format.space_after = Pt(2)

                p_q = doc.add_paragraph()
                r_no = p_q.add_run(f"{q['section_no']}. ")
                r_no.bold = True
                p_q.add_run(q["pertanyaan"])
                p_q.paragraph_format.space_after = Pt(2)

                p_ans_line = doc.add_paragraph("    Jawaban: _________________________________________________________________")
                p_ans_line.paragraph_format.space_after = Pt(4)

        # Kunci Jawaban & Pedoman Penskoran (Halaman Terpisah)
        doc.add_page_break()
        self._add_section_heading(doc, "Kunci Jawaban & Pedoman Penskoran")
        ans_table = doc.add_table(rows=len(bp["questions"]) + 2, cols=4)
        for c_i, h_text in enumerate(["No", "Bentuk & Level", "Kunci Jawaban & Pembahasan", "Skor Maks"]):
            ans_table.cell(0, c_i).text = h_text
            self._format_header_cell(ans_table.cell(0, c_i))
        for r_i, q in enumerate(bp["questions"], start=1):
            ans_table.cell(r_i, 0).text = f"{q['bagian']}.{q['section_no']}"
            bentuk_label = "PG" if q["tipe_soal"] == "PG" else "Essai"
            ans_table.cell(r_i, 1).text = f"{bentuk_label} ({q['level_kognitif']})"
            pemb = f" — {q['pembahasan']}" if q.get("pembahasan") else ""
            ans_table.cell(r_i, 2).text = f"{q['kunci_jawaban']}{pemb}"
            ans_table.cell(r_i, 3).text = str(q["bobot_skor"])
        last_r = len(bp["questions"]) + 1
        ans_table.cell(last_r, 0).text = "-"
        ans_table.cell(last_r, 1).text = "TOTAL"
        ans_table.cell(last_r, 2).text = "Nilai Akhir = (Skor Diperoleh / 100) x 100"
        ans_table.cell(last_r, 3).text = str(bp["total_skor_maksimal"])
        self._style_data_table(ans_table, [12, 32, 96, 20], has_header_row=True)

        # Lembar Jawab (LJK) khusus S12
        if request.service_id == ServiceIdEnum.STS_SAS:
            doc.add_page_break()
            self._add_section_heading(doc, "Lembar Jawab Peserta Didik (LJK)")
            ljk_info = doc.add_paragraph("Nama: ..............................................   No. Ujian: ....................   Kelas: ............")
            ljk_info.paragraph_format.space_after = Pt(6)
            pg_qs = [q for q in bp["questions"] if q["tipe_soal"] == "PG"]
            if pg_qs:
                ljk_tbl = doc.add_table(rows=len(pg_qs) + 1, cols=2)
                ljk_tbl.cell(0, 0).text = "No"
                ljk_tbl.cell(0, 1).text = "Pilihan Jawaban (Silang / Lingkari)"
                self._format_header_cell(ljk_tbl.cell(0, 0))
                self._format_header_cell(ljk_tbl.cell(0, 1))
                for r_i, q in enumerate(pg_qs, start=1):
                    opts_str = "    ".join(f"[ {letters[i]} ]" for i in range(max(4, len(q.get("opsi") or []))))
                    ljk_tbl.cell(r_i, 0).text = str(q["no"])
                    ljk_tbl.cell(r_i, 1).text = opts_str
                self._style_data_table(ljk_tbl, [20, 140], has_header_row=True)
