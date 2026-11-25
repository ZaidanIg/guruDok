import re
from io import BytesIO
import openpyxl
import pytest
from docx import Document
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_service_16_deskripsi_rapor_xlsx_docx_pdf(client):
    """TDD Sprint 54: Service 16_deskripsi_rapor produces e-Rapor XLSX (formula), DOCX, PDF Landscape, and preview-pdf."""
    payload = {
        "service_id": "16_deskripsi_rapor",
        "jenjang": "SMA",
        "kelas": 11,
        "subject_id": "SMA-K11-INF",
        "semester": 1,
        "paper_size": "F4",
        "custom_overrides": {
            "nama_rombel": "XI-F2",
            "kktp_nilai": 75,
            "rapor_entries": [
                {
                    "nomor_absen": 1,
                    "nisn": "0081112221",
                    "nama_lengkap": "Alya Putri Rahma",
                    "nilai_sumatif": 92,
                    "nilai_sas": 90,
                    "tp_tertinggi_code": "11.1.1",
                    "tp_terendah_code": "11.1.3",
                },
                {
                    "nomor_absen": 2,
                    "nisn": "0081112222",
                    "nama_lengkap": "Bima Pratama",
                    "nilai_sumatif": 72,
                    "nilai_sas": 74,
                    "tp_tertinggi_code": "11.1.2",
                    "tp_terendah_code": "11.1.4",
                },
            ],
        },
    }

    # 1. XLSX
    res_xlsx = client.post("/api/v1/documents/generate", json={**payload, "output_format": "xlsx"})
    assert res_xlsx.status_code == 201, f"S16 XLSX failed: {res_xlsx.text}"
    dl_xlsx = client.get(res_xlsx.json()["data"]["download_url"])
    assert dl_xlsx.status_code == 200
    wb = openpyxl.load_workbook(BytesIO(dl_xlsx.content), data_only=False)
    ws = wb.active
    sheet_text = "\n".join(str(c.value) for r in ws.iter_rows() for c in r if c.value is not None)
    assert "DESKRIPSI" in sheet_text.upper()
    assert "Alya Putri Rahma" in sheet_text
    assert "Menunjukkan penguasaan yang sangat baik" in sheet_text
    assert "AVERAGE(" in sheet_text

    # 2. DOCX
    res_docx = client.post("/api/v1/documents/generate", json={**payload, "output_format": "docx"})
    assert res_docx.status_code == 201, f"S16 DOCX failed: {res_docx.text}"
    dl_docx = client.get(res_docx.json()["data"]["download_url"])
    doc = Document(BytesIO(dl_docx.content))
    combined = "\n".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
    assert "Alya Putri Rahma" in combined
    assert "Perlu bimbingan dan pendampingan" in combined

    # 3. PDF Landscape + preview-pdf
    res_pdf = client.post("/api/v1/documents/generate", json={**payload, "output_format": "pdf"})
    assert res_pdf.status_code == 201
    dl_pdf = client.get(res_pdf.json()["data"]["download_url"])
    assert dl_pdf.content[:5] == b"%PDF-"
    boxes = re.findall(rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*\]", dl_pdf.content)
    assert len(boxes) >= 1 and float(boxes[0][0]) > float(boxes[0][1])

    prev = client.post("/api/v1/documents/preview-pdf", json={**payload, "output_format": "pdf"})
    assert prev.status_code == 200
    assert prev.content[:5] == b"%PDF-"


def test_service_17_rekap_rapor_xlsx_formulas_docx_pdf_and_security(client):
    """TDD Sprint 54: Service 17_rekap_rapor generates active ROUND/RANK/IF Excel formulas, DOCX, PDF, and guards XSS/invalid scores."""
    payload = {
        "service_id": "17_rekap_rapor",
        "jenjang": "SMA",
        "kelas": 11,
        "subject_id": "SMA-K11-INF",
        "semester": 1,
        "paper_size": "A4",
        "custom_overrides": {
            "nama_rombel": "XI-F2",
            "kktp_nilai": 75,
            "bobot_nilai": {"sumatif": 60, "sas": 40},
            "rapor_entries": [
                {
                    "nomor_absen": 1,
                    "nisn": "0081112221",
                    "nama_lengkap": "Alya Putri Rahma",
                    "nilai_sumatif": 90,
                    "nilai_sas": 85,
                },
                {
                    "nomor_absen": 2,
                    "nisn": "0081112222",
                    "nama_lengkap": "Bima Pratama",
                    "nilai_sumatif": 70,
                    "nilai_sas": 75,
                },
            ],
        },
    }

    # 1. XLSX formulas (=ROUND, =RANK, =IF, =AVERAGE, =MAX, =MIN)
    res_xlsx = client.post("/api/v1/documents/generate", json={**payload, "output_format": "xlsx"})
    assert res_xlsx.status_code == 201, f"S17 XLSX failed: {res_xlsx.text}"
    dl_xlsx = client.get(res_xlsx.json()["data"]["download_url"])
    wb = openpyxl.load_workbook(BytesIO(dl_xlsx.content), data_only=False)
    ws = wb.active
    sheet_text = "\n".join(str(c.value) for r in ws.iter_rows() for c in r if c.value is not None)
    assert "REKAP NILAI RAPOR" in sheet_text.upper()
    assert "=ROUND(" in sheet_text
    assert "=RANK(" in sheet_text
    assert "=IF(" in sheet_text
    assert "AVERAGE(" in sheet_text

    # 2. DOCX & PDF Landscape
    res_docx = client.post("/api/v1/documents/generate", json={**payload, "output_format": "docx"})
    assert res_docx.status_code == 201
    res_pdf = client.post("/api/v1/documents/generate", json={**payload, "output_format": "pdf"})
    assert res_pdf.status_code == 201
    dl_pdf = client.get(res_pdf.json()["data"]["download_url"])
    boxes = re.findall(rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*\]", dl_pdf.content)
    assert len(boxes) >= 1 and float(boxes[0][0]) > float(boxes[0][1])

    # 3. Anti-XSS inside rapor_entries
    xss_res = client.post(
        "/api/v1/documents/generate",
        json={
            **payload,
            "output_format": "xlsx",
            "custom_overrides": {
                "rapor_entries": [
                    {
                        "nama_lengkap": "<script>alert('xss')</script>",
                        "nilai_sumatif": 80,
                        "nilai_sas": 80,
                    }
                ]
            },
        },
    )
    assert xss_res.status_code == 400

    # 4. Invalid out-of-range score -> 422
    bad_score = client.post(
        "/api/v1/documents/generate",
        json={
            **payload,
            "output_format": "xlsx",
            "custom_overrides": {
                "rapor_entries": [
                    {
                        "nama_lengkap": "Test Siswa",
                        "nilai_sumatif": 150,
                        "nilai_sas": 80,
                    }
                ]
            },
        },
    )
    assert bad_score.status_code == 422
