import io
from collections import OrderedDict
from typing import Optional, List, Dict, Any
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

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


class XlsxDocumentEngine(DocumentEngine):
    """Engine responsible for generating Microsoft Excel (.xlsx) documents with active formulas & 26-week calendar."""

    def generate(
        self,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
        raw_template: Optional[dict] = None,
    ) -> bytes:
        try:
            if request.service_id == ServiceIdEnum.PROMES:
                return self._generate_promes_xlsx(request, subject, teacher, raw_template)
            if request.service_id == ServiceIdEnum.KKTP:
                return self._generate_kktp_xlsx(request, subject, chapter, teacher)
            return self._generate_structured_curriculum_xlsx(request, subject, chapter, teacher, raw_template)
        except Exception as e:
            raise DocumentGenerationError(f"Failed to generate Excel document: {str(e)}")

    def _generate_promes_xlsx(
        self,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        teacher: TeacherProfile,
        raw_template: Optional[dict],
    ) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Promes Smtr {request.semester}"

        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.sheet_properties.pageSetUpPr.fitToPage = True

        title_font = Font(name="Arial", size=13, bold=True, color="0F172A")
        sub_font = Font(name="Arial", size=10, bold=True, color="334155")
        header_font = Font(name="Arial", size=9.5, bold=True, color="0F172A")
        data_font = Font(name="Arial", size=9, color="1E293B")
        bold_font = Font(name="Arial", size=9, bold=True, color="0F172A")
        agenda_font = Font(name="Arial", size=8, bold=True, color="92400E")

        header_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
        month_fill = PatternFill(start_color="CBD5E1", end_color="CBD5E1", fill_type="solid")
        total_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        agenda_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")

        thin_border_side = Side(style="thin", color="94A3B8")
        cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)

        # 1. School Header & CP Fase Block
        kop = teacher.get_formatted_kop()
        ws.cell(row=1, column=1, value=f"PROGRAM SEMESTER ( PROSEM ) — FASE {subject.fase} KELAS {subject.kelas}").font = title_font
        ws.cell(row=2, column=1, value=f"Satuan Pendidikan: {kop['nama_sekolah']} | Mata Pelajaran: {subject.nama_mapel.upper()}").font = sub_font
        ws.cell(
            row=3,
            column=1,
            value=f"Kelas / Semester: {subject.kelas} (Fase {subject.fase}) / Semester {request.semester} ({'Ganjil' if request.semester == 1 else 'Genap'}) | Tahun Penyusunan: 2026/2027",
        ).font = sub_font
        elems_summary = " | ".join(
            f"{e.get('nama_elemen')}: {e.get('deskripsi_cp', '')[:90]}..."
            for e in (getattr(subject, "elemen_cp_resmi", []) or [])
        )
        ws.cell(row=4, column=1, value=f"Capaian Pembelajaran Fase {subject.fase} Berdasarkan Elemen: {elems_summary}").font = data_font

        # 2. Table Headers (Row 5 & 6)
        ws.merge_cells("A5:A6")
        ws.cell(row=5, column=1, value="No").alignment = center_align

        ws.merge_cells("B5:B6")
        ws.cell(row=5, column=2, value="Bab / Lingkup Materi").alignment = center_align

        ws.merge_cells("C5:C6")
        ws.cell(row=5, column=3, value="Tujuan Pembelajaran (TP)").alignment = center_align

        ws.merge_cells("D5:D6")
        ws.cell(row=5, column=4, value="Alokasi\nJP").alignment = center_align

        # Extract 26 calendar weeks from GuruDocDB if provided in raw_template, else build default 26-week calendar
        calendar_weeks: List[Dict[str, Any]] = []
        if isinstance(raw_template, dict) and raw_template.get("calendar_weeks"):
            calendar_weeks = raw_template["calendar_weeks"]

        if calendar_weeks:
            months_dict: "OrderedDict[str, List[Dict[str, Any]]]" = OrderedDict()
            for cw in calendar_weeks:
                m_name = cw["month_name"]
                months_dict.setdefault(m_name, []).append(cw)
        else:
            default_months = (
                [("Juli", 5), ("Agustus", 4), ("September", 4), ("Oktober", 5), ("November", 4), ("Desember", 4)]
                if request.semester == 1
                else [("Januari", 4), ("Februari", 4), ("Maret", 5), ("April", 4), ("Mei", 4), ("Juni", 5)]
            )
            months_dict = OrderedDict()
            for m_name, count in default_months:
                months_dict[m_name] = [
                    {"month_name": m_name, "week_in_month": w, "week_status": "EFEKTIF", "table_code": "JP"}
                    for w in range(1, count + 1)
                ]

        col_idx = 5
        week_columns_meta: List[Dict[str, Any]] = []  # (col_number, week_status, table_code)
        for month_name, weeks_list in months_dict.items():
            num_weeks = len(weeks_list)
            end_col = col_idx + num_weeks - 1
            start_letter = get_column_letter(col_idx)
            end_letter = get_column_letter(end_col)

            ws.merge_cells(f"{start_letter}5:{end_letter}5")
            m_cell = ws.cell(row=5, column=col_idx, value=month_name)
            m_cell.alignment = center_align
            m_cell.font = bold_font
            m_cell.fill = month_fill

            for offset, w_meta in enumerate(weeks_list):
                c_num = col_idx + offset
                w_cell = ws.cell(row=6, column=c_num, value=str(w_meta["week_in_month"]))
                w_cell.alignment = center_align
                w_cell.font = header_font
                w_cell.fill = header_fill
                ws.column_dimensions[get_column_letter(c_num)].width = 4.5
                week_columns_meta.append(
                    {
                        "col": c_num,
                        "status": w_meta.get("week_status", "EFEKTIF"),
                        "code": w_meta.get("table_code", "JP"),
                    }
                )

            col_idx += num_weeks

        for r in range(5, 7):
            for c in range(1, col_idx):
                cell = ws.cell(row=r, column=c)
                cell.border = cell_border
                if not cell.fill.start_color.rgb:
                    cell.fill = header_fill
                    cell.font = header_font

        # 3. Populate TP Rows & Distribute JP only on EFEKTIF weeks, marking non-effective weeks with agenda codes
        current_row = 7
        chapters = subject.get_chapters_by_semester(request.semester) or subject.bab_list

        effective_cols = [wm["col"] for wm in week_columns_meta if wm["status"] == "EFEKTIF"]
        non_effective_meta = [wm for wm in week_columns_meta if wm["status"] != "EFEKTIF"]

        row_num = 1
        eff_ptr = 0

        for ch in chapters:
            is_current = (request.chapter_id and ch.id == request.chapter_id)
            ch_tps = _resolve_effective_tps(ch, request) if is_current else ch.tujuan_pembelajaran
            for tp in ch_tps:
                ws.cell(row=current_row, column=1, value=row_num).alignment = center_align
                ws.cell(row=current_row, column=2, value=f"Bab {ch.nomor_bab}: {ch.judul_bab}").alignment = left_align
                ws.cell(row=current_row, column=3, value=f"[{tp.code}] {tp.deskripsi}").alignment = left_align
                ws.cell(row=current_row, column=4, value=tp.alokasi_jp).alignment = center_align

                # Mark non-effective agenda columns (MPLS, STS, SAS, LSMT, RMD, RPR, LHR)
                for nem in non_effective_meta:
                    ag_cell = ws.cell(row=current_row, column=nem["col"], value=nem["code"])
                    ag_cell.alignment = center_align
                    ag_cell.font = agenda_font
                    ag_cell.fill = agenda_fill

                # Distribute JP across effective weeks
                jp_per_week = subject.alokasi_jp_mingguan or 2
                needed_weeks = max(1, round(tp.alokasi_jp / jp_per_week))

                for _ in range(needed_weeks):
                    if eff_ptr < len(effective_cols):
                        target_col = effective_cols[eff_ptr]
                        week_cell = ws.cell(row=current_row, column=target_col, value=jp_per_week)
                        week_cell.alignment = center_align
                        week_cell.font = data_font
                        eff_ptr += 1

                for c in range(1, col_idx):
                    cell = ws.cell(row=current_row, column=c)
                    cell.border = cell_border
                    if not cell.font or cell.font == Font():
                        cell.font = data_font

                current_row += 1
                row_num += 1

        # 4. Total Row with Active Excel Formula =SUM(...)
        ws.cell(row=current_row, column=1, value="").alignment = center_align
        ws.merge_cells(f"B{current_row}:C{current_row}")
        ws.cell(row=current_row, column=2, value="TOTAL ALOKASI JAM PELAJARAN (JP)").alignment = Alignment(horizontal="right", vertical="center")
        ws.cell(row=current_row, column=2).font = bold_font

        total_cell = ws.cell(row=current_row, column=4, value=f"=SUM(D7:D{current_row - 1})")
        total_cell.alignment = center_align
        total_cell.font = bold_font

        for c in range(1, col_idx):
            cell = ws.cell(row=current_row, column=c)
            cell.border = cell_border
            cell.fill = total_fill

        ws.column_dimensions["A"].width = 5
        ws.column_dimensions["B"].width = 28
        ws.column_dimensions["C"].width = 45
        ws.column_dimensions["D"].width = 10

        # 5. Signatures at bottom
        sig_row = current_row + 3
        pengesahan = teacher.get_lembar_pengesahan()

        ws.cell(row=sig_row, column=col_idx - 6, value=pengesahan["titimangsa"]).font = sub_font
        ws.cell(row=sig_row + 1, column=2, value="Mengetahui,\nKepala Sekolah").font = sub_font
        ws.cell(row=sig_row + 1, column=col_idx - 6, value="Guru Mata Pelajaran,").font = sub_font

        ws.cell(row=sig_row + 4, column=2, value=pengesahan["nama_kepala_sekolah"]).font = bold_font
        ws.cell(row=sig_row + 5, column=2, value=pengesahan["nip_kepala_sekolah"]).font = sub_font

        ws.cell(row=sig_row + 4, column=col_idx - 6, value=pengesahan["nama_guru"]).font = bold_font
        ws.cell(row=sig_row + 5, column=col_idx - 6, value=pengesahan["nip_guru"]).font = sub_font

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def _generate_structured_curriculum_xlsx(
        self,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
        raw_template: Optional[dict],
    ) -> bytes:
        """Generates Excel (.xlsx) workbook with active =SUM formulas for CP-TP, ATP, Prota, or Modul Ajar."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = request.service_id.value[:20]

        title_font = Font(name="Arial", size=12, bold=True, color="0F172A")
        header_font = Font(name="Arial", size=10, bold=True, color="0F172A")
        data_font = Font(name="Arial", size=9.5, color="1E293B")
        header_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
        thin_side = Side(style="thin", color="94A3B8")
        border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        kop = teacher.get_formatted_kop()
        ws.cell(row=1, column=1, value=kop["nama_sekolah"]).font = title_font
        ws.cell(row=2, column=1, value=f"DOKUMEN {request.service_id.value.upper()} — {subject.nama_mapel.upper()} KELAS {subject.kelas}").font = title_font

        headers = ["No", "Semester", "Bab / Lingkup Materi", "Kode & Deskripsi Tujuan Pembelajaran (TP)", "Dimensi Profil Lulusan", "Alokasi JP"]
        for idx, h in enumerate(headers, start=1):
            c = ws.cell(row=4, column=idx, value=h)
            c.font = header_font
            c.fill = header_fill
            c.border = border

        row_idx = 5
        no = 1
        target_chapters = [chapter] if (request.service_id == ServiceIdEnum.MODUL_AJAR and chapter) else subject.bab_list
        ov = request.custom_overrides
        for ch in target_chapters:
            is_current = (request.chapter_id and ch.id == request.chapter_id) or (chapter and ch.id == chapter.id) or (len(target_chapters) == 1)
            tps = _resolve_effective_tps(ch, request) if is_current else ch.tujuan_pembelajaran
            for tp in tps:
                vals = [
                    no,
                    f"Semester {ch.semester}",
                    f"Bab {ch.nomor_bab}: {ch.judul_bab}",
                    f"[{tp.code}] {tp.deskripsi}",
                    ", ".join(ch.dimensi_profil_lulusan),
                    tp.alokasi_jp,
                ]
                for c_i, v in enumerate(vals, start=1):
                    cell = ws.cell(row=row_idx, column=c_i, value=v)
                    cell.font = data_font
                    cell.border = border
                row_idx += 1
                no += 1

        # Active Formula Total Row
        ws.cell(row=row_idx, column=5, value="TOTAL ALOKASI JP").font = header_font
        tot_cell = ws.cell(row=row_idx, column=6, value=f"=SUM(F5:F{row_idx - 1})")
        tot_cell.font = header_font
        tot_cell.border = border

        ws.column_dimensions["A"].width = 6
        ws.column_dimensions["B"].width = 14
        ws.column_dimensions["C"].width = 30
        ws.column_dimensions["D"].width = 50
        ws.column_dimensions["E"].width = 28
        ws.column_dimensions["F"].width = 12

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def _generate_kktp_xlsx(
        self,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
    ) -> bytes:
        """Generates Service 07 (KKTP) Excel workbook with active =IF, =AVERAGE, and =COUNTIF formulas."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"KKTP Smt {request.semester}"

        title_font = Font(name="Arial", size=12, bold=True)
        header_font = Font(name="Arial", size=10, bold=True)
        data_font = Font(name="Arial", size=10)
        header_fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        thin_side = Side(style="thin", color="334155")
        border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        ws["A1"] = f"KRITERIA KETERCAPAIAN TUJUAN PEMBELAJARAN (KKTP) — {subject.nama_mapel.upper()}"
        ws["A1"].font = title_font
        ws["A2"] = f"{teacher.nama_sekolah} | Kelas {subject.kelas} (Fase {subject.fase}) | Penyusun: {teacher.nama_guru}"
        ws["A2"].font = data_font

        headers = ["No", "Kode TP", "Rumusan Tujuan Pembelajaran", "Skor Capaian (0-100)", "Predikat Otomatis", "Status Ketuntasan (KKTP >= 75)"]
        for idx, h in enumerate(headers, start=1):
            c = ws.cell(row=4, column=idx, value=h)
            c.font = header_font
            c.fill = header_fill
            c.border = border

        target_chapters = [chapter] if chapter else [c for c in subject.bab_list if c.semester == request.semester]
        if not target_chapters:
            target_chapters = subject.bab_list[:2]

        row_idx = 5
        no = 1
        for ch in target_chapters:
            for tp in _resolve_effective_tps(ch, request):
                ws.cell(row=row_idx, column=1, value=no).border = border
                ws.cell(row=row_idx, column=2, value=tp.code).border = border
                ws.cell(row=row_idx, column=3, value=tp.deskripsi).border = border
                c_score = ws.cell(row=row_idx, column=4, value=80)
                c_score.border = border
                c_pred = ws.cell(
                    row=row_idx,
                    column=5,
                    value=f'=IF(D{row_idx}>=88,"Sangat Baik (A)",IF(D{row_idx}>=75,"Baik (B)",IF(D{row_idx}>=61,"Cukup (C)","Perlu Bimbingan (D)")))',
                )
                c_pred.border = border
                c_status = ws.cell(
                    row=row_idx,
                    column=6,
                    value=f'=IF(D{row_idx}>=75,"Tuntas (Tidak Remedial)","Belum Tuntas (Remedial)")',
                )
                c_status.border = border
                row_idx += 1
                no += 1

        last_data_row = max(5, row_idx - 1)
        ws.cell(row=row_idx, column=3, value="RATA-RATA SKOR & JUMLAH TUNTAS").font = header_font
        avg_cell = ws.cell(row=row_idx, column=4, value=f"=AVERAGE(D5:D{last_data_row})")
        avg_cell.font = header_font
        avg_cell.border = border
        cnt_cell = ws.cell(row=row_idx, column=6, value=f'=COUNTIF(F5:F{last_data_row},"Tuntas (Tidak Remedial)")')
        cnt_cell.font = header_font
        cnt_cell.border = border

        ws.column_dimensions["A"].width = 6
        ws.column_dimensions["B"].width = 14
        ws.column_dimensions["C"].width = 52
        ws.column_dimensions["D"].width = 20
        ws.column_dimensions["E"].width = 24
        ws.column_dimensions["F"].width = 28

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
