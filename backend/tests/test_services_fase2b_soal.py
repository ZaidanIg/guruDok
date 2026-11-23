from io import BytesIO
import pytest
from docx import Document
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _sample_questions():
    return [
        {
            "id": "q-1",
            "tipe_soal": "PG",
            "tp_code": "TP.11.1.1",
            "level_kognitif": "C1-C2",
            "stimulus": "Bacalah teks berikut: Berpikir komputasional membantu memecahkan masalah kompleks menjadi bagian kecil.",
            "pertanyaan": "Proses memecah masalah besar menjadi bagian-bagian kecil yang lebih mudah dikelola disebut...",
            "opsi": ["Dekomposisi", "Pengenalan Pola", "Abstraksi", "Algoritma", "Iterasi"],
            "kunci_jawaban": "A",
            "bobot_skor": 20,
            "pembahasan": "Dekomposisi adalah pemecahan masalah kompleks menjadi sub-masalah.",
        },
        {
            "id": "q-2",
            "tipe_soal": "PG",
            "tp_code": "TP.11.1.2",
            "level_kognitif": "C3",
            "stimulus": "",
            "pertanyaan": "Struktur data yang bekerja dengan prinsip LIFO (Last In, First Out) adalah...",
            "opsi": ["Queue", "Stack", "Tree", "Graph", "Array"],
            "kunci_jawaban": "B",
            "bobot_skor": 20,
            "pembahasan": "Stack (tumpukan) menggunakan prinsip LIFO.",
        },
        {
            "id": "q-3",
            "tipe_soal": "URAIAN",
            "tp_code": "TP.11.1.2",
            "level_kognitif": "C4-C6",
            "stimulus": "Sebuah aplikasi antrean rumah sakit memproses pasien berdasarkan urutan kedatangan.",
            "pertanyaan": "Analisislah struktur data apa yang paling tepat digunakan dan jelaskan alasannya!",
            "opsi": [],
            "kunci_jawaban": "Queue (Antrean) karena menggunakan prinsip FIFO (First In, First Out).",
            "bobot_skor": 60,
            "pembahasan": "Queue memastikan pasien yang datang pertama dilayani lebih dahulu.",
        },
    ]


def test_generate_service_10_kuis_docx_and_pdf(client):
    """TDD: Service 10_kuis generates DOCX (F4/A4) & PDF with questions, stimulus, and answer key."""
    for paper in ("F4", "A4"):
        res = client.post(
            "/api/v1/documents/generate",
            json={
                "service_id": "10_kuis",
                "jenjang": "SMA",
                "kelas": 11,
                "subject_id": "SMA-K11-INF",
                "semester": 1,
                "chapter_id": "INF-K11-B01",
                "paper_size": paper,
                "output_format": "docx",
                "custom_overrides": {
                    "butir_soal_kustom": _sample_questions(),
                    "tipe_soal_kuis": "CAMPURAN",
                },
            },
        )
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["service_id"] == "10_kuis"
        assert data["filename"].endswith(".docx")

        dl = client.get(data["download_url"])
        assert dl.status_code == 200
        assert dl.content[:4] == b"PK\x03\x04"

        doc = Document(BytesIO(dl.content))
        combined = "\n".join(p.text for p in doc.paragraphs) + "\n" + "\n".join(
            c.text for t in doc.tables for r in t.rows for c in r.cells
        )
        assert "KUIS HARIAN" in combined.upper()
        assert "Dekomposisi" in combined
        assert "KUNCI JAWABAN" in combined.upper()

    res_pdf = client.post(
        "/api/v1/documents/generate",
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
                "butir_soal_kustom": _sample_questions(),
            },
        },
    )
    assert res_pdf.status_code == 201
    dl_pdf = client.get(res_pdf.json()["data"]["download_url"])
    assert dl_pdf.status_code == 200
    assert dl_pdf.content[:5] == b"%PDF-"


