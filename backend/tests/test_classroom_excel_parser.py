import io
import pytest
import openpyxl
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def create_in_memory_xlsx(rows: list) -> io.BytesIO:
    """Helper to generate an in-memory .xlsx file bytes."""
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio


class TestClassroomExcelParser:
    """TDD Test Suite for Classroom Excel Stateless Parser & Template Generator."""

    def test_parse_standard_excel_success(self):
        """Test parsing a standard clean Excel file with header at row 1."""
        rows = [
            ["No", "NISN", "Nama Siswa", "Jenis Kelamin"],
            [1, "0081234561", "Ahmad Fauzi", "L"],
            [2, "0081234562", "Budi Santoso", "Laki-laki"],
            [3, "0081234563", "Citra Lestari", "P"],
            [4, "0081234564", "Dewi Sartika", "Perempuan"],
        ]
        xlsx_bio = create_in_memory_xlsx(rows)

        response = client.post(
            "/api/v1/classrooms/parse-excel",
            files={"file": ("siswa_kelas_4a.xlsx", xlsx_bio.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        result = data["data"]

        assert result["detected_header_row"] == 1
        assert len(result["students"]) == 4

        s1 = result["students"][0]
        assert s1["nomor_absen"] == 1
        assert s1["nisn"] == "0081234561"
        assert s1["nama_lengkap"] == "Ahmad Fauzi"
        assert s1["jenis_kelamin"] == "L"

        s2 = result["students"][1]
        assert s2["jenis_kelamin"] == "L"  # Normalized from 'Laki-laki'

        s4 = result["students"][3]
        assert s4["jenis_kelamin"] == "P"  # Normalized from 'Perempuan'

    def test_parse_flexible_excel_with_kop_and_empty_rows(self):
        """Test auto-header detection when teacher has school header/kop in rows 1-3."""
        rows = [
            ["PEMERINTAH KABUPATEN BANYUMAS"],
            ["DINAS PENDIDIKAN DAN KEBUDAYAAN"],
            ["DAFTAR PESERTA DIDIK KELAS IV-A TAHUN AJARAN 2026/2027"],
            [],  # Empty row 4
            ["No Urut", "No Induk", "Nama Peserta Didik", "L/P", "Alamat Domisili"],  # Header row 5
            [1, "1234", "Eko Prasetyo", "L", "Purwokerto"],
            [2, "1235", "Fitriani", "P", "Sokaraja"],
        ]
        xlsx_bio = create_in_memory_xlsx(rows)

        response = client.post(
            "/api/v1/classrooms/parse-excel",
            files={"file": ("dapodik_siswa.xlsx", xlsx_bio.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        assert response.status_code == 200
        result = response.json()["data"]
        assert result["detected_header_row"] == 5
        assert len(result["students"]) == 2
        assert result["students"][0]["nama_lengkap"] == "Eko Prasetyo"
        assert result["students"][0]["jenis_kelamin"] == "L"
        assert result["students"][1]["nama_lengkap"] == "Fitriani"
        assert result["students"][1]["jenis_kelamin"] == "P"

    def test_security_reject_invalid_magic_bytes(self):
        """FileAttackGuard: Uploading a non-xlsx file with .xlsx extension must return HTTP 400."""
        fake_content = b"This is plain text pretending to be an excel spreadsheet."
        response = client.post(
            "/api/v1/classrooms/parse-excel",
            files={"file": ("malicious.xlsx", fake_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        assert response.status_code == 400
        assert "format Excel" in response.json().get("detail", "") or "signature" in response.json().get("detail", "").lower()

    def test_security_reject_oversized_file(self):
        """FileAttackGuard: Uploading file > 2 MB must return HTTP 413 or 400."""
        large_bytes = b"PK\x03\x04" + (b"0" * (2 * 1024 * 1024 + 100))
        response = client.post(
            "/api/v1/classrooms/parse-excel",
            files={"file": ("large_file.xlsx", large_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        assert response.status_code in (400, 413)

    def test_security_sanitize_formula_injection(self):
        """Formula injection (=cmd, +cmd, @cmd) must be neutralized without active formula triggers."""
        rows = [
            ["No", "NISN", "Nama Siswa", "Jenis Kelamin"],
            [1, "001", "=cmd|'/C calc'!A0", "L"],
            [2, "002", "+2+5", "P"],
        ]
        xlsx_bio = create_in_memory_xlsx(rows)

        response = client.post(
            "/api/v1/classrooms/parse-excel",
            files={"file": ("formula_injected.xlsx", xlsx_bio.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        assert response.status_code == 200
        students = response.json()["data"]["students"]
        assert len(students) == 2

        # Formula prefix must be stripped (does not start with active '=' or '+' trigger)
        assert not students[0]["nama_lengkap"].startswith("=")
        assert not students[1]["nama_lengkap"].startswith("+")

    def test_security_reject_script_injection_xss(self):
        """InputSanitizer: Script injection (<script>alert) must be strictly rejected with HTTP 400."""
        rows = [
            ["No", "NISN", "Nama Siswa", "Jenis Kelamin"],
            [1, "002", "<script>alert('xss')</script>Siti Aminah", "P"],
        ]
        xlsx_bio = create_in_memory_xlsx(rows)

        response = client.post(
            "/api/v1/classrooms/parse-excel",
            files={"file": ("xss_injected.xlsx", xlsx_bio.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        assert response.status_code == 400
        assert "script injection" in response.json().get("detail", "").lower()

    def test_download_official_template_excel(self):
        """Test downloading the official GuruDok student template."""
        response = client.get("/api/v1/classrooms/template-excel")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert response.content.startswith(b"PK\x03\x04")

        # Verify workbook integrity
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        ws = wb.active
        assert ws is not None
        # Verify header title contains GuruDok or Data Siswa
        text_content = [str(cell.value) for row in ws.iter_rows() for cell in row if cell.value is not None]
        assert any("SISWA" in t.upper() for t in text_content)
