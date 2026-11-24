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


def test_service_14_jurnal_generate_docx_xlsx_pdf(client):
    """TDD Sprint 49: Service 14_jurnal_mengajar generates DOCX, XLSX (formula), and PDF (Landscape 9 cols)."""
    base_payload = {
        "service_id": "14_jurnal_mengajar",
        "jenjang": "SMA",
        "kelas": 11,
        "subject_id": "SMA-K11-INF",
        "semester": 1,
        "paper_size": "F4",
        "custom_overrides": {
            "nama_rombel": "XI-F1",
            "hari_mengajar": ["Senin", "Rabu"],
            "tanggal_mulai_semester": "2026-07-13",
            "jam_mengajar": "1-3",
            "jumlah_pertemuan_jurnal": 8,
        },
    }

    # 1. DOCX
    res_docx = client.post("/api/v1/documents/generate", json={**base_payload, "output_format": "docx"})
    assert res_docx.status_code == 201, f"DOCX failed: {res_docx.text}"
    dl_docx = client.get(res_docx.json()["data"]["download_url"])
    assert dl_docx.status_code == 200
    assert dl_docx.content[:4] == b"PK\x03\x04"
    doc = Document(BytesIO(dl_docx.content))
    combined = "\n".join(p.text for p in doc.paragraphs) + "\n" + "\n".join(
        c.text for t in doc.tables for r in t.rows for c in r.cells
    )
    assert "JURNAL MENGAJAR HARIAN" in combined.upper()
    assert "XI-F1" in combined
    assert "Senin" in combined
    assert "Rabu" in combined
    assert "Hambatan & Refleksi" in combined

    # 2. XLSX with formula
    res_xlsx = client.post("/api/v1/documents/generate", json={**base_payload, "output_format": "xlsx"})
    assert res_xlsx.status_code == 201, f"XLSX failed: {res_xlsx.text}"
    dl_xlsx = client.get(res_xlsx.json()["data"]["download_url"])
    assert dl_xlsx.status_code == 200
    wb = openpyxl.load_workbook(BytesIO(dl_xlsx.content), data_only=False)
    ws = wb.active
    sheet_text = "\n".join(str(cell.value) for row in ws.iter_rows() for cell in row if cell.value is not None)
    assert "JURNAL MENGAJAR" in sheet_text.upper()
    assert "=COUNTA(" in sheet_text

    # 3. PDF Landscape
    res_pdf = client.post("/api/v1/documents/generate", json={**base_payload, "output_format": "pdf"})
    assert res_pdf.status_code == 201, f"PDF failed: {res_pdf.text}"
    dl_pdf = client.get(res_pdf.json()["data"]["download_url"])
    assert dl_pdf.status_code == 200
    assert dl_pdf.content[:5] == b"%PDF-"
    boxes = re.findall(rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*\]", dl_pdf.content)
    assert len(boxes) >= 1
    w, h = float(boxes[0][0]), float(boxes[0][1])
    assert w > h, f"Expected Landscape (w > h) for 14_jurnal_mengajar PDF, got {w}x{h}"


def test_service_14_jurnal_preview_pdf_and_xss_guard(client):
    """TDD Sprint 49: preview-pdf supports 14_jurnal_mengajar and rejects XSS in jam_mengajar."""
    prev = client.post(
        "/api/v1/documents/preview-pdf",
        json={
            "service_id": "14_jurnal_mengajar",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "A4",
            "output_format": "pdf",
        },
    )
    assert prev.status_code == 200
    assert prev.content[:5] == b"%PDF-"

    xss = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "14_jurnal_mengajar",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "F4",
            "output_format": "docx",
            "custom_overrides": {
                "jam_mengajar": "<script>alert(1)</script>",
            },
        },
    )
    assert xss.status_code == 400