def test_generate_service_11_sumatif_bab_docx_and_pdf(client):
    """TDD: Service 11_sumatif_bab generates DOCX & PDF with scoring rubric (Skor Maks 100) and kisi-kisi."""
    res = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "11_sumatif_bab",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "chapter_id": "INF-K11-B01",
            "paper_size": "F4",
            "output_format": "docx",
            "custom_overrides": {
                "butir_soal_kustom": _sample_questions(),
            },
        },
    )
    assert res.status_code == 201
    dl = client.get(res.json()["data"]["download_url"])
    assert dl.status_code == 200
    assert dl.content[:4] == b"PK\x03\x04"

    doc = Document(BytesIO(dl.content))
    combined = "\n".join(p.text for p in doc.paragraphs) + "\n" + "\n".join(
        c.text for t in doc.tables for r in t.rows for c in r.cells
    )
    assert "ASESMEN SUMATIF" in combined.upper()
    assert "PEDOMAN PENSKORAN" in combined.upper()
    assert "100" in combined

    res_pdf = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "11_sumatif_bab",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "chapter_id": "INF-K11-B01",
            "paper_size": "A4",
            "output_format": "pdf",
            "custom_overrides": {
                "butir_soal_kustom": _sample_questions(),
            },
        },
    )
    assert res_pdf.status_code == 201
    dl_pdf = client.get(res_pdf.json()["data"]["download_url"])
    assert dl_pdf.status_code == 200
    assert dl_pdf.content[:5] == b"%PDF-"


def test_generate_service_12_sts_sas_kisi_kartu_ljk_and_paket_ab(client):
    """TDD: Service 12_sts_sas produces 7-col Kisi-Kisi, Kartu Soal, Kunci & Rubrik, LJK, and Paket A/B."""
    res_a = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "12_sts_sas",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "F4",
            "output_format": "docx",
            "custom_overrides": {
                "jenis_ujian": "STS",
                "alokasi_waktu_menit": 90,
                "paket_soal": "A",
                "butir_soal_kustom": _sample_questions(),
            },
        },
    )
    assert res_a.status_code == 201
    dl_a = client.get(res_a.json()["data"]["download_url"])
    assert dl_a.status_code == 200
    doc_a = Document(BytesIO(dl_a.content))
    text_a = "\n".join(p.text for p in doc_a.paragraphs) + "\n" + "\n".join(
        c.text for t in doc_a.tables for r in t.rows for c in r.cells
    )
    assert "KISI-KISI PENULISAN SOAL" in text_a.upper()
    assert "KARTU SOAL" in text_a.upper()
    assert "LEMBAR JAWAB" in text_a.upper()
    assert "PAKET A" in text_a.upper()

    res_b = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "12_sts_sas",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "A4",
            "output_format": "pdf",
            "custom_overrides": {
                "jenis_ujian": "SAS",
                "alokasi_waktu_menit": 90,
                "paket_soal": "B",
                "butir_soal_kustom": _sample_questions(),
            },
        },
    )
    assert res_b.status_code == 201
    dl_b = client.get(res_b.json()["data"]["download_url"])
    assert dl_b.status_code == 200
    assert dl_b.content[:5] == b"%PDF-"


def test_collection_service_silent_auto_persist_excludes_kop_surat(client):
    """TDD: POST /documents/generate silently stores questions & CP to DB via CollectionService without KOP Surat/PII."""
    unique_q = "Apa fungsi utama gerbang logika AND pada rangkaian digital modern 2026?"
    res = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "10_kuis",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "F4",
            "output_format": "docx",
            "teacher_profile": {
                "nama_guru": "RAHASIA GURU PII",
                "nip_guru": "198801012015011001",
                "nama_sekolah": "SMAN 99 RAHASIA",
                "npsn": "20109999",
                "kabupaten_kota": "Kota Bandung",
                "provinsi": "Jawa Barat",
                "nama_kepala_sekolah": "Kepsek Rahasia",
                "nip_kepala_sekolah": "197001011995011001",
                "no_whatsapp": "+6281234567890",
            },
            "custom_overrides": {
                "custom_elemen_cp": [
                    {
                        "kode_elemen": "EL-KUSTOM-01",
                        "nama_elemen": "Sistem Komputer Lanjut",
                        "deskripsi_cp": "Peserta didik mampu memahami arsitektur gerbang logika digital.",
                    }
                ],
                "butir_soal_kustom": [
                    {
                        "id": "q-unique-1",
                        "tipe_soal": "PG",
                        "tp_code": "TP.11.1.1",
                        "level_kognitif": "C1-C2",
                        "pertanyaan": unique_q,
                        "opsi": ["Menghasilkan 1 jika semua input 1", "Selalu 0", "Membalik sinyal", "Menjumlah biner"],
                        "kunci_jawaban": "A",
                        "bobot_skor": 100,
                    }
                ],
            },
        },
    )
    assert res.status_code == 201

    q_res = client.get("/api/v1/questions", params={"subject_id": "SMA-K11-INF"})
    assert q_res.status_code == 200
    items = q_res.json()["data"]
    assert any(it["pertanyaan"] == unique_q for it in items)
    serialized = str(items)
    assert "RAHASIA GURU PII" not in serialized
    assert "SMAN 99 RAHASIA" not in serialized
    assert "+6281234567890" not in serialized


