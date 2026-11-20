import io
import re
from typing import List, Dict, Optional, Tuple
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from app.core.exceptions import SecurityViolationError
from app.core.security import FileAttackGuard, InputSanitizer
from app.schemas.classroom import StudentParsedItem, ClassroomParseResponseData

MAX_EXCEL_SIZE = 2 * 1024 * 1024  # 2 MB

# Synonym keywords for header auto-detection (lowercase, normalized)
SYNONYMS_NAMA = {
    "nama", "nama siswa", "nama lengkap", "nama peserta didik", "nama murid",
    "student name", "peserta didik", "nama anak", "nama_siswa", "nama_lengkap"
}

SYNONYMS_NISN = {
    "nisn", "nis", "no induk", "nomor induk", "no. induk", "nipd", "nik", "id siswa", "no_induk"
}

SYNONYMS_GENDER = {
    "jk", "jenis kelamin", "l/p", "gender", "kelamin", "sex", "l / p", "jenis_kelamin"
}

SYNONYMS_NOMOR = {
    "no", "nomor", "no.", "no absen", "no urut", "absen", "no. urut", "no_absen", "no_urut"
}

# Footers / non-student indicators to stop parsing
STOP_KEYWORDS = {
    "mengetahui", "kepala sekolah", "wali kelas", "guru mata pelajaran", "nip.", "nip", "catatan:"
}


