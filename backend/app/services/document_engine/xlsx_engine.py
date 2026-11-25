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
from app.services.document_engine.jurnal_blueprint import JurnalBlueprintEngine
from app.services.document_engine.rapor_blueprint import RaporBlueprintEngine


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
            if request.service_id == ServiceIdEnum.PRESENSI:
                return self._generate_presensi_xlsx(request, subject, teacher)
            if request.service_id == ServiceIdEnum.JURNAL_MENGAJAR:
                return self._generate_jurnal_xlsx(request, subject, teacher)
            if request.service_id == ServiceIdEnum.DAFTAR_NILAI:
                return self._generate_daftar_nilai_xlsx(request, subject, chapter, teacher)
            if request.service_id == ServiceIdEnum.DESKRIPSI_RAPOR:
                return self._generate_deskripsi_rapor_xlsx(request, subject, teacher)
            if request.service_id == ServiceIdEnum.REKAP_RAPOR:
                return self._generate_rekap_rapor_xlsx(request, subject, teacher)
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
            if not ch_tps:
                from app.models.curriculum import LearningObjective
                ch_tps = [
                    LearningObjective(
                        code=f"TP.{subject.kelas}.{ch.nomor_bab}.1",
                        deskripsi=f"Mempelajari dan mengaplikasikan materi {ch.judul_bab}",
                        alokasi_jp=ch.alokasi_jp,
                        urutan_atp=1,
                    )
                ]
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

    def _generate_presensi_xlsx(
        self,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        teacher: TeacherProfile,
    ) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Presensi Siswa"

        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.sheet_properties.pageSetUpPr.fitToPage = True

        title_font = Font(name="Calibri", size=13, bold=True, color="0F172A")
        sub_font = Font(name="Calibri", size=10, italic=True, color="475569")
        meta_label_font = Font(name="Calibri", size=10, bold=True, color="1E293B")
        meta_val_font = Font(name="Calibri", size=10, color="334155")
        th_font = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
        td_font = Font(name="Calibri", size=9, color="0F172A")
        td_bold = Font(name="Calibri", size=9, bold=True, color="0F172A")

        th_fill = PatternFill(start_color="0D9488", end_color="0D9488", fill_type="solid")
        th_rekap_fill = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid")
        summary_fill = PatternFill(start_color="F0FDFA", end_color="F0FDFA", fill_type="solid")

        thin_side = Side(border_style="thin", color="CBD5E1")
        cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_align = Alignment(horizontal="left", vertical="center")

        # 1. Title Block
        tahun_ajaran = (request.teacher_profile.tahun_ajaran if request.teacher_profile and hasattr(request.teacher_profile, "tahun_ajaran") else None) or "2026/2027"
        ws["A1"] = "PRESENSI DAN KEHADIRAN PESERTA DIDIK"
        ws["A1"].font = title_font
        ws["A2"] = f"SEKOLAH: {teacher.nama_sekolah.upper() if teacher.nama_sekolah else 'GURUDOK SCHOOL'}"
        ws["A2"].font = title_font
        ws["A3"] = f"TAHUN AJARAN {tahun_ajaran} — SEMESTER {request.semester or 1}"
        ws["A3"].font = sub_font

        # 2. Metadata Block
        ov = request.custom_overrides
        rombel_name = (ov.nama_rombel if ov and ov.nama_rombel else None) or f"{subject.jenjang} Kelas {request.kelas}"
        bulan_name = (ov.bulan_presensi if ov and ov.bulan_presensi else None) or "Bulan Berjalan"

        ws["A5"] = "Mata Pelajaran"
        ws["A5"].font = meta_label_font
        ws["B5"] = f": {subject.nama_mapel}"
        ws["B5"].font = meta_val_font

        ws["A6"] = "Kelas / Rombel"
        ws["A6"].font = meta_label_font
        ws["B6"] = f": {rombel_name}"
        ws["B6"].font = meta_val_font

        ws["N5"] = "Guru Pengampu"
        ws["N5"].font = meta_label_font
        ws["O5"] = f": {teacher.nama_guru or '-'}"
        ws["O5"].font = meta_val_font

        ws["N6"] = "Bulan Presensi"
        ws["N6"].font = meta_label_font
        ws["O6"] = f": {bulan_name}"
        ws["O6"].font = meta_val_font

        # 3. Table Headers (Row 8 & 9)
        headers_merged = [
            ("A8", "A9", "No"),
            ("B8", "B9", "NISN"),
            ("C8", "C9", "Nama Lengkap Siswa"),
            ("D8", "D9", "L/P"),
            ("E8", "AI8", f"Tanggal Pelaksanaan Presensi ({bulan_name})"),
            ("AJ8", "AN8", "Rekapitulasi Kehadiran"),
        ]
        for top_left, bottom_right, text in headers_merged:
            ws.merge_cells(f"{top_left}:{bottom_right}")
            cell = ws[top_left]
            cell.value = text
            cell.font = th_font
            cell.fill = th_rekap_fill if "Rekap" in text else th_fill
            cell.alignment = center_align

        # Sub-headers for Dates 1-31 (Row 9, Cols E s.d. AI -> col 5 s.d. 35)
        for day in range(1, 32):
            col_letter = get_column_letter(4 + day)
            cell = ws[f"{col_letter}9"]
            cell.value = day
            cell.font = th_font
            cell.fill = th_fill
            cell.alignment = center_align

        # Sub-headers for Rekap (Row 9, Cols AJ s.d. AN -> col 36 s.d. 40)
        rekap_labels = [("AJ9", "H"), ("AK9", "S"), ("AL9", "I"), ("AM9", "A"), ("AN9", "%")]
        for pos, lbl in rekap_labels:
            cell = ws[pos]
            cell.value = lbl
            cell.font = th_font
            cell.fill = th_rekap_fill
            cell.alignment = center_align

        # Apply borders to header rows (8 & 9)
        for r in (8, 9):
            for c in range(1, 41):
                col_letter = get_column_letter(c)
                ws[f"{col_letter}{r}"].border = cell_border

        # 4. Student Data Rows (Starting Row 10)
        students_input = (ov.students if ov and ov.students else None) or []
        if not students_input:
            students_input = [
                type("obj", (), {"nomor_absen": 1, "nisn": "-", "nama_lengkap": "Ahmad Fauzi", "jenis_kelamin": "L"}),
                type("obj", (), {"nomor_absen": 2, "nisn": "-", "nama_lengkap": "Budi Santoso", "jenis_kelamin": "L"}),
                type("obj", (), {"nomor_absen": 3, "nisn": "-", "nama_lengkap": "Citra Lestari", "jenis_kelamin": "P"}),
                type("obj", (), {"nomor_absen": 4, "nisn": "-", "nama_lengkap": "Dewi Sartika", "jenis_kelamin": "P"}),
                type("obj", (), {"nomor_absen": 5, "nisn": "-", "nama_lengkap": "Eko Prasetyo", "jenis_kelamin": "L"}),
            ]

        curr_row = 10
        for idx, st in enumerate(students_input, start=1):
            s_name = getattr(st, "nama_lengkap", "") or ""
            while s_name and s_name[0] in ("=", "+", "-", "@"):
                s_name = s_name[1:].strip()

            s_nisn = getattr(st, "nisn", "-") or "-"
            s_gender = getattr(st, "jenis_kelamin", "L") or "L"
            s_no = getattr(st, "nomor_absen", idx) or idx

            ws.cell(row=curr_row, column=1, value=s_no).alignment = center_align
            ws.cell(row=curr_row, column=2, value=s_nisn).alignment = center_align
            ws.cell(row=curr_row, column=3, value=s_name).alignment = left_align
            ws.cell(row=curr_row, column=4, value=s_gender).alignment = center_align

            # Dates 1-31 (cols 5 to 35)
            for c in range(5, 36):
                cell = ws.cell(row=curr_row, column=c, value="")
                cell.alignment = center_align

            # Active Formulas for Attendance Summary
            ws.cell(row=curr_row, column=36, value=f'=COUNTIF(E{curr_row}:AI{curr_row}, "H")').alignment = center_align
            ws.cell(row=curr_row, column=37, value=f'=COUNTIF(E{curr_row}:AI{curr_row}, "S")').alignment = center_align
            ws.cell(row=curr_row, column=38, value=f'=COUNTIF(E{curr_row}:AI{curr_row}, "I")').alignment = center_align
            ws.cell(row=curr_row, column=39, value=f'=COUNTIF(E{curr_row}:AI{curr_row}, "A")').alignment = center_align
            ws.cell(
                row=curr_row,
                column=40,
                value=f'=IF((AJ{curr_row}+AK{curr_row}+AL{curr_row}+AM{curr_row})>0, ROUND((AJ{curr_row}/(AJ{curr_row}+AK{curr_row}+AL{curr_row}+AM{curr_row}))*100, 1), 100)'
            ).alignment = center_align

            for c in range(1, 41):
                cell = ws.cell(row=curr_row, column=c)
                cell.font = td_font
                cell.border = cell_border

            curr_row += 1

        last_data_row = curr_row - 1

        # 5. Class Summary Row
        ws.merge_cells(f"A{curr_row}:D{curr_row}")
        sum_label = ws[f"A{curr_row}"]
        sum_label.value = "TOTAL REKAPITULASI KELAS"
        sum_label.font = td_bold
        sum_label.alignment = Alignment(horizontal="right", vertical="center")

        ws.cell(row=curr_row, column=36, value=f"=SUM(AJ10:AJ{last_data_row})").alignment = center_align
        ws.cell(row=curr_row, column=37, value=f"=SUM(AK10:AK{last_data_row})").alignment = center_align
        ws.cell(row=curr_row, column=38, value=f"=SUM(AL10:AL{last_data_row})").alignment = center_align
        ws.cell(row=curr_row, column=39, value=f"=SUM(AM10:AM{last_data_row})").alignment = center_align
        ws.cell(row=curr_row, column=40, value=f"=ROUND(AVERAGE(AN10:AN{last_data_row}), 1)").alignment = center_align

        for c in range(1, 41):
            cell = ws.cell(row=curr_row, column=c)
            cell.font = td_bold
            cell.fill = summary_fill
            cell.border = cell_border

        # Column Widths
        ws.column_dimensions["A"].width = 5
        ws.column_dimensions["B"].width = 15
        ws.column_dimensions["C"].width = 28
        ws.column_dimensions["D"].width = 6
        for c in range(5, 36):
            ws.column_dimensions[get_column_letter(c)].width = 3.6
        for c in range(36, 40):
            ws.column_dimensions[get_column_letter(c)].width = 5.5
        ws.column_dimensions["AN"].width = 8

        # 6. Signature Block
        sig_row = curr_row + 3
        city = teacher.kabupaten_kota or "Surabaya"
        ws.cell(row=sig_row, column=3, value="Mengetahui,")
        ws.cell(row=sig_row + 1, column=3, value="Kepala Sekolah")
        ws.cell(row=sig_row + 5, column=3, value=f"({teacher.nama_kepala_sekolah or '................................'})").font = td_bold
        ws.cell(row=sig_row + 6, column=3, value=f"NIP. {teacher.nip_kepala_sekolah or '-'}")

        ws.cell(row=sig_row, column=32, value=f"{city}, ....................")
        ws.cell(row=sig_row + 1, column=32, value="Guru Mata Pelajaran")
        ws.cell(row=sig_row + 5, column=32, value=f"({teacher.nama_guru or '................................'})").font = td_bold
        ws.cell(row=sig_row + 6, column=32, value=f"NIP. {teacher.nip_guru or '-'}")

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def _generate_daftar_nilai_xlsx(
        self,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
    ) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Daftar Nilai"

        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.sheet_properties.pageSetUpPr.fitToPage = True

        title_font = Font(name="Calibri", size=13, bold=True, color="0F172A")
        sub_font = Font(name="Calibri", size=10, italic=True, color="475569")
        meta_label_font = Font(name="Calibri", size=10, bold=True, color="1E293B")
        meta_val_font = Font(name="Calibri", size=10, color="334155")
        th_font = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
        td_font = Font(name="Calibri", size=9, color="0F172A")
        td_bold = Font(name="Calibri", size=9, bold=True, color="0F172A")

        th_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        th_sumatif_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
        th_final_fill = PatternFill(start_color="0D9488", end_color="0D9488", fill_type="solid")
        summary_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

        thin_side = Side(border_style="thin", color="CBD5E1")
        cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_align = Alignment(horizontal="left", vertical="center")

        ov = request.custom_overrides
        rombel_name = (ov.nama_rombel if ov and ov.nama_rombel else None) or f"{subject.jenjang} Kelas {request.kelas}"
        kktp_val = (ov.kktp_nilai if ov and ov.kktp_nilai else None) or 75

        # 1. Title Block
        tahun_ajaran = (request.teacher_profile.tahun_ajaran if request.teacher_profile and hasattr(request.teacher_profile, "tahun_ajaran") else None) or "2026/2027"
        ws["A1"] = "BUKU DAFTAR NILAI PESERTA DIDIK"
        ws["A1"].font = title_font
        ws["A2"] = f"SEKOLAH: {teacher.nama_sekolah.upper() if teacher.nama_sekolah else 'GURUDOK SCHOOL'}"
        ws["A2"].font = title_font
        ws["A3"] = f"KURIKULUM MERDEKA — TAHUN AJARAN {tahun_ajaran} (SEMESTER {request.semester or 1})"
        ws["A3"].font = sub_font

        # 2. Metadata Block
        ws["A5"] = "Mata Pelajaran"
        ws["A5"].font = meta_label_font
        ws["B5"] = f": {subject.nama_mapel}"
        ws["B5"].font = meta_val_font

        ws["A6"] = "Kelas / Rombel"
        ws["A6"].font = meta_label_font
        ws["B6"] = f": {rombel_name}"
        ws["B6"].font = meta_val_font

        ws["H5"] = "KKTP Sekolah"
        ws["H5"].font = meta_label_font
        ws["I5"] = f": {kktp_val}"
        ws["I5"].font = meta_val_font

        ws["H6"] = "Guru Pengampu"
        ws["H6"].font = meta_label_font
        ws["I6"] = f": {teacher.nama_guru or '-'}"
        ws["I6"].font = meta_val_font

        # 3. Table Headers (Row 8 & 9)
        headers_merged = [
            ("A8", "A9", "No", th_fill),
            ("B8", "B9", "NISN", th_fill),
            ("C8", "C9", "Nama Lengkap Siswa", th_fill),
            ("D8", "D9", "L/P", th_fill),
            ("E8", "H8", "Asesmen Formatif (Tujuan Pembelajaran)", th_fill),
            ("I8", "I9", "Rata-rata\nFormatif", th_fill),
            ("J8", "K8", "Asesmen Sumatif", th_sumatif_fill),
            ("L8", "L9", "Nilai Akhir\n(NA)", th_final_fill),
            ("M8", "M9", f"Ketercapaian\n(KKTP {kktp_val})", th_final_fill),
        ]

        for top_left, bottom_right, text, fill_color in headers_merged:
            ws.merge_cells(f"{top_left}:{bottom_right}")
            cell = ws[top_left]
            cell.value = text
            cell.font = th_font
            cell.fill = fill_color
            cell.alignment = center_align

        # Sub-headers row 9
        sub_headers = [
            ("E9", "TP 1", th_fill),
            ("F9", "TP 2", th_fill),
            ("G9", "TP 3", th_fill),
            ("H9", "TP 4", th_fill),
            ("J9", "STS", th_sumatif_fill),
            ("K9", "SAS", th_sumatif_fill),
        ]
        for pos, lbl, fill_c in sub_headers:
            cell = ws[pos]
            cell.value = lbl
            cell.font = th_font
            cell.fill = fill_c
            cell.alignment = center_align

        for r in (8, 9):
            for c in range(1, 14):
                col_letter = get_column_letter(c)
                ws[f"{col_letter}{r}"].border = cell_border

        # 4. Student Data Rows (Starting Row 10)
        students_input = (ov.students if ov and ov.students else None) or []
        if not students_input:
            students_input = [
                type("obj", (), {"nomor_absen": 1, "nisn": "-", "nama_lengkap": "Ahmad Fauzi", "jenis_kelamin": "L"}),
                type("obj", (), {"nomor_absen": 2, "nisn": "-", "nama_lengkap": "Budi Santoso", "jenis_kelamin": "L"}),
                type("obj", (), {"nomor_absen": 3, "nisn": "-", "nama_lengkap": "Citra Lestari", "jenis_kelamin": "P"}),
                type("obj", (), {"nomor_absen": 4, "nisn": "-", "nama_lengkap": "Dewi Sartika", "jenis_kelamin": "P"}),
                type("obj", (), {"nomor_absen": 5, "nisn": "-", "nama_lengkap": "Eko Prasetyo", "jenis_kelamin": "L"}),
            ]

        curr_row = 10
        for idx, st in enumerate(students_input, start=1):
            s_name = getattr(st, "nama_lengkap", "") or ""
            while s_name and s_name[0] in ("=", "+", "-", "@"):
                s_name = s_name[1:].strip()

            s_nisn = getattr(st, "nisn", "-") or "-"
            s_gender = getattr(st, "jenis_kelamin", "L") or "L"
            s_no = getattr(st, "nomor_absen", idx) or idx

            ws.cell(row=curr_row, column=1, value=s_no).alignment = center_align
            ws.cell(row=curr_row, column=2, value=s_nisn).alignment = center_align
            ws.cell(row=curr_row, column=3, value=s_name).alignment = left_align
            ws.cell(row=curr_row, column=4, value=s_gender).alignment = center_align

            # Sample Initial Formatif Scores
            ws.cell(row=curr_row, column=5, value=78).alignment = center_align
            ws.cell(row=curr_row, column=6, value=82).alignment = center_align
            ws.cell(row=curr_row, column=7, value=80).alignment = center_align
            ws.cell(row=curr_row, column=8, value=85).alignment = center_align

            # Col 9 (I): Rata-rata Formatif =ROUND(AVERAGE(E{curr_row}:H{curr_row}), 1)
            ws.cell(row=curr_row, column=9, value=f"=ROUND(AVERAGE(E{curr_row}:H{curr_row}), 1)").alignment = center_align

            # Sumatif: STS (Col 10/J) and SAS (Col 11/K)
            ws.cell(row=curr_row, column=10, value=80).alignment = center_align
            ws.cell(row=curr_row, column=11, value=82).alignment = center_align

            # Col 12 (L): Nilai Akhir (NA) =ROUND((I{curr_row}*0.4)+(J{curr_row}*0.3)+(K{curr_row}*0.3), 0)
            ws.cell(
                row=curr_row,
                column=12,
                value=f"=ROUND((I{curr_row}*0.4)+(J{curr_row}*0.3)+(K{curr_row}*0.3), 0)"
            ).alignment = center_align

            # Col 13 (M): Status Ketercapaian =IF(L{curr_row}>={kktp_val}, "TUNTAS", "BELUM TUNTAS")
            ws.cell(
                row=curr_row,
                column=13,
                value=f'=IF(L{curr_row}>={kktp_val}, "TUNTAS", "BELUM TUNTAS")'
            ).alignment = center_align

            for c in range(1, 14):
                cell = ws.cell(row=curr_row, column=c)
                cell.font = td_font
                cell.border = cell_border

            curr_row += 1

        last_data_row = curr_row - 1

        # 5. Class Statistics Summary Rows (at bottom)
        stat_rows = [
            ("RATA-RATA KELAS", "AVERAGE"),
            ("NILAI TERTINGGI", "MAX"),
            ("NILAI TERENDAH", "MIN"),
        ]

        for label, fn in stat_rows:
            ws.merge_cells(f"A{curr_row}:D{curr_row}")
            ws[f"A{curr_row}"].value = label
            ws[f"A{curr_row}"].font = td_bold
            ws[f"A{curr_row}"].alignment = Alignment(horizontal="right", vertical="center")

            for c in range(5, 13):
                col_letter = get_column_letter(c)
                if fn == "AVERAGE":
                    ws.cell(row=curr_row, column=c, value=f"=ROUND(AVERAGE({col_letter}10:{col_letter}{last_data_row}), 1)").alignment = center_align
                else:
                    ws.cell(row=curr_row, column=c, value=f"={fn}({col_letter}10:{col_letter}{last_data_row})").alignment = center_align

            ws.cell(row=curr_row, column=13, value="").alignment = center_align

            for c in range(1, 14):
                cell = ws.cell(row=curr_row, column=c)
                cell.font = td_bold
                cell.fill = summary_fill
                cell.border = cell_border
            curr_row += 1

        # Summary Row: Jumlah Siswa Tuntas
        ws.merge_cells(f"A{curr_row}:L{curr_row}")
        ws[f"A{curr_row}"].value = f"JUMLAH SISWA TUNTAS (KKTP ≥ {kktp_val})"
        ws[f"A{curr_row}"].font = td_bold
        ws[f"A{curr_row}"].alignment = Alignment(horizontal="right", vertical="center")
        ws.cell(row=curr_row, column=13, value=f'=COUNTIF(M10:M{last_data_row}, "TUNTAS")').alignment = center_align

        for c in range(1, 14):
            cell = ws.cell(row=curr_row, column=c)
            cell.font = td_bold
            cell.fill = summary_fill
            cell.border = cell_border
        curr_row += 1

        # Summary Row: Persentase Ketuntasan
        ws.merge_cells(f"A{curr_row}:L{curr_row}")
        ws[f"A{curr_row}"].value = "PERSENTASE KETUNTASAN KLASIKAL"
        ws[f"A{curr_row}"].font = td_bold
        ws[f"A{curr_row}"].alignment = Alignment(horizontal="right", vertical="center")
        ws.cell(
            row=curr_row,
            column=13,
            value=f'=ROUND((COUNTIF(M10:M{last_data_row}, "TUNTAS")/COUNTA(C10:C{last_data_row}))*100, 1)'
        ).alignment = center_align

        for c in range(1, 14):
            cell = ws.cell(row=curr_row, column=c)
            cell.font = td_bold
            cell.fill = summary_fill
            cell.border = cell_border

        # 6. Column Widths
        ws.column_dimensions["A"].width = 5
        ws.column_dimensions["B"].width = 15
        ws.column_dimensions["C"].width = 28
        ws.column_dimensions["D"].width = 6
        for c in range(5, 9):
            ws.column_dimensions[get_column_letter(c)].width = 9
        ws.column_dimensions["I"].width = 14
        ws.column_dimensions["J"].width = 10
        ws.column_dimensions["K"].width = 10
        ws.column_dimensions["L"].width = 13
        ws.column_dimensions["M"].width = 18

        # 7. Signature Block
        sig_row = curr_row + 3
        city = teacher.kabupaten_kota or "Surabaya"
        ws.cell(row=sig_row, column=3, value="Mengetahui,")
        ws.cell(row=sig_row + 1, column=3, value="Kepala Sekolah")
        ws.cell(row=sig_row + 5, column=3, value=f"({teacher.nama_kepala_sekolah or '................................'})").font = td_bold
        ws.cell(row=sig_row + 6, column=3, value=f"NIP. {teacher.nip_kepala_sekolah or '-'}")

        ws.cell(row=sig_row, column=10, value=f"{city}, ....................")
        ws.cell(row=sig_row + 1, column=10, value="Guru Mata Pelajaran")
        ws.cell(row=sig_row + 5, column=10, value=f"({teacher.nama_guru or '................................'})").font = td_bold
        ws.cell(row=sig_row + 6, column=10, value=f"NIP. {teacher.nip_guru or '-'}")

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def _generate_jurnal_xlsx(
        self,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        teacher: TeacherProfile,
    ) -> bytes:
        bp = JurnalBlueprintEngine.build_blueprint(request, subject)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Jurnal Mengajar"

        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.sheet_properties.pageSetUpPr.fitToPage = True

        title_font = Font(name="Arial", size=13, bold=True, color="0F172A")
        sub_font = Font(name="Arial", size=10, bold=True, color="334155")
        th_font = Font(name="Arial", size=9.5, bold=True, color="0F172A")
        td_font = Font(name="Arial", size=9, color="1E293B")
        td_bold = Font(name="Arial", size=9, bold=True, color="0F172A")

        header_fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        summary_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        thin_side = Side(style="thin", color="475569")
        cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_align = Alignment(horizontal="left", vertical="top", wrap_text=True)

        kop = teacher.get_formatted_kop()
        ws.cell(row=1, column=1, value=f"JURNAL MENGAJAR HARIAN GURU — {subject.nama_mapel.upper()}").font = title_font
        ws.cell(row=2, column=1, value=f"Satuan Pendidikan: {kop['nama_sekolah']} | Rombel: {bp['rombel']} | Semester {request.semester}").font = sub_font
        ws.cell(row=3, column=1, value=f"Jadwal Rutin: {bp['hari_label']} (Jam {bp['jam_mengajar']}) | Mulai Semester: {bp['tanggal_mulai']}").font = sub_font

        headers = [
            "No",
            "Hari / Tanggal",
            "Jam Ke- / Pertemuan",
            "Tujuan Pembelajaran (TP)",
            "Materi Pembelajaran",
            "Ringkasan Kegiatan",
            "Kehadiran Siswa",
            "Hambatan & Refleksi",
            "Paraf",
        ]
        header_row = 5
        for c_idx, h_text in enumerate(headers, start=1):
            c = ws.cell(row=header_row, column=c_idx, value=h_text)
            c.font = th_font
            c.fill = header_fill
            c.alignment = center_align
            c.border = cell_border
        ws.row_dimensions[header_row].height = 28

        curr_row = header_row + 1
        start_data_row = curr_row
        for item in bp["rows"]:
            vals = [
                int(item["no"]),
                item["hari_tanggal"],
                item["jam_pertemuan"],
                item["tp"],
                item["materi"],
                item["kegiatan"],
                item["kehadiran"],
                item["refleksi"],
                item["paraf"],
            ]
            for c_idx, val in enumerate(vals, start=1):
                cell = ws.cell(row=curr_row, column=c_idx, value=val)
                cell.font = td_bold if c_idx == 1 else td_font
                cell.alignment = center_align if c_idx in (1, 3, 9) else left_align
                cell.border = cell_border
            ws.row_dimensions[curr_row].height = 36
            curr_row += 1

        end_data_row = curr_row - 1
        ws.cell(row=curr_row, column=1, value="-").alignment = center_align
        ws.cell(row=curr_row, column=2, value="TOTAL PERTEMUAN TERJADWAL").alignment = left_align
        ws.cell(row=curr_row, column=3, value=f"=COUNTA(B{start_data_row}:B{end_data_row})").alignment = center_align
        for c_idx in range(1, 10):
            c = ws.cell(row=curr_row, column=c_idx)
            c.font = td_bold
            c.fill = summary_fill
            c.border = cell_border

        col_widths = [5, 22, 18, 34, 24, 30, 20, 26, 10]
        for idx_w, w in enumerate(col_widths, start=1):
            ws.column_dimensions[get_column_letter(idx_w)].width = w

        sig_row = curr_row + 2
        city = teacher.kabupaten_kota or "Surabaya"
        ws.cell(row=sig_row, column=2, value="Mengetahui,")
        ws.cell(row=sig_row + 1, column=2, value="Kepala Sekolah")
        ws.cell(row=sig_row + 5, column=2, value=f"({teacher.nama_kepala_sekolah or '................................'})").font = td_bold
        ws.cell(row=sig_row + 6, column=2, value=f"NIP. {teacher.nip_kepala_sekolah or '-'}")

        ws.cell(row=sig_row, column=7, value=f"{city}, ....................")
        ws.cell(row=sig_row + 1, column=7, value="Guru Mata Pelajaran")
        ws.cell(row=sig_row + 5, column=7, value=f"({teacher.nama_guru or '................................'})").font = td_bold
        ws.cell(row=sig_row + 6, column=7, value=f"NIP. {teacher.nip_guru or '-'}")

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def _generate_deskripsi_rapor_xlsx(
        self,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        teacher: TeacherProfile,
    ) -> bytes:
        bp = RaporBlueprintEngine.build_blueprint(request, subject)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Deskripsi e-Rapor"
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.sheet_properties.pageSetUpPr.fitToPage = True

        title_font = Font(name="Arial", size=13, bold=True, color="0F172A")
        sub_font = Font(name="Arial", size=10, bold=True, color="334155")
        th_font = Font(name="Arial", size=9.5, bold=True, color="0F172A")
        td_font = Font(name="Arial", size=9, color="1E293B")
        td_bold = Font(name="Arial", size=9, bold=True, color="0F172A")
        header_fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        summary_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        thin_side = Side(style="thin", color="475569")
        cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_align = Alignment(horizontal="left", vertical="top", wrap_text=True)

        kop = teacher.get_formatted_kop()
        ws.cell(row=1, column=1, value=f"DESKRIPSI CAPAIAN KOMPETENSI (e-RAPOR) — {subject.nama_mapel.upper()}").font = title_font
        ws.cell(row=2, column=1, value=f"Satuan Pendidikan: {kop['nama_sekolah']} | Rombel: {bp['rombel']} | Semester {request.semester}").font = sub_font
        ws.cell(row=3, column=1, value=f"KKTP Minimum: {bp['kktp']} | Format siap salin (copy-paste) ke aplikasi e-Rapor Kemendikdasmen").font = sub_font

        headers = [
            "No",
            "NISN",
            "Nama Peserta Didik",
            "Nilai Rapor",
            "Kompetensi Tertinggi (TP)",
            "Kompetensi Perlu Pendampingan (TP)",
            "Deskripsi Capaian Tertinggi (e-Rapor)",
            "Deskripsi Perlu Pendampingan (e-Rapor)",
        ]
        header_row = 5
        for c_idx, h_text in enumerate(headers, start=1):
            c = ws.cell(row=header_row, column=c_idx, value=h_text)
            c.font = th_font
            c.fill = header_fill
            c.alignment = center_align
            c.border = cell_border
        ws.row_dimensions[header_row].height = 28

        curr_row = header_row + 1
        start_data_row = curr_row
        for item in bp["rows"]:
            vals = [
                item["no"],
                item["nisn"],
                item["nama"],
                item["nilai_akhir"],
                f"[{item['tp_tertinggi_code']}] {item['tp_tertinggi_ringkasan']}",
                f"[{item['tp_terendah_code']}] {item['tp_terendah_ringkasan']}",
                f'="Menunjukkan penguasaan yang sangat baik dalam "&SUBSTITUTE(E{curr_row},"["&LEFT(E{curr_row},FIND("]",E{curr_row})-1)&"] ","")&"."',
                f'="Perlu bimbingan dan pendampingan lebih lanjut dalam "&SUBSTITUTE(F{curr_row},"["&LEFT(F{curr_row},FIND("]",F{curr_row})-1)&"] ","")&"."',
            ]
            for c_idx, val in enumerate(vals, start=1):
                cell = ws.cell(row=curr_row, column=c_idx, value=val)
                cell.font = td_bold if c_idx in (1, 4) else td_font
                cell.alignment = center_align if c_idx in (1, 2, 4) else left_align
                cell.border = cell_border
            ws.row_dimensions[curr_row].height = 42
            curr_row += 1

        end_data_row = curr_row - 1
        ws.cell(row=curr_row, column=3, value="RATA-RATA NILAI RAPOR").alignment = left_align
        ws.cell(row=curr_row, column=4, value=f"=ROUND(AVERAGE(D{start_data_row}:D{end_data_row}), 1)").alignment = center_align
        ws.cell(row=curr_row, column=5, value=f'=COUNTIF(D{start_data_row}:D{end_data_row}, ">={bp["kktp"]}")&" Siswa Tuntas"').alignment = center_align
        for c_idx in range(1, 9):
            c = ws.cell(row=curr_row, column=c_idx)
            c.font = td_bold
            c.fill = summary_fill
            c.border = cell_border

        col_widths = [5, 14, 24, 12, 30, 30, 42, 42]
        for idx_w, w in enumerate(col_widths, start=1):
            ws.column_dimensions[get_column_letter(idx_w)].width = w

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    def _generate_rekap_rapor_xlsx(
        self,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        teacher: TeacherProfile,
    ) -> bytes:
        bp = RaporBlueprintEngine.build_blueprint(request, subject)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Rekap Nilai Rapor"
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.sheet_properties.pageSetUpPr.fitToPage = True

        title_font = Font(name="Arial", size=13, bold=True, color="0F172A")
        sub_font = Font(name="Arial", size=10, bold=True, color="334155")
        th_font = Font(name="Arial", size=9.5, bold=True, color="0F172A")
        td_font = Font(name="Arial", size=9, color="1E293B")
        td_bold = Font(name="Arial", size=9, bold=True, color="0F172A")
        header_fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
        summary_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        thin_side = Side(style="thin", color="475569")
        cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)

        kop = teacher.get_formatted_kop()
        ws.cell(row=1, column=1, value=f"REKAP NILAI RAPOR FINAL & PERINGKAT KELAS — {subject.nama_mapel.upper()}").font = title_font
        ws.cell(row=2, column=1, value=f"Satuan Pendidikan: {kop['nama_sekolah']} | Rombel: {bp['rombel']} | Semester {request.semester}").font = sub_font
        ws.cell(row=3, column=1, value="KKTP Minimum").font = td_bold
        ws.cell(row=3, column=2, value=bp["kktp"]).font = td_bold
        ws.cell(row=3, column=4, value="Bobot Sumatif (%)").font = td_bold
        ws.cell(row=3, column=5, value=bp["bobot_sumatif"]).font = td_bold
        ws.cell(row=3, column=6, value="Bobot SAS (%)").font = td_bold
        ws.cell(row=3, column=7, value=bp["bobot_sas"]).font = td_bold

        headers = [
            "No",
            "NISN",
            "Nama Peserta Didik",
            "Rata Sumatif Materi",
            "Nilai SAS",
            "Nilai Akhir Rapor",
            "Peringkat",
            "Ketuntasan (KKTP)",
            "Predikat",
        ]
        header_row = 5
        for c_idx, h_text in enumerate(headers, start=1):
            c = ws.cell(row=header_row, column=c_idx, value=h_text)
            c.font = th_font
            c.fill = header_fill
            c.alignment = center_align
            c.border = cell_border
        ws.row_dimensions[header_row].height = 28

        start_data_row = header_row + 1
        end_data_row = start_data_row + len(bp["rows"]) - 1
        curr_row = start_data_row
        for item in bp["rows"]:
            vals = [
                item["no"],
                item["nisn"],
                item["nama"],
                item["sumatif"],
                item["sas"],
                f"=ROUND((D{curr_row}*$E$3/100)+(E{curr_row}*$G$3/100), 0)",
                f"=RANK(F{curr_row}, $F${start_data_row}:$F${end_data_row})",
                f'=IF(F{curr_row}>=$B$3, "TUNTAS", "BELUM TUNTAS")',
                f'=IF(F{curr_row}>=90, "A (Sangat Baik)", IF(F{curr_row}>=80, "B (Baik)", IF(F{curr_row}>=$B$3, "C (Cukup)", "D (Perlu Bimbingan)")))',
            ]
            for c_idx, val in enumerate(vals, start=1):
                cell = ws.cell(row=curr_row, column=c_idx, value=val)
                cell.font = td_bold if c_idx in (1, 6, 7) else td_font
                cell.alignment = left_align if c_idx == 3 else center_align
                cell.border = cell_border
            ws.row_dimensions[curr_row].height = 22
            curr_row += 1

        # Summary rows: AVERAGE, MAX, MIN
        stats = [
            ("RATA-RATA KELAS", f"=ROUND(AVERAGE(F{start_data_row}:F{end_data_row}), 1)"),
            ("NILAI TERTINGGI", f"=MAX(F{start_data_row}:F{end_data_row})"),
            ("NILAI TERENDAH", f"=MIN(F{start_data_row}:F{end_data_row})"),
        ]
        for label, formula in stats:
            ws.cell(row=curr_row, column=3, value=label).alignment = left_align
            ws.cell(row=curr_row, column=6, value=formula).alignment = center_align
            for c_idx in range(1, 10):
                c = ws.cell(row=curr_row, column=c_idx)
                c.font = td_bold
                c.fill = summary_fill
                c.border = cell_border
            curr_row += 1

        col_widths = [5, 14, 28, 16, 12, 16, 12, 18, 22]
        for idx_w, w in enumerate(col_widths, start=1):
            ws.column_dimensions[get_column_letter(idx_w)].width = w

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
