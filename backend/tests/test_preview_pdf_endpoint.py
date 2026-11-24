import re
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _extract_mediabox_sizes(pdf_bytes: bytes):
    """Extract (width_pt, height_pt) tuples from PDF MediaBox entries."""
    matches = re.findall(rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*\]", pdf_bytes)
    return [(float(w), float(h)) for w, h in matches]


def test_preview_pdf_portrait_a4_and_f4_dimensions(client):
    """TDD Sprint 43: preview-pdf returns valid watermarked PDF with exact A4 & F4 dimensions."""
    # A4: 210x297 mm -> ~595.28 x 841.89 pt
    # F4: 215x330 mm -> ~609.45 x 935.43 pt
    expected_pt = {
        "A4": (595.28, 841.89),
        "F4": (609.45, 935.43),
    }

    for paper_size, (exp_w, exp_h) in expected_pt.items():
        res = client.post(
            "/api/v1/documents/preview-pdf",
            json={
                "service_id": "10_kuis",
                "jenjang": "SMA",
                "kelas": 11,
                "subject_id": "SMA-K11-INF",
                "semester": 1,
                "chapter_id": "INF-K11-B01",
                "paper_size": paper_size,
                "output_format": "pdf",
                "custom_overrides": {
                    "butir_soal_kustom": [
                        {
                            "tipe_soal": "PG",
                            "pertanyaan": "Apa fungsi utama algoritma dekomposisi?",
                            "opsi": ["Memecah masalah", "Menghapus data", "Menggambar", "Menyalin"],
                            "kunci_jawaban": "A",
                            "tp_code": "TP.11.1.1",
                            "level_kognitif": "C1-C2",
                        }
                    ]
                },
            },
        )
        assert res.status_code == 200, f"Expected 200 for {paper_size}, got {res.status_code}: {res.text}"
        assert res.headers.get("content-type", "").startswith("application/pdf")
        assert res.content[:5] == b"%PDF-"
        assert int(res.headers.get("x-preview-page-count", "0")) >= 2
        assert "no-store" in res.headers.get("cache-control", "")

        boxes = _extract_mediabox_sizes(res.content)
        assert len(boxes) >= 1, "PDF must contain MediaBox definitions"
        w, h = boxes[0]
        assert abs(w - exp_w) < 2.0 and abs(h - exp_h) < 2.0, (
            f"Paper {paper_size} mismatch: got ({w}, {h}), expected ({exp_w}, {exp_h})"
        )


def test_preview_pdf_landscape_services(client):
    """TDD Sprint 43: Promes, Presensi, and Daftar Nilai render in Landscape orientation (width > height)."""
    for service_id in ("06_promes", "13_presensi", "15_daftar_nilai"):
        res = client.post(
            "/api/v1/documents/preview-pdf",
            json={
                "service_id": service_id,
                "jenjang": "SMA",
                "kelas": 11,
                "subject_id": "SMA-K11-INF",
                "semester": 1,
                "paper_size": "F4",
                "output_format": "pdf",
            },
        )
        assert res.status_code == 200, f"Failed for {service_id}: {res.text}"
        assert res.content[:5] == b"%PDF-"
        boxes = _extract_mediabox_sizes(res.content)
        assert len(boxes) >= 1
        w, h = boxes[0]
        assert w > h, f"Expected landscape (w > h) for {service_id}, got w={w}, h={h}"


def test_preview_pdf_zero_side_effect_on_history(client):
    """TDD Sprint 43: Calling preview-pdf must NOT record an entry in generation history."""
    before = client.get("/api/v1/documents/history").json()["data"]
    before_count = len(before)

    res = client.post(
        "/api/v1/documents/preview-pdf",
        json={
            "service_id": "03_cp_tp",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "A4",
            "output_format": "pdf",
        },
    )
    assert res.status_code == 200

    after = client.get("/api/v1/documents/history").json()["data"]
    assert len(after) == before_count, "Preview endpoint must not pollute document generation history"


def test_preview_pdf_security_xss_and_not_found(client):
    """TDD Sprint 43: preview-pdf enforces Zero-Trust Anti-XSS (HTTP 400) and 404 on unknown subject."""
    xss_res = client.post(
        "/api/v1/documents/preview-pdf",
        json={
            "service_id": "03_cp_tp",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "F4",
            "output_format": "pdf",
            "custom_overrides": {
                "topik_kontekstual": "<script>alert('xss')</script>",
            },
        },
    )
    assert xss_res.status_code == 400

    nf_res = client.post(
        "/api/v1/documents/preview-pdf",
        json={
            "service_id": "03_cp_tp",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "NON-EXISTENT-SUBJECT",
            "semester": 1,
            "paper_size": "F4",
            "output_format": "pdf",
        },
    )
    assert nf_res.status_code == 404


def test_preview_pdf_without_teacher_profile_and_alokasi_zero(client):
    """TDD Sprint 48: preview-pdf accepts missing teacher_profile and alokasi_waktu_menit=0."""
    res = client.post(
        "/api/v1/documents/preview-pdf",
        json={
            "service_id": "10_kuis",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "chapter_id": "INF-K11-B01",
            "paper_size": "A4",
            "output_format": "pdf",
            "custom_overrides": {
                "alokasi_waktu_menit": 0,
            },
        },
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    assert res.content[:5] == b"%PDF-"