class ClassroomExcelParserService:
    """Stateless service to parse teacher Excel files, detect headers, map columns, and generate templates."""

    @classmethod
    def sanitize_cell_value(cls, value: any) -> str:
        """Sanitizes cell content, prevents Formula Injection (DDE) and XSS."""
        if value is None:
            return ""

        text = str(value).strip()
        if not text:
            return ""

        # Formula Injection Guard: strip leading formula triggers
        while text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
            text = text[1:].strip()

        # InputSanitizer for HTML / Script prevention
        return InputSanitizer.sanitize_text(text, max_length=200, allow_empty=True)

    @classmethod
    def normalize_gender(cls, value: any) -> str:
        """Normalizes various gender representations to strictly 'L' or 'P'."""
        cleaned = str(value).strip().lower() if value is not None else ""
        if not cleaned:
            return "L"

        if cleaned.startswith("l") or "laki" in cleaned or "pria" in cleaned or cleaned == "m":
            return "L"
        if cleaned.startswith("p") or "perempuan" in cleaned or "wanita" in cleaned or cleaned == "f":
            return "P"

        return "L"

    @classmethod
    def detect_header_row(cls, sheet: openpyxl.worksheet.worksheet.Worksheet, max_scan_rows: int = 20) -> Tuple[int, Dict[str, int]]:
        """
        Scans top rows to identify the actual table header row using synonym scoring.
        Returns (header_row_index_1_based, column_indices_0_based_dict).
        """
        best_row = 1
        best_score = -1
        best_mappings: Dict[str, int] = {}

        for row_idx, row in enumerate(sheet.iter_rows(max_row=max_scan_rows, values_only=True), start=1):
            if not row or all(v is None or str(v).strip() == "" for v in row):
                continue

            current_mappings: Dict[str, int] = {}
            score = 0

            for col_idx, cell_value in enumerate(row):
                if cell_value is None:
                    continue
                cell_text = str(cell_value).strip().lower().replace("\n", " ")

                # Match against synonyms
                if "nama" not in current_mappings and (cell_text in SYNONYMS_NAMA or any(syn in cell_text for syn in ("nama siswa", "nama lengkap", "peserta didik"))):
                    current_mappings["nama"] = col_idx
                    score += 5
                elif "nama" not in current_mappings and cell_text == "nama":
                    current_mappings["nama"] = col_idx
                    score += 5
                elif "nisn" not in current_mappings and (cell_text in SYNONYMS_NISN or any(syn in cell_text for syn in ("nisn", "no induk", "nomor induk"))):
                    current_mappings["nisn"] = col_idx
                    score += 3
                elif "gender" not in current_mappings and (cell_text in SYNONYMS_GENDER or cell_text in ("l/p", "jk")):
                    current_mappings["gender"] = col_idx
                    score += 3
                elif "nomor" not in current_mappings and (cell_text in SYNONYMS_NOMOR or cell_text in ("no", "no.")):
                    current_mappings["nomor"] = col_idx
                    score += 2

            # A valid header must at least recognize a name column
            if "nama" in current_mappings and score > best_score:
                best_score = score
                best_row = row_idx
                best_mappings = current_mappings

        if best_score < 5:
            # Fallback default: assume row 1 has standard order
            best_row = 1
            best_mappings = {"nomor": 0, "nisn": 1, "nama": 2, "gender": 3}

        return best_row, best_mappings

    @classmethod
    def parse_excel_file(cls, file_bytes: bytes, filename: str) -> ClassroomParseResponseData:
        """
        Stateless parsing of uploaded Excel file bytes.
        Verifies magic bytes, size limits, auto-detects headers, and extracts students.
        """
        # 1. File Size Verification
        if len(file_bytes) > MAX_EXCEL_SIZE:
            raise SecurityViolationError(f"Ukuran file melebihi batas maksimum 2 MB ({len(file_bytes)} bytes).")

        # 2. File Extension & Magic Byte Verification
        if not filename.lower().endswith(".xlsx"):
            raise SecurityViolationError("Hanya file format Excel (.xlsx) yang diperbolehkan.")

        if not FileAttackGuard.verify_docx_or_xlsx_signature(file_bytes):
            raise SecurityViolationError("File bukan format Excel valid / signature file korup.")

        # 3. Load Workbook
        try:
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=False)
            ws = wb.active
        except Exception as e:
            raise SecurityViolationError(f"Gagal memproses file Excel: {str(e)}")

        # 4. Detect Header
        header_row_idx, col_mappings = cls.detect_header_row(ws)

        name_col = col_mappings.get("nama")
        nisn_col = col_mappings.get("nisn")
        gender_col = col_mappings.get("gender")
        nomor_col = col_mappings.get("nomor")

        students: List[StudentParsedItem] = []
        warnings: List[str] = []
        current_seq = 1

        # 5. Extract Student Rows
        for r_idx, row in enumerate(ws.iter_rows(min_row=header_row_idx + 1, values_only=True), start=header_row_idx + 1):
            if not row or all(v is None or str(v).strip() == "" for v in row):
                continue

            # Extract Name
            raw_name = row[name_col] if name_col is not None and name_col < len(row) else None
            sanitized_name = cls.sanitize_cell_value(raw_name)

            if not sanitized_name:
                continue

            # Check if this row is a signature/footer block
            if any(sanitized_name.lower().startswith(kw) for kw in STOP_KEYWORDS):
                break

            # Extract NISN
            raw_nisn = row[nisn_col] if nisn_col is not None and nisn_col < len(row) else None
            sanitized_nisn = cls.sanitize_cell_value(raw_nisn)
            if not sanitized_nisn:
                sanitized_nisn = "-"

            # Extract Gender
            raw_gender = row[gender_col] if gender_col is not None and gender_col < len(row) else None
            normalized_gender = cls.normalize_gender(raw_gender)

            # Extract No Absen
            nomor_val = current_seq
            if nomor_col is not None and nomor_col < len(row):
                raw_no = row[nomor_col]
                try:
                    if raw_no is not None:
                        nomor_val = int(float(str(raw_no).strip()))
                except ValueError:
                    nomor_val = current_seq

            students.append(
                StudentParsedItem(
                    nomor_absen=nomor_val,
                    nisn=sanitized_nisn,
                    nama_lengkap=sanitized_name,
                    jenis_kelamin=normalized_gender,
                )
            )
            current_seq += 1

        return ClassroomParseResponseData(
            detected_header_row=header_row_idx,
            column_mappings={
                "nomor": nomor_col,
                "nisn": nisn_col,
                "nama": name_col,
                "jenis_kelamin": gender_col,
            },
            total_rows=len(students),
            students=students,
            warnings=warnings,
        )

    @classmethod
    def generate_official_template(cls) -> io.BytesIO:
        """Generates the official GuruDok student roster Excel template with formatting and guidance."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Data Siswa"

        # Theme Colors
        teal_dark = "0D9488"
        gray_light = "F1F5F9"
        border_color = "CBD5E1"

        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color=teal_dark, end_color=teal_dark, fill_type="solid")
        title_font = Font(name="Calibri", size=14, bold=True, color="0F172A")
        sub_font = Font(name="Calibri", size=10, italic=True, color="64748B")
        data_font = Font(name="Calibri", size=11, color="1E293B")

        thin_side = Side(border_style="thin", color=border_color)
        cell_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        center_align = Alignment(horizontal="center", vertical="center")
        left_align = Alignment(horizontal="left", vertical="center")

        # Title Block
        ws["A1"] = "FORMAT DATA SISWA KELAS — GURUDOK"
        ws["A1"].font = title_font
        ws["A2"] = "Panduan: Isi daftar nama siswa, NISN, dan jenis kelamin (L/P). File ini dapat langsung diunggah ke GuruDok."
        ws["A2"].font = sub_font

        # Headers
        headers = ["No", "NISN", "Nama Lengkap Siswa", "Jenis Kelamin (L/P)"]
        for col_idx, text in enumerate(headers, start=1):
            cell = ws.cell(row=4, column=col_idx, value=text)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align
            cell.border = cell_border

        # Sample Guidance Rows
        sample_data = [
            (1, "0081234561", "Ahmad Fauzi", "L"),
            (2, "0081234562", "Budi Santoso", "L"),
            (3, "0081234563", "Citra Dewi Lestari", "P"),
            (4, "0081234564", "Dewi Sartika", "P"),
            (5, "0081234565", "Eko Prasetyo", "L"),
        ]

        for r_offset, row_values in enumerate(sample_data, start=5):
            for c_idx, val in enumerate(row_values, start=1):
                cell = ws.cell(row=r_offset, column=c_idx, value=val)
                cell.font = data_font
                cell.border = cell_border
                cell.alignment = center_align if c_idx in (1, 2, 4) else left_align

        # Column Widths
        ws.column_dimensions["A"].width = 8
        ws.column_dimensions["B"].width = 18
        ws.column_dimensions["C"].width = 35
        ws.column_dimensions["D"].width = 20

        bio = io.BytesIO()
        wb.save(bio)
        bio.seek(0)
        return bio
