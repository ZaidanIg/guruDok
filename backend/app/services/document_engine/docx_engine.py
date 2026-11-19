import io
import re
from typing import Optional, List, Dict, Any
from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn

from app.core.exceptions import DocumentGenerationError
from app.models.curriculum import CurriculumSubject, ChapterTopic, LearningObjective
from app.models.teacher import TeacherProfile
from app.schemas.generation import DocumentGenerateRequest, ServiceIdEnum
from app.services.document_engine.base_engine import DocumentEngine


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

            style = doc.styles["Normal"]
            font = style.font
            font.name = "Arial"
            font.size = Pt(10)
            font.color.rgb = RGBColor(15, 23, 42)

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

        p_line = doc.add_paragraph()
        p_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_line.paragraph_format.space_after = Pt(10)
        r_line = p_line.add_run("―" * 58)
        r_line.bold = True
        r_line.font.color.rgb = RGBColor(15, 23, 42)

    def _add_cp_fase_and_elemen_block(self, doc: Document, subject: CurriculumSubject):
        """Renders the official CAPAIAN PEMBELAJARAN FASE and Fase Berdasarkan Elemen table."""
        self._add_section_heading(doc, f"Capaian Pembelajaran Fase {subject.fase} Berdasarkan Elemen")
        elems = getattr(subject, "elemen_cp_resmi", []) or []
        tbl = doc.add_table(rows=1, cols=2)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.rows[0].cells[0].text = "Elemen"
        tbl.rows[0].cells[1].text = "Capaian Pembelajaran"
        self._format_header_cell(tbl.rows[0].cells[0], width_mm=45)
        self._format_header_cell(tbl.rows[0].cells[1], width_mm=135)

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
        self._style_data_table(tbl, [44, 130], has_header_row=True)
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
            self._format_header_cell(rc[0], width_mm=50)
        self._style_data_table(id_table, [50, 124], has_header_row=False)

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
        self._format_header_cell(t_aims.rows[0].cells[1], width_mm=168)
        for idx, aim_str in enumerate(aims_list, start=1):
            rc = t_aims.add_row().cells
            rc[0].text = str(idx)
            rc[1].text = aim_str
            rc[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            rc[0].paragraphs[0].runs[0].bold = True
        self._style_data_table(t_aims, [14, 160], has_header_row=True)

        # 3. Karakteristik & 4. Capaian Pembelajaran Fase Berdasarkan Elemen
        self._add_section_heading(doc, f"3. Karakteristik Mata Pelajaran & 4. Capaian Pembelajaran Fase {subject.fase} Berdasarkan Elemen")
        karakteristik = getattr(subject, "karakteristik_bskap", "") or (
            f"Mata pelajaran {subject.nama_mapel} menerapkan pendekatan pembelajaran mendalam (Deep Learning 3M) yang mengintegrasikan "
            f"pemahaman konsep, keterampilan proses, dan refleksi kontekstual."
        )
        doc.add_paragraph(karakteristik)

        elems = getattr(subject, "elemen_cp_resmi", []) or []
        t_kar = doc.add_table(rows=1, cols=2)
        t_kar.alignment = WD_TABLE_ALIGNMENT.CENTER
        t_kar.rows[0].cells[0].text = "Elemen"
        t_kar.rows[0].cells[1].text = "Deskripsi Capaian Pembelajaran Resmi (BSKAP 046/2025)"
        self._format_header_cell(t_kar.rows[0].cells[0], width_mm=45)
        self._format_header_cell(t_kar.rows[0].cells[1], width_mm=135)
        if elems:
            for e in elems:
                rc = t_kar.add_row().cells
                rc[0].text = str(e.get("nama_elemen", "-"))
                rc[1].text = str(e.get("deskripsi_cp", "-"))
                rc[0].paragraphs[0].runs[0].bold = True
        self._style_data_table(t_kar, [44, 130], has_header_row=True)

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
            self._format_header_cell(t_bab.rows[0].cells[0], width_mm=45)
            self._format_header_cell(t_bab.rows[0].cells[1], width_mm=135)

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

            self._style_data_table(t_bab, [44, 130], has_header_row=True)

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
            self._format_header_cell(hdr_cell[0], width_mm=180)

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
                self._format_header_cell(rc[0], width_mm=52)

            self._style_data_table(table, [52, 122], has_header_row=True)
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
            self._format_header_cell(rc[0], width_mm=50)
        self._style_data_table(id_table, [50, 124], has_header_row=False)

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
        self._format_header_cell(d_table.rows[0].cells[0], width_mm=50)
        self._format_header_cell(d_table.rows[0].cells[1], width_mm=130)
        for dim in active_dimensions:
            rc = d_table.add_row().cells
            rc[0].text = dim
            rc[1].text = f"Dikembangkan melalui aktivitas diskusi, eksplorasi konsep {ch.judul_bab if ch else subject.nama_mapel}, dan refleksi pemecahan masalah."
            rc[0].paragraphs[0].runs[0].bold = True
        self._style_data_table(d_table, [50, 124], has_header_row=True)

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
        self._format_header_cell(rc_cp[0], width_mm=50)
        rc_cp[1].width = Mm(130)

        # B. Lintas Disiplin Ilmu
        lintas_txt = (ov.lintas_disiplin_ilmu if (ov and ov.lintas_disiplin_ilmu) else None) or desain.get(
            "lintas_disiplin_ilmu",
            "Bahasa Indonesia (literasi & presentasi); Matematika (logika berpikir & kalkulasi); Sains & IPS (konteks sosial & etika teknologi).",
        )
        rc_ld = des_table.add_row().cells
        rc_ld[0].text = "B. LINTAS DISIPLIN ILMU YANG RELEVAN"
        rc_ld[1].text = lintas_txt
        self._format_header_cell(rc_ld[0], width_mm=50)
        rc_ld[1].width = Mm(130)

        # C. Tujuan Pembelajaran (TP)
        tp_lines = "\n".join(f"{idx}. Pertemuan {idx} [{tp.code}]: {tp.deskripsi} ({tp.alokasi_jp} JP)" for idx, tp in enumerate(tps_effective, start=1))
        rc_tp = des_table.add_row().cells
        rc_tp[0].text = "C. Tujuan Pembelajaran (TP)"
        rc_tp[1].text = tp_lines
        self._format_header_cell(rc_tp[0], width_mm=50)
        rc_tp[1].width = Mm(130)

        # D. Topik Pembelajaran Kontekstual
        topik_txt = (ov.topik_kontekstual if (ov and ov.topik_kontekstual) else None) or desain.get(
            "topik_pembelajaran_kontekstual",
            f"Penerapan nyata materi {ch.judul_bab if ch else subject.nama_mapel} dalam memecahkan persoalan kontekstual sehari-hari.",
        )
        rc_tk = des_table.add_row().cells
        rc_tk[0].text = "D. TOPIK PEMBELAJARAN KONTEKSTUAL"
        rc_tk[1].text = topik_txt
        self._format_header_cell(rc_tk[0], width_mm=50)
        rc_tk[1].width = Mm(130)

        # E. Kerangka Pembelajaran
        pemantik_list = (ov.pertanyaan_pemantik if (ov and ov.pertanyaan_pemantik) else None) or inti.get("pertanyaan_pemantik", [
            f"Bagaimana konsep {ch.judul_bab if ch else subject.nama_mapel} dapat membantu menyelesaikan persoalan di dunia nyata?"
        ])
        model_pedagogis = request.model_pembelajaran or "Inquiry Based Learning (Mendalam/DL)"
        rc_kp = des_table.add_row().cells
        rc_kp[0].text = "E. Kerangka Pembelajaran"
        rc_kp[1].text = f"Model Pedagogis: {model_pedagogis}\nPertanyaan Pemantik: {' | '.join(pemantik_list)}"
        self._format_header_cell(rc_kp[0], width_mm=50)
        self._style_data_table(des_table, [50, 124], has_header_row=False)

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
            self._format_header_cell(hdr[0], width_mm=180)

            # Row 1: Pendahuluan
            r_pend = t_step.add_row().cells
            r_pend[0].text = "1. Kegiatan Pendahuluan (15%)"
            r_pend[1].text = (
                f"Guru membuka kelas dengan salam, doa, presensi, apersepsi mengaitkan pengalaman nyata siswa "
                f"dengan topik {ch.judul_bab if ch else subject.nama_mapel}, serta menyampaikan pertanyaan pemantik: \"{q_pemantik}\"."
            )
            self._format_header_cell(r_pend[0], width_mm=50)
            r_pend[1].width = Mm(130)

            # Row 2: Inti 3M
            r_inti = t_step.add_row().cells
            r_inti[0].text = "2. Kegiatan Inti — Memahami, Mengaplikasi, Merefleksi (70%)"
            r_inti[1].text = (
                f"• Memahami (Mindful Learning): {step_m}\n"
                f"• Mengaplikasi (Meaningful Learning): {step_a}\n"
                f"• Merefleksi (Joyful Learning): {step_r}"
            )
            self._format_header_cell(r_inti[0], width_mm=50)
            r_inti[1].width = Mm(130)

            # Row 3: Penutup
            r_pen = t_step.add_row().cells
            r_pen[0].text = "3. Kegiatan Penutup (15%)"
            r_pen[1].text = (
                f"Peserta didik bersama guru menyimpulkan poin penting pertemuan {idx + 1}, "
                f"melakukan refleksi singkat, dan menerima informasi materi pertemuan berikutnya."
            )
            self._format_header_cell(r_pen[0], width_mm=48)

            self._style_data_table(t_step, [48, 126], has_header_row=True)
            doc.add_paragraph()

        # G. Asesmen Pembelajaran & Butir Soal
        if request.include_asesmen:
            self._add_section_heading(doc, "G. Asesmen Pembelajaran & Butir Soal")
            t_as = doc.add_table(rows=1, cols=2)
            t_as.alignment = WD_TABLE_ALIGNMENT.CENTER
            t_as.rows[0].cells[0].text = "Jenis Asesmen"
            t_as.rows[0].cells[1].text = "Teknik & Butir Soal Instrumen"
            self._format_header_cell(t_as.rows[0].cells[0], width_mm=50)
            self._format_header_cell(t_as.rows[0].cells[1], width_mm=130)

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

            self._style_data_table(t_as, [48, 126], has_header_row=True)

        # H. Lampiran (LKPD, Glosarium & Bahan Bacaan)
        lampiran = tpl.get("lampiran", {})
        if (request.include_lkpd or request.include_rubrik) and lampiran:
            self._add_section_heading(doc, "H. Lampiran: Lembar Kerja Peserta Didik (LKPD), Glosarium & Bahan Bacaan")
            lkpd = lampiran.get("lkpd", {})
            if lkpd:
                p_lk = doc.add_paragraph()
                p_lk.add_run(f"Judul LKPD: {lkpd.get('judul_lkpd', 'Lembar Aktivitas Siswa')}\n").bold = True
                if lkpd.get("tujuan_aktivitas"):
                    p_lk.add_run(f"Tujuan: {lkpd.get('tujuan_aktivitas')}\n")
                for s in lkpd.get("langkah_kerja", []):
                    doc.add_paragraph(f"• {s}")
            glosarium = lampiran.get("glosarium")
            if glosarium:
                p_glo = doc.add_paragraph()
                p_glo.add_run("Glosarium: ").bold = True
                p_glo.add_run(str(glosarium))
            bahan = lampiran.get("bahan_bacaan_guru_dan_siswa")
            if bahan:
                p_bah = doc.add_paragraph()
                p_bah.add_run("Bahan Bacaan Guru dan Siswa: ").bold = True
                p_bah.add_run(str(bahan))

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
        widths = [24, 12, 94, 22, 28]
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
        self._style_data_table(table, [24, 12, 90, 22, 26], has_header_row=True)

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

        self._style_data_table(table, [12, 74, 12, 10, 10, 10, 10, 10, 10, 16], has_header_row=True)

    def _add_section_heading(self, doc: Document, title: str):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(title)
        r.bold = True
        r.font.size = Pt(10.5)
        r.font.color.rgb = RGBColor(30, 58, 138)

    def _add_lembar_pengesahan(self, doc: Document, teacher: TeacherProfile):
        doc.add_paragraph().paragraph_format.space_before = Pt(14)
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
                cell.width = Mm(87)
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
