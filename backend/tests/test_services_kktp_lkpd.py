from io import BytesIO
import pytest
from docx import Document
from openpyxl import load_workbook
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_generate_kktp_docx_f4_and_a4(client):
    """TDD: Service 07_kktp generates official DOCX with 4-scale interval table & TP rubric."""
    for paper in ("F4", "A4"):
        res = client.post(
            "/api/v1/documents/generate",
            json={
                "service_id": "07_kktp",
                "jenjang": "SMA",
                "kelas": 11,
                "subject_id": "SMA-K11-INF",
                "semester": 1,
                "paper_size": paper,
                "output_format": "docx",
            },
        )
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["service_id"] == "07_kktp"
        assert data["filename"].endswith(".docx")

        dl = client.get(data["download_url"])
        assert dl.status_code == 200
        assert dl.content[:4] == b"PK\x03\x04"

        doc = Document(BytesIO(dl.content))
        full_text = "\n".join(p.text for p in doc.paragraphs)
        table_text = "\n".join(
            cell.text for tbl in doc.tables for row in tbl.rows for cell in row.cells
        )
        combined = full_text + "\n" + table_text
        assert "KRITERIA KETERCAPAIAN TUJUAN PEMBELAJARAN" in combined.upper()
        assert "Perlu Bimbingan" in combined
        assert "Sangat Baik" in combined


def test_generate_kktp_xlsx_with_active_formulas(client):
    """TDD: Service 07_kktp generates XLSX with active Excel formulas (=IF, =AVERAGE)."""
    res = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "07_kktp",
            "jenjang": "SMP",
            "kelas": 8,
            "subject_id": "SMP-K8-IPA",
            "semester": 1,
            "paper_size": "F4",
            "output_format": "xlsx",
        },
    )
    assert res.status_code == 201
    dl = client.get(res.json()["data"]["download_url"])
    assert dl.status_code == 200

    wb = load_workbook(BytesIO(dl.content), data_only=False)
    ws = wb.active
    cell_values = [
        str(cell.value)
        for row in ws.iter_rows()
        for cell in row
        if cell.value is not None
    ]
    formulas = [v for v in cell_values if v.startswith("=")]
    assert any("IF(" in f.upper() for f in formulas)
    assert any("AVERAGE(" in f.upper() for f in formulas)


def test_generate_kktp_pdf(client):
    """TDD: Service 07_kktp generates valid PDF."""
    res = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "07_kktp",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "A4",
            "output_format": "pdf",
        },
    )
    assert res.status_code == 201
    dl = client.get(res.json()["data"]["download_url"])
    assert dl.status_code == 200
    assert dl.content[:5] == b"%PDF-"


def test_generate_lkpd_docx_and_pdf(client):
    """TDD: Service 09_lkpd generates student worksheet DOCX & PDF with 3M activities."""
    res = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "09_lkpd",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "F4",
            "output_format": "docx",
        },
    )
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["service_id"] == "09_lkpd"

    dl = client.get(data["download_url"])
    assert dl.status_code == 200
    doc = Document(BytesIO(dl.content))
    combined = "\n".join(p.text for p in doc.paragraphs) + "\n" + "\n".join(
        cell.text for tbl in doc.tables for row in tbl.rows for cell in row.cells
    )
    assert "LEMBAR KERJA PESERTA DIDIK" in combined.upper()
    assert "Nama Peserta Didik" in combined

    res_pdf = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "09_lkpd",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "A4",
            "output_format": "pdf",
        },
    )
    assert res_pdf.status_code == 201
    dl_pdf = client.get(res_pdf.json()["data"]["download_url"])
    assert dl_pdf.status_code == 200
    assert dl_pdf.content[:5] == b"%PDF-"
