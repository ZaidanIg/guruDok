import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCustomChapterApi:
    """TDD Suite for Custom User-Defined Chapter Creation and Persistence."""

    def test_create_custom_chapter_api_success(self):
        subject_id = "SMA-K11-INF"
        payload = {
            "nomor_bab": 7,
            "semester": 2,
            "judul_bab": "Kecerdasan Buatan dan Etika Digital Terapan",
            "elemen_cp": "Dampak Sosial Informatika (DSI)",
            "alokasi_jp": 18,
            "model_pembelajaran": "Problem Based Learning (PBL)",
            "daftar_tp": [
                {
                    "code": "TP.11.7.1",
                    "deskripsi": "Memahami konsep dasar kecerdasan buatan dan implikasi etisnya bagi masyarakat.",
                    "alokasi_jp": 6,
                },
                {
                    "code": "TP.11.7.2",
                    "deskripsi": "Menganalisis studi kasus pemanfaatan AI generatif secara kritis dan bertanggung jawab.",
                    "alokasi_jp": 12,
                },
            ],
        }

        response = client.post(f"/api/v1/curriculum/subjects/{subject_id}/chapters", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        body = response.json()
        assert body["success"] is True
        data = body["data"]

        assert data["nomor_bab"] == 7
        assert data["semester"] == 2
        assert "Kecerdasan Buatan" in data["judul_bab"]
        assert data["alokasi_jp"] == 18
        assert len(data["tujuan_pembelajaran"]) == 2
        assert data["tujuan_pembelajaran"][0]["code"] == "TP.11.7.1"
        assert "modul_ajar_template" in data

    def test_create_custom_chapter_security_sanitization(self):
        subject_id = "SMA-K11-INF"
        # 1. Script injection must be strictly rejected with HTTP 400
        malicious_payload = {
            "nomor_bab": 8,
            "semester": 2,
            "judul_bab": "Keamanan Siber & Pentesting <script>alert('XSS')</script>",
            "elemen_cp": "Jaringan Komputer dan Internet",
            "alokasi_jp": 12,
        }
        response = client.post(f"/api/v1/curriculum/subjects/{subject_id}/chapters", json=malicious_payload)
        assert response.status_code == 400, "XSS script tags must trigger 400 Bad Request"

        # 2. Benign formatting tags must be safely stripped
        benign_payload = {
            "nomor_bab": 8,
            "semester": 2,
            "judul_bab": "Keamanan Siber & Pentesting <b>Terapan</b>",
            "elemen_cp": "Jaringan Komputer dan Internet <i>(JKI)</i>",
            "alokasi_jp": 12,
            "daftar_tp": [
                {
                    "code": "TP.11.8.1",
                    "deskripsi": "Memahami prinsip keamanan data <u>esensial</u>.",
                    "alokasi_jp": 12,
                }
            ],
        }
        res_benign = client.post(f"/api/v1/curriculum/subjects/{subject_id}/chapters", json=benign_payload)
        assert res_benign.status_code == 200
        data = res_benign.json()["data"]
        assert "<b>" not in data["judul_bab"]
        assert "Terapan" in data["judul_bab"]

    def test_custom_chapter_persisted_in_database_and_queried(self):
        subject_id = "SMA-K11-INF"
        response = client.get(f"/api/v1/curriculum/subjects/{subject_id}/chapters?semester=2")
        assert response.status_code == 200
        chapters = response.json()["data"]
        chapter_titles = [c["judul_bab"] for c in chapters]
        assert any("Kecerdasan Buatan" in t for t in chapter_titles)

    def test_custom_chapter_generates_documents(self):
        # Retrieve the newly created chapter ID
        resp = client.get("/api/v1/curriculum/subjects/SMA-K11-INF/chapters?semester=2")
        chapters = resp.json()["data"]
        custom_ch = next((c for c in chapters if "Kecerdasan Buatan" in c["judul_bab"]), None)
        assert custom_ch is not None, "Custom chapter must exist in database"

        generate_payload = {
            "service_id": "08_modul_ajar",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 2,
            "chapter_id": custom_ch["id"],
            "paper_size": "F4",
            "output_format": "docx",
            "teacher_profile": {
                "nama_guru": "Drs. Eko Prasetyo, M.Kom.",
                "nip_guru": "197508102000031004",
                "nama_sekolah": "SMA Negeri 1 Surabaya",
                "kabupaten_kota": "Kota Surabaya",
                "provinsi": "Jawa Timur",
                "nama_kepala_sekolah": "Dra. Hj. Nurul Hidayati, M.Pd.",
                "nip_kepala_sekolah": "196805121994122001",
                "no_whatsapp": "081234567890",
                "ukuran_kertas_default": "F4",
            },
            "include_lkpd": True,
            "include_asesmen": True,
            "include_rubrik": True,
        }

        gen_resp = client.post("/api/v1/documents/generate", json=generate_payload)
        assert gen_resp.status_code in (200, 201)
        body = gen_resp.json()
        assert body["success"] is True
        assert "download_url" in body["data"]
