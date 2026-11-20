import io
import pytest
import openpyxl
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_TEACHER = {
    "nama_guru": "Siti Aminah, S.Pd.",
    "nip_guru": "198507122010012005",
    "nama_sekolah": "SD Negeri 1 Purwokerto",
    "nama_kepala_sekolah": "Bambang Hidayat, M.M.",
    "nip_kepala_sekolah": "197203151998021001",
    "kabupaten_kota": "Banyumas",
    "provinsi": "Jawa Tengah",
    "tahun_ajaran": "2026/2027",
    "no_whatsapp": "+6281234567890",
}

SAMPLE_STUDENTS = [
    {"nomor_absen": 1, "nisn": "0081234561", "nama_lengkap": "Ahmad Fauzi", "jenis_kelamin": "L"},
    {"nomor_absen": 2, "nisn": "0081234562", "nama_lengkap": "Budi Santoso", "jenis_kelamin": "L"},
    {"nomor_absen": 3, "nisn": "0081234563", "nama_lengkap": "Citra Lestari", "jenis_kelamin": "P"},
]


class TestServicesPresensiAndDaftarNilai:
    """TDD Test Suite for Service 13 (Presensi Siswa) and Service 15 (Daftar Nilai) in Active Formula .xlsx format."""

    def test_generate_presensi_siswa_xlsx_active_formulas(self):
        """Service 13: Must generate .xlsx with active COUNTIF & IF formulas for dates 1-31 and attendance summary."""
        payload = {
            "service_id": "13_presensi",
            "jenjang": "SD",
            "kelas": 4,
            "subject_id": "SD-K4-MAT",
            "semester": 1,
            "paper_size": "F4",
            "output_format": "xlsx",
            "teacher_profile": SAMPLE_TEACHER,
            "custom_overrides": {
                "nama_rombel": "Kelas 4-A",
                "bulan_presensi": "Agustus",
                "students": SAMPLE_STUDENTS,
            },
        }

        response = client.post("/api/v1/documents/generate", json=payload)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True

        # Download the file content
        file_url = data["data"]["download_url"]
        dl_response = client.get(file_url)
        assert dl_response.status_code == 200
        assert dl_response.content.startswith(b"PK\x03\x04")

        # Inspect workbook with data_only=False to read formula strings
        wb = openpyxl.load_workbook(io.BytesIO(dl_response.content), data_only=False)
        ws = wb.active
        assert ws is not None

        # Verify KOP info in top rows
        text_content = [str(cell.value) for row in ws.iter_rows(max_row=8) for cell in row if cell.value]
        assert any("PRESENSI" in t.upper() or "ABSENSI" in t.upper() for t in text_content)
        assert any("SD NEGERI 1 PURWOKERTO" in t.upper() for t in text_content)

        # Verify students exist
        all_text = [str(cell.value) for row in ws.iter_rows() for cell in row if cell.value]
        assert any("Ahmad Fauzi" in t for t in all_text)
        assert any("Citra Lestari" in t for t in all_text)

        # Verify Active Formulas in attendance summary columns
        formula_cells = [str(cell.value) for row in ws.iter_rows() for cell in row if str(cell.value).startswith("=")]
        assert len(formula_cells) > 0, "Excel sheet must contain active formulas!"
        assert any("COUNTIF" in f for f in formula_cells), "Attendance summary must contain COUNTIF formulas"
        assert any("IF" in f for f in formula_cells), "Attendance percentage must contain IF formula"

    def test_generate_daftar_nilai_xlsx_active_formulas(self):
        """Service 15: Must generate .xlsx with active AVERAGE, ROUND, IF (KKTP), and summary statistics formulas."""
        payload = {
            "service_id": "15_daftar_nilai",
            "jenjang": "SD",
            "kelas": 4,
            "subject_id": "SD-K4-MAT",
            "semester": 1,
            "paper_size": "F4",
            "output_format": "xlsx",
            "teacher_profile": SAMPLE_TEACHER,
            "custom_overrides": {
                "nama_rombel": "Kelas 4-A",
                "kktp_nilai": 75,
                "students": SAMPLE_STUDENTS,
            },
        }

        response = client.post("/api/v1/documents/generate", json=payload)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True

        file_url = data["data"]["download_url"]
        dl_response = client.get(file_url)
        assert dl_response.status_code == 200

        wb = openpyxl.load_workbook(io.BytesIO(dl_response.content), data_only=False)
        ws = wb.active
        assert ws is not None

        # Verify title and KKTP indicator
        all_text = [str(cell.value) for row in ws.iter_rows() for cell in row if cell.value]
        assert any("DAFTAR NILAI" in t.upper() for t in all_text)
        assert any("75" in t for t in all_text)

        # Verify student names
        assert any("Ahmad Fauzi" in t for t in all_text)

        # Verify Active Formulas
        formula_cells = [str(cell.value) for row in ws.iter_rows() for cell in row if str(cell.value).startswith("=")]
        assert len(formula_cells) > 0, "Daftar Nilai sheet must contain active Excel formulas"
        assert any("AVERAGE" in f for f in formula_cells), "Must contain AVERAGE formula for formatif/class average"
        assert any("IF" in f and ("TUNTAS" in f or "BELUM" in f) for f in formula_cells), "Must contain IF status formula with KKTP"
        assert any("MAX" in f for f in formula_cells), "Must contain MAX formula for highest score"
        assert any("MIN" in f for f in formula_cells), "Must contain MIN formula for lowest score"

    def test_generate_presensi_with_empty_students_fallback(self):
        """If students list is empty, generator must provide default numbered blank rows with formulas."""
        payload = {
            "service_id": "13_presensi",
            "jenjang": "SMP",
            "kelas": 7,
            "subject_id": "SMP-K7-IPA",
            "semester": 1,
            "paper_size": "F4",
            "output_format": "xlsx",
            "teacher_profile": SAMPLE_TEACHER,
            "custom_overrides": {
                "nama_rombel": "Kelas 7-A",
                "students": [],
            },
        }

        response = client.post("/api/v1/documents/generate", json=payload)
        assert response.status_code == 201
        dl_response = client.get(response.json()["data"]["download_url"])
        wb = openpyxl.load_workbook(io.BytesIO(dl_response.content), data_only=False)
        ws = wb.active
        assert ws is not None
        # Must have blank rows with formula cells
        formula_cells = [str(cell.value) for row in ws.iter_rows() for cell in row if str(cell.value).startswith("=")]
        assert len(formula_cells) > 0
