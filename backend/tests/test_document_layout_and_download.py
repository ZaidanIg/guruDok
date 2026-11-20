import io
from docx import Document
from docx.oxml.ns import qn
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import AuthService


@pytest.fixture
def client():
    return TestClient(app)


def test_docx_table_widths_within_160mm(client):
    """TDD Green Phase: All generated tables in .docx across all 7 services must not exceed 160 mm to prevent overflow on mobile & iOS."""
    services = [
        ("03_cp_tp", "SMA-K11-INF", 11),
        ("04_atp", "SMA-K11-INF", 11),
        ("05_prota", "SMA-K11-INF", 11),
        ("06_promes", "SMA-K11-INF", 11),
        ("07_kktp", "SMA-K11-INF", 11),
        ("08_modul_ajar", "SMA-K11-INF", 11),
        ("09_lkpd", "SMA-K11-INF", 11),
    ]
    MAX_DXA = 9100

    for s_id, subj_id, grade in services:
        res = client.post(
            "/api/v1/documents/generate",
            json={
                "service_id": s_id,
                "jenjang": "SMA",
                "kelas": grade,
                "subject_id": subj_id,
                "semester": 1,
                "paper_size": "A4",
                "output_format": "docx",
            },
        )
        assert res.status_code == 201, f"Failed generating {s_id}"
        dl_url = res.json()["data"]["download_url"]
        dl_res = client.get(dl_url)
        assert dl_res.status_code == 200

        doc = Document(io.BytesIO(dl_res.content))
        for idx, table in enumerate(doc.tables):
            tbl_pr = table._tbl.tblPr
            tbl_w = tbl_pr.find(qn("w:tblW"))
            if tbl_w is not None and tbl_w.get(qn("w:type")) == "dxa":
                raw_w = tbl_w.get(qn("w:w")) or tbl_w.get(qn("w:val"))
                if raw_w:
                    width_dxa = int(raw_w)
                    assert width_dxa <= MAX_DXA, f"Service {s_id} Table {idx} width {width_dxa} dxa ({width_dxa / 56.6929:.1f} mm) exceeds 160 mm (9070 dxa)!"


def test_docx_kop_divider_uses_native_xml_border(client):
    """TDD Red Phase: KOP divider must use XML paragraph border instead of string dashes that wrap on mobile/iOS."""
    res = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "08_modul_ajar",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "A4",
            "output_format": "docx",
        },
    )
    assert res.status_code == 201
    dl_url = res.json()["data"]["download_url"]
    dl_res = client.get(dl_url)
    assert dl_res.status_code == 200

    doc = Document(io.BytesIO(dl_res.content))
    # Check that no paragraph contains string dash overflow ("―" * 20 or more)
    for p in doc.paragraphs:
        assert "――――――――" not in p.text, "Found fragile string dash divider in KOP! Must use native XML border."

    # Verify that a paragraph in the KOP contains the XML bottom border
    has_bottom_border = False
    for p in doc.paragraphs[:5]:
        p_pr = p._p.get_or_add_pPr()
        p_bdr = p_pr.find(qn("w:pBdr"))
        if p_bdr is not None and p_bdr.find(qn("w:bottom")) is not None:
            has_bottom_border = True
            break
    assert has_bottom_border, "KOP official divider must use native OpenXML w:bottom border!"


def test_download_endpoint_with_query_token_auth(client):
    """TDD: Download endpoint safely authenticates via ?token= query param for mobile & iOS native downloads."""
    # Create valid auth token
    auth_service = AuthService()
    token = auth_service.create_access_token({
        "id": "teacher-test-1",
        "email": "guru@sekolah.id",
        "full_name": "Guru Test",
        "role": "teacher",
    })

    # Test PDF generation and authenticated download via ?token=
    res_pdf = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "08_modul_ajar",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "F4",
            "output_format": "pdf",
        },
    )
    assert res_pdf.status_code == 201
    pdf_filename = res_pdf.json()["data"]["filename"]
    assert pdf_filename.endswith(".pdf")

    # Download with query param token
    dl_pdf = client.get(f"/api/v1/documents/{pdf_filename}/download?token={token}")
    assert dl_pdf.status_code == 200
    assert dl_pdf.headers.get("content-type") == "application/pdf"
    assert f'filename="{pdf_filename}"' in dl_pdf.headers.get("content-disposition", "")
    assert dl_pdf.content.startswith(b"%PDF-")

    # Test XLSX generation and authenticated download via ?token=
    res_xlsx = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "06_promes",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "F4",
            "output_format": "xlsx",
        },
    )
    assert res_xlsx.status_code == 201
    xlsx_filename = res_xlsx.json()["data"]["filename"]
    assert xlsx_filename.endswith(".xlsx")

    dl_xlsx = client.get(f"/api/v1/documents/{xlsx_filename}/download?token={token}")
    assert dl_xlsx.status_code == 200
    assert dl_xlsx.headers.get("content-type") == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert dl_xlsx.content.startswith(b"PK\x03\x04")