def test_fase2b_security_xss_and_validation(client):
    """TDD Negative: XSS in question text -> 400; jumlah_soal_pg > 50 -> 422."""
    xss_res = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "10_kuis",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "custom_overrides": {
                "butir_soal_kustom": [
                    {
                        "tipe_soal": "PG",
                        "pertanyaan": "<script>alert('xss')</script> Apa itu CPU?",
                        "opsi": ["A", "B", "C", "D"],
                        "kunci_jawaban": "A",
                    }
                ]
            },
        },
    )
    assert xss_res.status_code == 400

    limit_res = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "12_sts_sas",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "custom_overrides": {
                "jumlah_soal_pg": 999,
            },
        },
    )
    assert limit_res.status_code == 422


def test_sprint41_two_section_numbering_reset_pg_and_essai(client):
    """TDD Sprint 41: Bagian A (PG) & Bagian B (Essai) must have separate headings and section-reset numbering."""
    from app.models.curriculum import CurriculumSubject, ChapterTopic, LearningObjective
    from app.schemas.generation import DocumentGenerateRequest, CustomDocumentOverrides, CustomQuestionItem, ServiceIdEnum
    from app.services.document_engine.question_blueprint import QuestionBlueprintEngine

    sample_subject = CurriculumSubject(
        id="SMA-K11-INF",
        nama_mapel="Informatika",
        jenjang="SMA",
        kelas=11,
        fase="F",
        alokasi_jp_mingguan=3,
        total_alokasi_jp_tahun=108,
    )
    sample_chapter = ChapterTopic(
        id="INF-K11-B01",
        semester=1,
        nomor_bab=1,
        judul_bab="Berpikir Komputasional",
        alokasi_jp=12,
        tujuan_pembelajaran=[
            LearningObjective(code="TP.11.1.1", deskripsi="Memahami strategi algoritmik", alokasi_jp=4),
        ],
    )
    req = DocumentGenerateRequest(
        service_id=ServiceIdEnum.SUMATIF_BAB,
        jenjang="SMA",
        kelas=11,
        subject_id="SMA-K11-INF",
        semester=1,
        custom_overrides=CustomDocumentOverrides(
            butir_soal_kustom=[
                CustomQuestionItem(
                    tipe_soal="PG",
                    pertanyaan="Pertanyaan PG Satu",
                    opsi=["A", "B", "C", "D"],
                    kunci_jawaban="A",
                ),
                CustomQuestionItem(
                    tipe_soal="PG",
                    pertanyaan="Pertanyaan PG Dua",
                    opsi=["A", "B", "C", "D"],
                    kunci_jawaban="B",
                ),
                CustomQuestionItem(
                    tipe_soal="URAIAN",
                    pertanyaan="Pertanyaan Essai Satu",
                    opsi=[],
                    kunci_jawaban="Rubrik Essai Satu",
                ),
            ]
        ),
    )

    bp = QuestionBlueprintEngine.build_blueprint(req, sample_subject, sample_chapter)

    # 1. Blueprint validation
    assert len(bp["pg_questions"]) == 2
    assert len(bp["essai_questions"]) == 1
    assert bp["pg_questions"][0]["section_no"] == 1
    assert bp["pg_questions"][1]["section_no"] == 2
    assert bp["essai_questions"][0]["section_no"] == 1  # Reset to 1!
    assert bp["pg_questions"][0]["bagian"] == "A"
    assert bp["essai_questions"][0]["bagian"] == "B"

    # Kisi-kisi check
    assert bp["kisi_kisi"][0]["nomor_soal"] == "A.1"
    assert bp["kisi_kisi"][1]["nomor_soal"] == "A.2"
    assert bp["kisi_kisi"][2]["nomor_soal"] == "B.1"

    # 2. DOCX Generation check
    res_docx = client.post(
        "/api/v1/documents/generate",
        json={
            "service_id": "11_sumatif_bab",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "chapter_id": "INF-K11-B01",
            "paper_size": "F4",
            "output_format": "docx",
            "custom_overrides": {
                "butir_soal_kustom": _sample_questions(),
            },
        },
    )
    assert res_docx.status_code == 201
    dl_url = res_docx.json()["data"]["download_url"]
    dl = client.get(dl_url)
    assert dl.status_code == 200

    doc = Document(BytesIO(dl.content))
    combined_paragraphs = "\n".join(p.text for p in doc.paragraphs)
    assert "A. Soal Pilihan Ganda" in combined_paragraphs
    assert "B. Soal Essai" in combined_paragraphs
    assert "Stimulus Soal No." not in combined_paragraphs
    assert "Stimulus No." not in combined_paragraphs

