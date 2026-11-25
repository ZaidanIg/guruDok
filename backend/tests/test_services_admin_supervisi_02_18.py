import re
import zipfile
from io import BytesIO
import pytest
from docx import Document
from fastapi.testclient import TestClient

from app.core.security import FileAttackGuard
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_service_02_admin_kelas_docx_pdf_and_preview(client):
    """TDD Sprint 55: Service 02_admin_kelas generates DOCX, PDF, and /preview-pdf."""
    payload = {
        "service_id": "02_admin_kelas",
        "jenjang": "SMA",
        "kelas": 11,
        "subject_id": "SMA-K11-INF",
        "semester": 1,
        "paper_size": "F4",
        "custom_overrides": {
            "nama_rombel": "XI-F2",
            "students": [
                {"nomor_absen": 1, "nisn": "0081112221", "nama_lengkap": "Alya Putri Rahma"},
                {"nomor_absen": 2, "nisn": "0081112222", "nama_lengkap": "Bima Pratama"},
                {"nomor_absen": 3, "nisn": "0081112223", "nama_lengkap": "Citra Lestari"},
                {"nomor_absen": 4, "nisn": "0081112224", "nama_lengkap": "Dimas Saputra"},
            ],
            "ketua_kelas": "Alya Putri Rahma",
            "wakil_ketua_kelas": "Bima Pratama",
            "sekretaris_kelas": "Citra Lestari",
            "bendahara_kelas": "Dimas Saputra",
            "denah_duduk": "Kelompok Kolaboratif",
            "jadwal_piket": {
                "Senin": ["Alya Putri Rahma", "Bima Pratama"],
                "Selasa": ["Citra Lestari", "Dimas Saputra"],
            },
            "kesepakatan_kelas": [
                "Hadir tepat waktu sebelum bel masuk berbunyi.",
                "Menjaga kebersihan dan ketertiban ruang kelas bersama.",
            ],
        },
    }

    # 1. DOCX
    res_docx = client.post("/api/v1/documents/generate", json={**payload, "output_format": "docx"})
    assert res_docx.status_code == 201, f"S02 DOCX failed: {res_docx.text}"
    dl_docx = client.get(res_docx.json()["data"]["download_url"])
    assert dl_docx.status_code == 200
    doc = Document(BytesIO(dl_docx.content))
    doc_text = "\n".join(p.text for p in doc.paragraphs)
    table_text = "\n".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
    combined = f"{doc_text}\n{table_text}"
    assert "ADMINISTRASI KELAS" in combined.upper()
    assert "STRUKTUR ORGANISASI" in combined.upper()
    assert "Alya Putri Rahma" in combined
    assert "JADWAL PIKET" in combined.upper()
    assert "Kelompok Kolaboratif" in combined
    assert "Hadir tepat waktu sebelum bel masuk berbunyi." in combined

    # 2. PDF + /preview-pdf
    res_pdf = client.post("/api/v1/documents/generate", json={**payload, "output_format": "pdf"})
    assert res_pdf.status_code == 201, f"S02 PDF failed: {res_pdf.text}"
    dl_pdf = client.get(res_pdf.json()["data"]["download_url"])
    assert dl_pdf.status_code == 200
    assert dl_pdf.content[:5] == b"%PDF-"
    boxes = re.findall(rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*\]", dl_pdf.content)
    assert len(boxes) >= 1 and float(boxes[0][1]) > float(boxes[0][0])

    prev = client.post("/api/v1/documents/preview-pdf", json={**payload, "output_format": "pdf"})
    assert prev.status_code == 200
    assert prev.content[:5] == b"%PDF-"


