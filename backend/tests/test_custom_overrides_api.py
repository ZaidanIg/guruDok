import io
import pytest
from docx import Document

from app.models.teacher import TeacherProfile
from app.repositories.postgres_curriculum_repo import PostgresCurriculumRepository
from app.schemas.generation import (
    CustomDocumentOverrides,
    CustomRubrikDplItem,
    DocumentGenerateRequest,
    ServiceIdEnum,
    PaperSizeEnum,
    OutputFormatEnum,
    TeacherProfileCreate,
)
from app.services.document_engine.docx_engine import DocxDocumentEngine
from app.services.document_engine.pdf_engine import PdfDocumentEngine


class TestCustomOverridesModulAjar:
    @pytest.fixture
    def sample_teacher(self) -> TeacherProfile:
        return TeacherProfile(
            nama_guru="Siti Rahmawati, S.Pd.",
            nip_guru="198503152010012015",
            nama_sekolah="SD Negeri Percobaan 1",
            kabupaten_kota="Kota Bandung",
            provinsi="Jawa Barat",
            nama_kepala_sekolah="Drs. H. Ahmad Sanusi, M.M.",
            nip_kepala_sekolah="197001011995031002",
            no_whatsapp="+6281234567890",
        )

    def test_custom_overrides_sanitization_and_deserialization(self):
        """Verifies Pydantic schema deserializes new LKPD & Rubrik 8 DPL fields and rejects/sanitizes XSS injection."""
        from app.core.exceptions import SecurityViolationError

        # 1. Script injection must raise SecurityViolationError
        with pytest.raises(SecurityViolationError):
            CustomDocumentOverrides(judul_lkpd="LKPD <script>alert('xss')</script>")

        # 2. Clean input with HTML tags must be sanitized and deserialized
        clean_input = {
            "judul_lkpd": "LKPD Eksplorasi Kalimat <b>Penting</b>",
            "tujuan_lkpd": "Siswa mampu memahami pola kalimat SPOK secara aktif.",
            "petunjuk_lkpd": "1. Berdoalah. 2. Kerjakan tugas.",
            "tugas_lkpd_memahami": "Identifikasi subjek dan predikat.",
            "tugas_lkpd_mengaplikasi": "Buat 3 kalimat kontekstual di lingkungan sekolah.",
            "tugas_lkpd_merefleksi": "Tuliskan apa yang kamu pelajari hari ini.",
            "soal_asesmen_awal": ["Sebutkan huruf vokal!", "Apa itu kata?"],
            "soal_asesmen_proses": ["Kerjakan lembar pengamatan kelompok."],
            "soal_asesmen_akhir": ["Buat kalimat lengkap dengan struktur SPOK."],
            "custom_rubrik_dpl": [
                {
                    "no": 1,
                    "nama_dimensi": "Keimanan & Ketakwaan Tuhan YME",
                    "indikator": "Berdoa dengan khusyuk sebelum mulai.",
                    "is_active": True,
                },
                {
                    "no": 2,
                    "nama_dimensi": "Penalaran Kritis",
                    "indikator": "Menganalisis kalimat rancu dengan mandiri.",
                    "is_active": True,
                },
            ],
        }

        overrides = CustomDocumentOverrides(**clean_input)
        assert "<b>" not in overrides.judul_lkpd
        assert "LKPD Eksplorasi Kalimat Penting" in overrides.judul_lkpd
        assert overrides.tujuan_lkpd == "Siswa mampu memahami pola kalimat SPOK secara aktif."
        assert len(overrides.soal_asesmen_awal) == 2
        assert len(overrides.custom_rubrik_dpl) == 2
        assert overrides.custom_rubrik_dpl[0].is_active is True

    def test_modul_ajar_docx_renders_custom_lkpd_and_empty_checklist_rubrik(self, sample_teacher: TeacherProfile):
        """Verifies DocxDocumentEngine renders custom LKPD fields and empty checklist boxes [  ] for MB, B, BSH, SB."""
        pg_repo = PostgresCurriculumRepository()
        subject = pg_repo.get_subject_by_id("SD-K1-BINDO")
        assert subject is not None
        chapter = pg_repo.get_chapter("SD-K1-BINDO", "BINDO-K1-B01")
        assert chapter is not None

        custom_overrides = CustomDocumentOverrides(
            judul_lkpd="LKPD KUSTOM: Penyelidikan Huruf Vokal dan Konsonan",
            tujuan_lkpd="Peserta didik mampu membedakan bunyi huruf vokal dan konsonan secara tepat.",
            petunjuk_lkpd="Diskusikan bersama rekan sebangku dan tuliskan jawaban pada tempat yang tersedia.",
            tugas_lkpd_memahami="Sebutkan 5 huruf vokal dan contoh kata yang diawali huruf tersebut!",
            tugas_lkpd_mengaplikasi="Kelompokkan kartu kata yang diberikan ke dalam kotak vokal atau konsonan!",
            tugas_lkpd_merefleksi="Bagaimana perasaanmu setelah berhasil menyusun kata dengan tepat?",
            soal_asesmen_awal=["Apakah kamu bisa membaca huruf A sampai Z secara urut?"],
            soal_asesmen_proses=["Observasi keaktifan siswa saat menyusun kartu suku kata."],
            soal_asesmen_akhir=["Tes lisan: Membaca 3 kata sederhana berpola KV-KV."],
            custom_rubrik_dpl=[
                CustomRubrikDplItem(
                    no=1,
                    nama_dimensi="Keimanan & Ketakwaan terhadap Tuhan YME",
                    indikator="Berdoa sebelum dan sesudah belajar dengan tertib.",
                    is_active=True,
                ),
                CustomRubrikDplItem(
                    no=3,
                    nama_dimensi="Penalaran Kritis",
                    indikator="Mampu membedakan pasangan huruf yang mirip (b dan d).",
                    is_active=True,
                ),
            ],
        )

        req = DocumentGenerateRequest(
            service_id=ServiceIdEnum.MODUL_AJAR,
            jenjang="SD",
            kelas=1,
            subject_id="SD-K1-BINDO",
            semester=1,
            chapter_id="BINDO-K1-B01",
            paper_size=PaperSizeEnum.F4,
            output_format=OutputFormatEnum.DOCX,
            teacher_profile=TeacherProfileCreate(
                nama_guru=sample_teacher.nama_guru,
                nip_guru=sample_teacher.nip_guru,
                nama_sekolah=sample_teacher.nama_sekolah,
                kabupaten_kota=sample_teacher.kabupaten_kota,
                provinsi=sample_teacher.provinsi,
                nama_kepala_sekolah=sample_teacher.nama_kepala_sekolah,
                nip_kepala_sekolah=sample_teacher.nip_kepala_sekolah,
                no_whatsapp=sample_teacher.no_whatsapp,
            ),
            include_lkpd=True,
            include_asesmen=True,
            include_rubrik=True,
            custom_overrides=custom_overrides,
        )

        engine = DocxDocumentEngine()
        docx_bytes = engine.generate(req, subject, chapter, sample_teacher)
        doc = Document(io.BytesIO(docx_bytes))
        full_text = "\n".join([p.text for p in doc.paragraphs])
        for tbl in doc.tables:
            for row in tbl.rows:
                for cell in row.cells:
                    full_text += "\n" + cell.text

        # Verify Custom LKPD is rendered
        assert "LKPD KUSTOM: Penyelidikan Huruf Vokal dan Konsonan" in full_text
        assert "Peserta didik mampu membedakan bunyi huruf vokal dan konsonan secara tepat." in full_text
        assert "Sebutkan 5 huruf vokal dan contoh kata yang diawali huruf tersebut!" in full_text
        assert "Kelompokkan kartu kata yang diberikan ke dalam kotak vokal atau konsonan!" in full_text
        assert "Bagaimana perasaanmu setelah berhasil menyusun kata dengan tepat?" in full_text

        # Verify Custom Asesmen is rendered
        assert "Apakah kamu bisa membaca huruf A sampai Z secara urut?" in full_text
        assert "Observasi keaktifan siswa saat menyusun kartu suku kata." in full_text
        assert "Tes lisan: Membaca 3 kata sederhana berpola KV-KV." in full_text

        # Verify Custom Rubrik 8 DPL with blank checklist boxes [  ]
        assert "Mampu membedakan pasangan huruf yang mirip (b dan d)." in full_text
        assert "[  ]" in full_text

    def test_modul_ajar_pdf_renders_custom_lkpd_and_empty_checklist_rubrik(self, sample_teacher: TeacherProfile):
        """Verifies PdfDocumentEngine renders custom LKPD fields and 7-column Rubrik table with empty check cells."""
        pg_repo = PostgresCurriculumRepository()
        subject = pg_repo.get_subject_by_id("SD-K1-BINDO")
        chapter = pg_repo.get_chapter("SD-K1-BINDO", "BINDO-K1-B01")

        custom_overrides = CustomDocumentOverrides(
            judul_lkpd="LKPD PDF KUSTOM: Eksplorasi Suku Kata",
            tujuan_lkpd="Siswa dapat merangkai suku kata menjadi kata bermakna.",
            tugas_lkpd_memahami="Identifikasi suku kata pada kata 'BOLA'.",
            tugas_lkpd_mengaplikasi="Pasangkan kartu suku kata menjadi nama benda.",
            tugas_lkpd_merefleksi="Refleksi pembelajaran suku kata hari ini.",
            soal_asesmen_awal=["Tes awal PDF kata."],
            custom_rubrik_dpl=[
                CustomRubrikDplItem(
                    no=3,
                    nama_dimensi="Penalaran Kritis",
                    indikator="Menghubungkan lambang bunyi huruf secara logis.",
                    is_active=True,
                )
            ],
        )

        req = DocumentGenerateRequest(
            service_id=ServiceIdEnum.MODUL_AJAR,
            jenjang="SD",
            kelas=1,
            subject_id="SD-K1-BINDO",
            semester=1,
            chapter_id="BINDO-K1-B01",
            paper_size=PaperSizeEnum.F4,
            output_format=OutputFormatEnum.PDF,
            teacher_profile=TeacherProfileCreate(
                nama_guru=sample_teacher.nama_guru,
                nip_guru=sample_teacher.nip_guru,
                nama_sekolah=sample_teacher.nama_sekolah,
                kabupaten_kota=sample_teacher.kabupaten_kota,
                provinsi=sample_teacher.provinsi,
                nama_kepala_sekolah=sample_teacher.nama_kepala_sekolah,
                nip_kepala_sekolah=sample_teacher.nip_kepala_sekolah,
                no_whatsapp=sample_teacher.no_whatsapp,
            ),
            include_lkpd=True,
            include_asesmen=True,
            include_rubrik=True,
            custom_overrides=custom_overrides,
        )

        import re
        import zlib
        engine = PdfDocumentEngine()
        pdf_bytes = engine.generate(req, subject, chapter, sample_teacher)
        assert pdf_bytes.startswith(b"%PDF-")
        assert len(pdf_bytes) > 3000

        decompressed = b""
        for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", pdf_bytes, re.DOTALL):
            try:
                decompressed += zlib.decompress(m.group(1))
            except Exception:
                pass

        assert b"LKPD" in decompressed
        assert b"Eksplorasi Suku Kata" in decompressed
        assert b"Penalaran Kritis" in decompressed
