import re
import zlib
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _extract_decompressed_streams(pdf_bytes: bytes) -> bytes:
    """Extracts and decompresses all FlateDecode streams from PDF binary."""
    decompressed = b""
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", pdf_bytes, re.DOTALL):
        try:
            decompressed += zlib.decompress(m.group(1))
        except Exception:
            pass
    return decompressed


def test_pdf_modul_ajar_has_table_borders():
    """TDD Verification: Modul Ajar PDF must contain real table structures with official header fill color #D9E2F3 (RGB: 217, 226, 243)."""
    res = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "08_modul_ajar",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "A4",
            "output_format": "pdf",
        },
    )
    assert res.status_code == 201
    dl_url = res.json()["data"]["download_url"]
    dl_res = client.get(dl_url)
    assert dl_res.status_code == 200
    pdf_bytes = dl_res.content
    assert pdf_bytes.startswith(b"%PDF-")

    decompressed = _extract_decompressed_streams(pdf_bytes)
    assert len(decompressed) > 0, "PDF stream extraction failed"

    # Official header fill color #D9E2F3: RGB(217, 226, 243) -> in PDF: 0.851 0.8863 0.9529 rg
    has_table_header_fill = bool(
        re.search(rb"0\.851.*0\.886.*0\.952.*rg", decompressed)
        or re.search(rb"0\.8509.*0\.8862.*0\.9529.*rg", decompressed)
    )
    assert has_table_header_fill, "PDF Modul Ajar does NOT contain official table header fill color (#D9E2F3)! Tables are missing!"


def test_all_services_pdf_generation_with_tables():
    """TDD: All 7 services must generate valid PDF documents with table layout and official header colors."""
    services = [
        ("03_cp_tp", "SMA-K11-INF", 11),
        ("04_atp", "SMA-K11-INF", 11),
        ("05_prota", "SMA-K11-INF", 11),
        ("06_promes", "SMA-K11-INF", 11),
        ("07_kktp", "SMA-K11-INF", 11),
        ("08_modul_ajar", "SMA-K11-INF", 11),
        ("09_lkpd", "SMA-K11-INF", 11),
    ]

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
                "output_format": "pdf",
            },
        )
        assert res.status_code == 201, f"Failed generating PDF for {s_id}"
        dl_url = res.json()["data"]["download_url"]
        dl_res = client.get(dl_url)
        assert dl_res.status_code == 200
        assert dl_res.content.startswith(b"%PDF-")
        assert len(dl_res.content) > 1000

        decompressed = _extract_decompressed_streams(dl_res.content)
        has_table_header_fill = bool(
            re.search(rb"0\.851.*0\.886.*0\.952.*rg", decompressed)
            or re.search(rb"0\.8509.*0\.8862.*0\.9529.*rg", decompressed)
        )
        assert has_table_header_fill, f"Service {s_id} PDF missing table header styling (#D9E2F3)"
