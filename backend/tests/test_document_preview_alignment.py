import io
import pytest
from docx import Document
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.generation import CustomDocumentOverrides, CustomTpItem

client = TestClient(app)


class TestDocumentPreviewAlignment:
    """TDD Suite ensuring 100% precision between Live Document Paper Preview and Downloaded Documents."""

    def test_custom_overrides_schema_accepts_both_naming_conventions(self):
        data = {
            "tujuan_pembelajaran_custom": [
                {"code": "TP.11.1.99", "deskripsi": "Kustom TP dari frontend.", "alokasi_jp": 10}
            ],
            "alokasi_jp_bab": 20,
            "kesiapan_murid": "Kesiapan murid kustom",
            "langkah_inti_memahami": ["Langkah memahami kustom"],
        }
        ov = CustomDocumentOverrides(**data)
        assert ov.custom_tps is not None
        assert len(ov.custom_tps) == 1
        assert ov.custom_tps[0].code == "TP.11.1.99"
        assert ov.custom_alokasi_jp == 20
        assert ov.tujuan_pembelajaran_custom is not None
        assert ov.alokasi_jp_bab == 20

    def test_docx_modul_ajar_matches_preview_structure(self):
        # Fetch actual chapter id for SMA-K11-INF Bab 1
        ch_resp = client.get("/api/v1/curriculum/subjects/SMA-K11-INF/chapters?semester=1")
        assert ch_resp.status_code == 200
        first_ch = ch_resp.json()["data"][0]
        chapter_id = first_ch["id"]

        payload = {
            "service_id": "08_modul_ajar",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "chapter_id": chapter_id,
            "paper_size": "F4",
            "output_format": "docx",
            "teacher_profile": {
                "nama_guru": "Siti Aminah, S.Pd.",
                "nip_guru": "198805122014022003",
                "nama_sekolah": "SMA Negeri 1 Surabaya",
                "kabupaten_kota": "Kota Surabaya",
                "provinsi": "Jawa Timur",
                "nama_kepala_sekolah": "Drs. H. Bambang Irawan, M.Pd.",
                "nip_kepala_sekolah": "196904151995121002",
                "no_whatsapp": "081234567890",
                "ukuran_kertas_default": "F4",
            },
            "include_lkpd": True,
            "include_asesmen": True,
            "include_rubrik": True,
            "custom_overrides": {
                "tujuan_pembelajaran_custom": [
                    {"code": "TP.11.1.KUSTOM", "deskripsi": "Menganalisis algoritma rekursif secara mendalam.", "alokasi_jp": 8}
                ],
                "alokasi_jp_bab": 16,
                "soal_asesmen_awal": ["Sebutkan pengertian algoritma rekursif kustom!"],
                "soal_asesmen_proses": ["Analisis kompleksitas waktu dari fungsi faktorial kustom!"],
                "soal_asesmen_akhir": ["Buatlah program rekursif menara Hanoi kustom!"],
            },
        }

        resp = client.post("/api/v1/documents/generate", json=payload)
        print("DEBUG RESP:", resp.status_code, resp.text)
        assert resp.status_code in (200, 201)
        dl_url = resp.json()["data"]["download_url"]

        file_resp = client.get(dl_url)
        assert file_resp.status_code == 200
        doc = Document(io.BytesIO(file_resp.content))

        all_text = "\n".join(p.text for p in doc.paragraphs)
        all_table_text = "\n".join(
            " | ".join(cell.text.strip() for cell in row.cells)
            for t in doc.tables
            for row in t.rows
        )
        combined = all_text + "\n" + all_table_text

        # 1. Custom TP & JP rendered in table
        assert "TP.11.1.KUSTOM" in combined
        assert "Menganalisis algoritma rekursif secara mendalam" in combined
        assert "16 JP" in combined or "16 Jam Pelajaran" in combined or "16 x" in combined

        # 2. Desain Pembelajaran table structure (must be structured table with A-E)
        assert "A. Capaian Pembelajaran" in combined or "A. Capaian Pembelajaran (CP)" in combined
        assert "Lintas Disiplin Ilmu" in combined or "LINTAS DISIPLIN ILMU" in combined
        assert "C. Tujuan Pembelajaran" in combined
        assert "Topik Pembelajaran Kontekstual" in combined or "TOPIK PEMBELAJARAN KONTEKSTUAL" in combined
        assert "E. Kerangka Pembelajaran" in combined

        # 3. Langkah-Langkah Pembelajaran Berdiferensiasi 3M table
        assert "Kegiatan Pendahuluan (15%)" in combined
        assert "Kegiatan Inti — Memahami, Mengaplikasi, Merefleksi (70%)" in combined or "Kegiatan Inti" in combined
        assert "Kegiatan Penutup (15%)" in combined

        # 4. Asesmen table with custom questions
        assert "Sebutkan pengertian algoritma rekursif kustom!" in combined
        assert "Analisis kompleksitas waktu dari fungsi faktorial kustom!" in combined
        assert "Buatlah program rekursif menara Hanoi kustom!" in combined

    def test_docx_prota_matches_preview_structure(self):
        payload = {
            "service_id": "05_prota",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "paper_size": "F4",
            "output_format": "docx",
            "teacher_profile": {
                "nama_guru": "Siti Aminah, S.Pd.",
                "nip_guru": "198805122014022003",
                "nama_sekolah": "SMA Negeri 1 Surabaya",
                "kabupaten_kota": "Kota Surabaya",
                "provinsi": "Jawa Timur",
                "nama_kepala_sekolah": "Drs. H. Bambang Irawan, M.Pd.",
                "nip_kepala_sekolah": "196904151995121002",
                "no_whatsapp": "081234567890",
                "ukuran_kertas_default": "F4",
            },
            "include_lkpd": False,
            "include_asesmen": False,
            "include_rubrik": False,
            "custom_overrides": {
                "cadangan_jp": 10,
            },
        }

        resp = client.post("/api/v1/documents/generate", json=payload)
        print("DEBUG RESP:", resp.status_code, resp.text)
        assert resp.status_code in (200, 201)
        dl_url = resp.json()["data"]["download_url"]

        file_resp = client.get(dl_url)
        assert file_resp.status_code == 200
        doc = Document(io.BytesIO(file_resp.content))

        all_table_text = "\n".join(
            " | ".join(cell.text.strip() for cell in row.cells)
            for t in doc.tables
            for row in t.rows
        )

        # Prota table headers matching preview
        assert "SEMESTER" in all_table_text
        assert "MATERI POKOK" in all_table_text
        assert "ALOKASI (JP)" in all_table_text
        assert "KETERANGAN" in all_table_text
        assert "Cadangan Jam Pelajaran" in all_table_text
        assert "10 JP" in all_table_text
        assert "Jumlah Jam Pelajaran" in all_table_text

    def test_cp_tp_section_5_table_structure_matches_preview(self):
        ch_resp = client.get("/api/v1/curriculum/subjects/SMA-K11-INF/chapters?semester=1")
        assert ch_resp.status_code == 200
        chapter_id = ch_resp.json()["data"][0]["id"]

        payload = {
            "service_id": "03_cp_tp",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "chapter_id": chapter_id,
            "paper_size": "F4",
            "output_format": "docx",
            "teacher_profile": {
                "nama_guru": "Siti Aminah, S.Pd.",
                "nip_guru": "198805122014022003",
                "nama_sekolah": "SMA Negeri 1 Surabaya",
                "kabupaten_kota": "Kota Surabaya",
                "provinsi": "Jawa Timur",
                "nama_kepala_sekolah": "Drs. H. Bambang Irawan, M.Pd.",
                "nip_kepala_sekolah": "196904151995121002",
                "no_whatsapp": "081234567890",
                "ukuran_kertas_default": "F4",
            },
            "include_lkpd": False,
            "include_asesmen": False,
            "include_rubrik": False,
            "custom_overrides": {
                "tujuan_pembelajaran_custom": [
                    {"code": "TP.11.1.CPTP", "deskripsi": "TP Khusus CP-TP Kustom.", "alokasi_jp": 6}
                ],
                "alokasi_jp_bab": 18,
            },
        }

        resp = client.post("/api/v1/documents/generate", json=payload)
        print("DEBUG RESP:", resp.status_code, resp.text)
        assert resp.status_code in (200, 201)
        dl_url = resp.json()["data"]["download_url"]

        file_resp = client.get(dl_url)
        assert file_resp.status_code == 200
        doc = Document(io.BytesIO(file_resp.content))

        all_table_text = "\n".join(
            " | ".join(cell.text.strip() for cell in row.cells)
            for t in doc.tables
            for row in t.rows
        )

        assert "KATEGORI" in all_table_text
        assert "RUMUSAN" in all_table_text
        assert "Elemen" in all_table_text
        assert "Kalimat CP" in all_table_text
        assert "Tujuan Pembelajaran" in all_table_text
        assert "TP.11.1.CPTP" in all_table_text
        assert "TP Khusus CP-TP Kustom." in all_table_text
        assert "Alokasi Waktu" in all_table_text
        assert "18 Jam Pelajaran (JP)" in all_table_text or "18 JP" in all_table_text

    def test_docx_atp_matches_preview_structure(self):
        ch_resp = client.get("/api/v1/curriculum/subjects/SMA-K11-INF/chapters?semester=1")
        assert ch_resp.status_code == 200
        chapter_id = ch_resp.json()["data"][0]["id"]

        payload = {
            "service_id": "04_atp",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "chapter_id": chapter_id,
            "paper_size": "F4",
            "output_format": "docx",
            "teacher_profile": {
                "nama_guru": "Siti Aminah, S.Pd.",
                "nip_guru": "198805122014022003",
                "nama_sekolah": "SMA Negeri 1 Surabaya",
                "kabupaten_kota": "Kota Surabaya",
                "provinsi": "Jawa Timur",
                "nama_kepala_sekolah": "Drs. H. Bambang Irawan, M.Pd.",
                "nip_kepala_sekolah": "196904151995121002",
                "no_whatsapp": "081234567890",
                "ukuran_kertas_default": "F4",
            },
            "include_lkpd": False,
            "include_asesmen": False,
            "include_rubrik": False,
            "custom_overrides": {
                "tujuan_pembelajaran_custom": [
                    {"code": "TP.11.1.ATP99", "deskripsi": "TP Khusus ATP Kustom.", "alokasi_jp": 12}
                ],
                "alokasi_jp_bab": 24,
            },
        }

        resp = client.post("/api/v1/documents/generate", json=payload)
        assert resp.status_code in (200, 201)
        dl_url = resp.json()["data"]["download_url"]

        file_resp = client.get(dl_url)
        assert file_resp.status_code == 200
        doc = Document(io.BytesIO(file_resp.content))

        all_table_text = "\n".join(
            " | ".join(cell.text.strip() for cell in row.cells)
            for t in doc.tables
            for row in t.rows
        )

        assert "CAPAIAN PEMBELAJARAN FASE" in all_table_text or "Capaian Pembelajaran" in all_table_text
        assert "TP.11.1.ATP99" in all_table_text
        assert "TP Khusus ATP Kustom." in all_table_text
        assert "24 JP" in all_table_text
        assert "Kata Kunci" in all_table_text
        assert "Glosarium" in all_table_text

    def test_docx_promes_matches_preview_structure(self):
        ch_resp = client.get("/api/v1/curriculum/subjects/SMA-K11-INF/chapters?semester=1")
        assert ch_resp.status_code == 200
        chapter_id = ch_resp.json()["data"][0]["id"]

        payload = {
            "service_id": "06_promes",
            "jenjang": "SMA",
            "kelas": 11,
            "subject_id": "SMA-K11-INF",
            "semester": 1,
            "chapter_id": chapter_id,
            "paper_size": "F4",
            "output_format": "docx",
            "teacher_profile": {
                "nama_guru": "Siti Aminah, S.Pd.",
                "nip_guru": "198805122014022003",
                "nama_sekolah": "SMA Negeri 1 Surabaya",
                "kabupaten_kota": "Kota Surabaya",
                "provinsi": "Jawa Timur",
                "nama_kepala_sekolah": "Drs. H. Bambang Irawan, M.Pd.",
                "nip_kepala_sekolah": "196904151995121002",
                "no_whatsapp": "081234567890",
                "ukuran_kertas_default": "F4",
            },
            "include_lkpd": False,
            "include_asesmen": False,
            "include_rubrik": False,
            "custom_overrides": {
                "tujuan_pembelajaran_custom": [
                    {"code": "TP.11.1.PROMES99", "deskripsi": "TP Khusus Promes Kustom.", "alokasi_jp": 4}
                ],
                "alokasi_jp_bab": 16,
            },
        }

        resp = client.post("/api/v1/documents/generate", json=payload)
        assert resp.status_code in (200, 201)
        dl_url = resp.json()["data"]["download_url"]

        file_resp = client.get(dl_url)
        assert file_resp.status_code == 200
        doc = Document(io.BytesIO(file_resp.content))

        all_table_text = "\n".join(
            " | ".join(cell.text.strip() for cell in row.cells)
            for t in doc.tables
            for row in t.rows
        )

        assert "MATRIKS DISTRIBUSI MINGGU EFEKTIF" in "\n".join(p.text for p in doc.paragraphs) or "MATRIKS DISTRIBUSI MINGGU EFEKTIF" in all_table_text
        assert "TP.11.1.PROMES99" in all_table_text
        assert "TP Khusus Promes Kustom." in all_table_text
        assert "Intrakurikuler" in all_table_text
        assert "TM" in all_table_text

    def test_xlsx_and_pdf_engines_support_custom_overrides(self):
        ch_resp = client.get("/api/v1/curriculum/subjects/SMA-K11-INF/chapters?semester=1")
        assert ch_resp.status_code == 200
        chapter_id = ch_resp.json()["data"][0]["id"]

        for fmt in ("xlsx", "pdf"):
            payload = {
                "service_id": "08_modul_ajar",
                "jenjang": "SMA",
                "kelas": 11,
                "subject_id": "SMA-K11-INF",
                "semester": 1,
                "chapter_id": chapter_id,
                "paper_size": "F4",
                "output_format": fmt,
                "teacher_profile": {
                    "nama_guru": "Siti Aminah, S.Pd.",
                    "nip_guru": "198805122014022003",
                    "nama_sekolah": "SMA Negeri 1 Surabaya",
                    "kabupaten_kota": "Kota Surabaya",
                    "provinsi": "Jawa Timur",
                    "nama_kepala_sekolah": "Drs. H. Bambang Irawan, M.Pd.",
                    "nip_kepala_sekolah": "196904151995121002",
                    "no_whatsapp": "081234567890",
                    "ukuran_kertas_default": "F4",
                },
                "include_lkpd": True,
                "include_asesmen": True,
                "include_rubrik": True,
                "custom_overrides": {
                    "tujuan_pembelajaran_custom": [
                        {"code": f"TP.11.1.{fmt.upper()}", "deskripsi": f"TP format {fmt.upper()}.", "alokasi_jp": 8}
                    ],
                    "alokasi_jp_bab": 16,
                },
            }

            resp = client.post("/api/v1/documents/generate", json=payload)
            assert resp.status_code in (200, 201)
            dl_url = resp.json()["data"]["download_url"]
            file_resp = client.get(dl_url)
            assert file_resp.status_code == 200
            assert len(file_resp.content) > 1000

    def test_docx_tables_have_explicit_borders_padding_and_widths(self):
        """TDD RED->GREEN: Every content table in .docx must have XML borders, cell padding, and autofit=False."""
        from docx.oxml.ns import qn

        ch_resp = client.get("/api/v1/curriculum/subjects/SMA-K11-INF/chapters?semester=1")
        assert ch_resp.status_code == 200
        chapter_id = ch_resp.json()["data"][0]["id"]

        for svc in ("03_cp_tp", "04_atp", "05_prota", "06_promes", "08_modul_ajar"):
            payload = {
                "service_id": svc,
                "jenjang": "SMA",
                "kelas": 11,
                "subject_id": "SMA-K11-INF",
                "semester": 1,
                "chapter_id": chapter_id,
                "paper_size": "F4",
                "output_format": "docx",
                "teacher_profile": {
                    "nama_guru": "Siti Aminah, S.Pd.",
                    "nip_guru": "198805122014022003",
                    "nama_sekolah": "SMA Negeri 1 Surabaya",
                    "kabupaten_kota": "Kota Surabaya",
                    "provinsi": "Jawa Timur",
                    "nama_kepala_sekolah": "Drs. H. Bambang Irawan, M.Pd.",
                    "nip_kepala_sekolah": "196904151995121002",
                    "no_whatsapp": "081234567890",
                    "ukuran_kertas_default": "F4",
                },
                "include_lkpd": True,
                "include_asesmen": True,
                "include_rubrik": True,
            }
            resp = client.post("/api/v1/documents/generate", json=payload)
            assert resp.status_code in (200, 201), f"Failed for {svc}: {resp.text}"
            file_resp = client.get(resp.json()["data"]["download_url"])
            assert file_resp.status_code == 200

            doc = Document(io.BytesIO(file_resp.content))
            assert len(doc.tables) >= 2, f"Expected >=2 tables for {svc}"

            content_tables = doc.tables[:-1]  # Exclude Lembar Pengesahan
            for idx, tbl in enumerate(content_tables):
                assert tbl.autofit is False, f"{svc} table #{idx} must have autofit=False"
                tbl_pr = tbl._tbl.tblPr
                borders = tbl_pr.find(qn("w:tblBorders"))
                assert borders is not None, f"{svc} table #{idx} missing <w:tblBorders>"
                for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
                    el = borders.find(qn(f"w:{side}"))
                    assert el is not None, f"{svc} table #{idx} missing border side {side}"
                    assert el.get(qn("w:val")) == "single"

                # Check first cell has <w:tcMar> padding
                first_cell_tcpr = tbl.rows[0].cells[0]._tc.tcPr
                assert first_cell_tcpr is not None and first_cell_tcpr.find(qn("w:tcMar")) is not None, (
                    f"{svc} table #{idx} missing cell padding <w:tcMar>"
                )

            # Signature table (Lembar Pengesahan) must stay borderless
            sig_tbl_pr = doc.tables[-1]._tbl.tblPr
            sig_borders = sig_tbl_pr.find(qn("w:tblBorders"))
            if sig_borders is not None:
                for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
                    el = sig_borders.find(qn(f"w:{side}"))
                    if el is not None:
                        assert el.get(qn("w:val")) in ("none", "nil")