def test_service_18_paket_supervisi_zip_docx_pdf_and_preview(client):
    """TDD Sprint 55: Service 18_paket_supervisi creates valid Master ZIP archive, DOCX, PDF, and /preview-pdf."""
    payload = {
        "service_id": "18_paket_supervisi",
        "jenjang": "SMA",
        "kelas": 11,
        "subject_id": "SMA-K11-INF",
        "semester": 1,
        "paper_size": "F4",
        "custom_overrides": {
            "nama_rombel": "VIII-A",
            "nomor_sk_mengajar": "800/142/SMPN1/2025",
            "tanggal_supervisi": "2025-11-18",
            "nama_pengawas": "Drs. Hendra Wijaya, M.Pd.",
            "nip_pengawas": "196904121994031005",
            "students": [
                {"nomor_absen": 1, "nisn": "0102223331", "nama_lengkap": "Nadia Kusuma"},
                {"nomor_absen": 2, "nisn": "0102223332", "nama_lengkap": "Rafi Alfarizi"},
            ],
        },
    }

    # 1. Default format should resolve to ZIP Master Bundle
    res_zip = client.post("/api/v1/documents/generate", json=payload)
    assert res_zip.status_code == 201, f"S18 ZIP failed: {res_zip.text}"
    res_data = res_zip.json()["data"]
    assert res_data["file_format"] == "zip"
    assert res_data["filename"].endswith(".zip")
    assert ".zip/" in res_data["download_url"]

    dl_zip = client.get(res_data["download_url"])
    assert dl_zip.status_code == 200
    assert "zip" in dl_zip.headers.get("content-type", "").lower()
    assert dl_zip.content[:4] == b"PK\x03\x04"

    with zipfile.ZipFile(BytesIO(dl_zip.content), "r") as zf:
        assert zf.testzip() is None
        names = zf.namelist()
        assert len(names) >= 10
        assert any(n.endswith(".docx") for n in names)
        assert any(n.endswith(".xlsx") for n in names)
        assert any(n.endswith(".pdf") for n in names)

    # 2. DOCX Binder + Instrumen Supervisi
    res_docx = client.post("/api/v1/documents/generate", json={**payload, "output_format": "docx"})
    assert res_docx.status_code == 201, f"S18 DOCX failed: {res_docx.text}"
    dl_docx = client.get(res_docx.json()["data"]["download_url"])
    doc = Document(BytesIO(dl_docx.content))
    combined = "\n".join(
        [p.text for p in doc.paragraphs]
        + [c.text for t in doc.tables for r in t.rows for c in r.cells]
    )
    assert "SUPERVISI" in combined.upper()
    assert "800/142/SMPN1/2025" in combined
    assert "Drs. Hendra Wijaya, M.Pd." in combined
    assert "PENGESAHAN" in combined.upper()

    # 3. PDF Binder + /preview-pdf
    res_pdf = client.post("/api/v1/documents/generate", json={**payload, "output_format": "pdf"})
    assert res_pdf.status_code == 201
    dl_pdf = client.get(res_pdf.json()["data"]["download_url"])
    assert dl_pdf.content[:5] == b"%PDF-"

    prev = client.post("/api/v1/documents/preview-pdf", json={**payload, "output_format": "pdf"})
    assert prev.status_code == 200
    assert prev.content[:5] == b"%PDF-"


def test_service_02_18_security_xss_and_zip_guard(client):
    """TDD Sprint 55: Rejects XSS payloads in Service 02/18 overrides and validates .zip signature."""
    bad_s02 = {
        "service_id": "02_admin_kelas",
        "jenjang": "SD",
        "kelas": 4,
        "subject_id": "SD-K04-MTK",
        "semester": 1,
        "paper_size": "F4",
        "custom_overrides": {"ketua_kelas": "<script>alert('xss')</script>"},
    }
    res_s02 = client.post("/api/v1/documents/generate", json=bad_s02)
    assert res_s02.status_code == 400

    bad_s18 = {
        "service_id": "18_paket_supervisi",
        "jenjang": "SMA",
        "kelas": 10,
        "subject_id": "SMA-K10-INF",
        "semester": 1,
        "paper_size": "F4",
        "custom_overrides": {"nomor_sk_mengajar": "<script>alert(1)</script>"},
    }
    res_s18 = client.post("/api/v1/documents/generate", json=bad_s18)
    assert res_s18.status_code == 400

    assert FileAttackGuard.verify_file_signature(b"PK\x03\x04validzip", ".zip") is True
    assert FileAttackGuard.verify_file_signature(b"BADHEADER", ".zip") is False
