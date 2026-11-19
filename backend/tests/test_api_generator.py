import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestApiIntegration:
    """End-to-End REST API integration tests verifying TDD compliance and security."""

    def test_health_endpoint(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "BSKAP No. 046/H/KR/2025" in data["regulation_baseline"]

    def test_curriculum_api_flow(self):
        # 1. List SMP subjects
        resp = client.get("/api/v1/curriculum/subjects?jenjang=SMP&kelas=7")
        assert resp.status_code == 200
        subjects = resp.json()["data"]
        assert len(subjects) > 0
        subject_ids = [s["id"] for s in subjects]
        assert "SMP-K7-IPA" in subject_ids

        # 2. Get Chapters for SMP-K7-IPA
        resp_ch = client.get("/api/v1/curriculum/subjects/SMP-K7-IPA/chapters?semester=1")
        assert resp_ch.status_code == 200
        chapters = resp_ch.json()["data"]
        assert len(chapters) > 0

        # 3. Get 8 Dimensions
        resp_dims = client.get("/api/v1/curriculum/dimensions")
        assert resp_dims.status_code == 200
        assert len(resp_dims.json()["data"]) >= 6

    def test_teacher_lead_profile_post_and_security(self):
        payload = {
            "nama_guru": "Siti Aminah, S.Pd.",
            "nip_guru": "198805122014022003",
            "nama_sekolah": "SMP Negeri 1 Surabaya",
            "npsn": "20531234",
            "kabupaten_kota": "Kota Surabaya",
            "provinsi": "Jawa Timur",
            "nama_kepala_sekolah": "Drs. H. Bambang Irawan, M.Pd.",
            "nip_kepala_sekolah": "196904151995121002",
            "no_whatsapp": "081234567890",
            "ukuran_kertas_default": "F4",
        }
        resp = client.post("/api/v1/teachers/profile", json=payload)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["no_whatsapp"] == "+6281234567890"  # Normalized
        assert data["nama_sekolah"] == "SMP Negeri 1 Surabaya"

    def test_teacher_profile_rejects_xss(self):
        malicious_payload = {
            "nama_guru": "Hacker <script>alert('xss')</script>",
            "nip_guru": "-",
            "nama_sekolah": "SDN 1",
            "kabupaten_kota": "Jakarta",
            "provinsi": "DKI Jakarta",
            "nama_kepala_sekolah": "Kasek",
            "nip_kepala_sekolah": "-",
            "no_whatsapp": "081234567890",
        }
        resp = client.post("/api/v1/teachers/profile", json=malicious_payload)
        assert resp.status_code == 400
        assert "SECURITY_VIOLATION" in resp.json()["error_code"]

    def test_generate_modul_ajar_docx_api(self):
        payload = {
            "service_id": "08_modul_ajar",
            "jenjang": "SMP",
            "kelas": 7,
            "subject_id": "SMP-K7-IPA",
            "semester": 1,
            "chapter_id": "IPA-K7-B01",
            "paper_size": "F4",
            "teacher_profile": {
                "nama_guru": "Siti Aminah, S.Pd.",
                "nip_guru": "198805122014022003",
                "nama_sekolah": "SMP Negeri 1 Surabaya",
                "kabupaten_kota": "Kota Surabaya",
                "provinsi": "Jawa Timur",
                "nama_kepala_sekolah": "Drs. H. Bambang Irawan, M.Pd.",
                "nip_kepala_sekolah": "196904151995121002",
                "no_whatsapp": "081234567890",
            },
            "include_lkpd": True,
            "include_asesmen": True,
            "include_rubrik": True,
        }
        resp = client.post("/api/v1/documents/generate", json=payload)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["file_format"] == "docx"
        assert data["paper_size"] == "F4"
        assert data["download_url"].startswith("/api/v1/documents/")
        assert data["execution_time_ms"] < 3000  # Generated within 3 seconds

        # Test download of this generated file
        download_resp = client.get(data["download_url"])
        assert download_resp.status_code == 200
        assert download_resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert download_resp.content.startswith(b"PK\x03\x04")

    def test_generate_promes_xlsx_api(self):
        payload = {
            "service_id": "06_promes",
            "jenjang": "SMP",
            "kelas": 7,
            "subject_id": "SMP-K7-IPA",
            "semester": 1,
            "paper_size": "F4",
            "teacher_profile": {
                "nama_guru": "Siti Aminah, S.Pd.",
                "nip_guru": "-",
                "nama_sekolah": "SMP Negeri 1 Surabaya",
                "kabupaten_kota": "Kota Surabaya",
                "provinsi": "Jawa Timur",
                "nama_kepala_sekolah": "Drs. H. Bambang Irawan, M.Pd.",
                "nip_kepala_sekolah": "-",
                "no_whatsapp": "081234567890",
            },
        }
        resp = client.post("/api/v1/documents/generate", json=payload)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["file_format"] == "xlsx"

        download_resp = client.get(data["download_url"])
        assert download_resp.status_code == 200
        assert download_resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert download_resp.content.startswith(b"PK\x03\x04")

    def test_path_traversal_attack_blocked(self):
        resp = client.get("/api/v1/documents/..%2F..%2Fetc%2Fpasswd/download")
        assert resp.status_code in [400, 404]

    def test_generation_history_api(self):
        resp = client.get("/api/v1/documents/history")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 2  # Has previous generated jobs

    def test_generate_and_download_pdf_and_xlsx_multi_format_api(self):
        """Verifies POST /api/v1/documents/generate supports output_format='pdf', 'xlsx', and 'docx' end-to-end."""
        for fmt, expected_mime, expected_magic in [
            ("pdf", "application/pdf", b"%PDF-"),
            ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", b"PK\x03\x04"),
            ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", b"PK\x03\x04"),
        ]:
            payload = {
                "service_id": "08_modul_ajar",
                "jenjang": "SMP",
                "kelas": 7,
                "subject_id": "SMP-K7-IPA",
                "semester": 1,
                "chapter_id": "IPA-K7-B01",
                "paper_size": "F4",
                "output_format": fmt,
                "teacher_profile": {
                    "nama_guru": "Siti Aminah, S.Pd.",
                    "nip_guru": "198805122014022003",
                    "nama_sekolah": "SMP Negeri 1 Surabaya",
                    "kabupaten_kota": "Kota Surabaya",
                    "provinsi": "Jawa Timur",
                    "nama_kepala_sekolah": "Drs. H. Bambang Irawan, M.Pd.",
                    "nip_kepala_sekolah": "196904151995121002",
                    "no_whatsapp": "081234567890",
                },
            }
            resp = client.post("/api/v1/documents/generate", json=payload)
            assert resp.status_code == 201
            data = resp.json()["data"]
            assert data["file_format"] == fmt
            assert data["filename"].endswith(f".{fmt}")

            dl = client.get(data["download_url"])
            assert dl.status_code == 200
            assert dl.headers["content-type"] == expected_mime
            assert dl.content.startswith(expected_magic)

    def test_curriculum_api_exposes_enriched_gurudocdb_fields(self):
        """Verifies curriculum endpoints expose id_mapel_bskap, durasi_1_jp_menit, buku_rujukan_sibi, and elemen_cp."""
        resp = client.get("/api/v1/curriculum/subjects?jenjang=SMP&kelas=7")
        assert resp.status_code == 200
        ipa = next(s for s in resp.json()["data"] if s["id"] == "SMP-K7-IPA")
        assert ipa["id_mapel_bskap"] == "MAPEL-15"
        assert ipa["durasi_1_jp_menit"] == 40

        resp_ch = client.get("/api/v1/curriculum/subjects/SMP-K7-IPA/chapters?semester=1")
        assert resp_ch.status_code == 200
        ch1 = resp_ch.json()["data"][0]
        assert "elemen_cp" in ch1 and len(ch1["elemen_cp"]) > 0
        assert "estimasi_pertemuan" in ch1 and ch1["estimasi_pertemuan"] > 0
