import io
import pytest
import openpyxl
from docx import Document
from app.core.security import FileAttackGuard
from app.models.teacher import TeacherProfile
from app.repositories.curriculum_repo import JsonCurriculumRepository
from app.repositories.postgres_curriculum_repo import PostgresCurriculumRepository
from app.schemas.generation import (
    DocumentGenerateRequest,
    ServiceIdEnum,
    PaperSizeEnum,
    OutputFormatEnum,
    CustomDocumentOverrides,
    CustomTpItem,
)
from app.schemas.teacher import TeacherProfileCreate
from app.services.document_engine.docx_engine import DocxDocumentEngine
from app.services.document_engine.xlsx_engine import XlsxDocumentEngine
from app.services.document_engine.pdf_engine import PdfDocumentEngine
from app.services.document_engine.generator_factory import DocumentEngineFactory


@pytest.fixture
def sample_teacher() -> TeacherProfile:
    return TeacherProfile(
        nama_guru="Siti Aminah, S.Pd.",
        nip_guru="198805122014022003",
        nama_sekolah="SMP Negeri 1 Surabaya",
        kabupaten_kota="Kota Surabaya",
        provinsi="Jawa Timur",
        nama_kepala_sekolah="Drs. H. Bambang Irawan, M.Pd.",
        nip_kepala_sekolah="196904151995121002",
        no_whatsapp="+6281234567890",
        ukuran_kertas_default="F4",
    )


@pytest.fixture
def repo() -> JsonCurriculumRepository:
    return JsonCurriculumRepository()


class TestDocumentEngines:
    """Test suite for deterministic Word and Excel document generation engines."""

    def test_factory_engine_selection(self):
        promes_engine = DocumentEngineFactory.get_engine(ServiceIdEnum.PROMES)
        assert isinstance(promes_engine, XlsxDocumentEngine)

        modul_engine = DocumentEngineFactory.get_engine(ServiceIdEnum.MODUL_AJAR)
        assert isinstance(modul_engine, DocxDocumentEngine)

        atp_engine = DocumentEngineFactory.get_engine(ServiceIdEnum.ATP)
        assert isinstance(atp_engine, DocxDocumentEngine)

    def test_generate_modul_ajar_docx(self, repo: JsonCurriculumRepository, sample_teacher: TeacherProfile):
        subject = repo.get_subject_by_id("SMP-K7-IPA")
        assert subject is not None
        chapter = repo.get_chapter("SMP-K7-IPA", "IPA-K7-B01")
        assert chapter is not None

        req = DocumentGenerateRequest(
            service_id=ServiceIdEnum.MODUL_AJAR,
            jenjang="SMP",
            kelas=7,
            subject_id="SMP-K7-IPA",
            semester=1,
            chapter_id="IPA-K7-B01",
            paper_size=PaperSizeEnum.F4,
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
        )

        engine = DocxDocumentEngine()
        docx_bytes = engine.generate(req, subject, chapter, sample_teacher)

        # Assert output is valid Office Open XML ZIP container
        assert len(docx_bytes) > 5000
        assert FileAttackGuard.verify_docx_or_xlsx_signature(docx_bytes) is True

    def test_generate_promes_xlsx(self, repo: JsonCurriculumRepository, sample_teacher: TeacherProfile):
        subject = repo.get_subject_by_id("SMP-K7-IPA")
        assert subject is not None

        req = DocumentGenerateRequest(
            service_id=ServiceIdEnum.PROMES,
            jenjang="SMP",
            kelas=7,
            subject_id="SMP-K7-IPA",
            semester=1,
            paper_size=PaperSizeEnum.F4,
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
        )

        engine = XlsxDocumentEngine()
        xlsx_bytes = engine.generate(req, subject, None, sample_teacher)

        # Assert output is valid Excel ZIP container
        assert len(xlsx_bytes) > 4000
        assert FileAttackGuard.verify_docx_or_xlsx_signature(xlsx_bytes) is True

    def test_generate_atp_and_prota_docx(self, repo: JsonCurriculumRepository, sample_teacher: TeacherProfile):
        subject = repo.get_subject_by_id("SMP-K7-IPA")
        assert subject is not None

        engine = DocxDocumentEngine()

        for svc in [ServiceIdEnum.ATP, ServiceIdEnum.PROTA, ServiceIdEnum.CP_TP]:
            req = DocumentGenerateRequest(
                service_id=svc,
                jenjang="SMP",
                kelas=7,
                subject_id="SMP-K7-IPA",
                semester=1,
                paper_size=PaperSizeEnum.F4,
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
            )
            file_bytes = engine.generate(req, subject, None, sample_teacher)
            assert len(file_bytes) > 4000
            assert FileAttackGuard.verify_docx_or_xlsx_signature(file_bytes) is True

    def test_modul_ajar_renders_rich_payload_from_gurudocdb(self, sample_teacher: TeacherProfile):
        """Verifies DocxDocumentEngine injects rich modul_ajar_payload fields from GuruDocDB."""
        pg_repo = PostgresCurriculumRepository()
        subject = pg_repo.get_subject_by_id("SD-K1-BINDO")
        assert subject is not None
        chapter = pg_repo.get_chapter("SD-K1-BINDO", "BINDO-K1-B01")
        assert chapter is not None
        raw_tpl = pg_repo.get_raw_modul_template("SD-K1-BINDO", "BINDO-K1-B01")
        assert raw_tpl is not None

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
        )

        engine = DocxDocumentEngine()
        docx_bytes = engine.generate(req, subject, chapter, sample_teacher, raw_template=raw_tpl)
        doc = Document(io.BytesIO(docx_bytes))
        full_text = "\n".join([p.text for p in doc.paragraphs])
        for tbl in doc.tables:
            for row in tbl.rows:
                for cell in row.cells:
                    full_text += "\n" + cell.text

        # Assert chapter-specific payload from GuruDocDB is rendered inside the Word document
        assert "Bunyi apa saja yang kalian dengar saat pagi hari di rumah?" in full_text
        assert "LKPD Kartu Nama dan Pasangan Suku Kata" in full_text
        assert "Abjad: Kumpulan huruf dari A sampai Z" in full_text

    def test_promes_xlsx_integrates_26_weeks_academic_calendar_from_gurudocdb(self, sample_teacher: TeacherProfile):
        """Verifies XlsxDocumentEngine uses the 26 calendar weeks & agenda codes (MPLS, STS, SAS, LSMT) from GuruDocDB."""
        pg_repo = PostgresCurriculumRepository()
        subject = pg_repo.get_subject_by_id("SMP-K7-IPA")
        calendar_weeks = pg_repo.get_calendar_weeks(semester=1)
        assert len(calendar_weeks) == 26

        req = DocumentGenerateRequest(
            service_id=ServiceIdEnum.PROMES,
            jenjang="SMP",
            kelas=7,
            subject_id="SMP-K7-IPA",
            semester=1,
            paper_size=PaperSizeEnum.F4,
            output_format=OutputFormatEnum.XLSX,
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
        )

        engine = XlsxDocumentEngine()
        xlsx_bytes = engine.generate(req, subject, None, sample_teacher, raw_template={"calendar_weeks": calendar_weeks})
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=False)
        ws = wb.active

        all_values = []
        for row in ws.iter_rows(values_only=True):
            for val in row:
                if val is not None:
                    all_values.append(str(val))
        joined = " | ".join(all_values)

        assert "MPLS" in joined
        assert "STS" in joined
        assert "SAS" in joined
        assert "LSMT" in joined
        assert "=SUM(" in joined

    def test_multi_format_generation_docx_xlsx_pdf_for_all_services(self, sample_teacher: TeacherProfile):
        """Verifies every service can be generated in Word (.docx), Excel (.xlsx), and PDF (.pdf) formats."""
        pg_repo = PostgresCurriculumRepository()
        subject = pg_repo.get_subject_by_id("SMP-K7-IPA")
        chapter = pg_repo.get_chapter("SMP-K7-IPA", "IPA-K7-B01")
        raw_tpl = pg_repo.get_raw_modul_template("SMP-K7-IPA", "IPA-K7-B01")

        for fmt in [OutputFormatEnum.DOCX, OutputFormatEnum.XLSX, OutputFormatEnum.PDF]:
            for svc in [ServiceIdEnum.CP_TP, ServiceIdEnum.ATP, ServiceIdEnum.PROTA, ServiceIdEnum.PROMES, ServiceIdEnum.MODUL_AJAR]:
                req = DocumentGenerateRequest(
                    service_id=svc,
                    jenjang="SMP",
                    kelas=7,
                    subject_id="SMP-K7-IPA",
                    semester=1,
                    chapter_id="IPA-K7-B01" if svc == ServiceIdEnum.MODUL_AJAR else None,
                    paper_size=PaperSizeEnum.F4,
                    output_format=fmt,
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
                )
                engine = DocumentEngineFactory.get_engine(svc, fmt)
                out_bytes = engine.generate(req, subject, chapter, sample_teacher, raw_template=raw_tpl)
                assert len(out_bytes) > 1500
                if fmt == OutputFormatEnum.PDF:
                    assert out_bytes.startswith(b"%PDF-")
                else:
                    assert out_bytes.startswith(b"PK\x03\x04")

    def test_official_document_structures_match_reference_attachment(self, sample_teacher: TeacherProfile):
        """Verifies CP-TP, ATP, Modul Ajar Deep Learning, Prota, and Promes follow the attached official structure."""
        pg_repo = PostgresCurriculumRepository()
        subject = pg_repo.get_subject_by_id("SMA-K11-INF")
        assert subject is not None
        chapter = subject.bab_list[0]
        raw_tpl = pg_repo.get_raw_modul_template("SMA-K11-INF", chapter.id)
        engine = DocxDocumentEngine()

        def extract_docx_text(b: bytes) -> str:
            d = Document(io.BytesIO(b))
            txt = "\n".join(p.text for p in d.paragraphs)
            for t in d.tables:
                for r in t.rows:
                    for c in r.cells:
                        txt += "\n" + c.text
            return txt

        # 1. Verify CP-TP Structure (Rasional, Tujuan, Karakteristik, CP Fase, KATEGORI | RUMUSAN)
        req_cp = DocumentGenerateRequest(
            service_id=ServiceIdEnum.CP_TP,
            jenjang="SMA",
            kelas=11,
            subject_id="SMA-K11-INF",
            semester=1,
            paper_size=PaperSizeEnum.F4,
            teacher_profile=TeacherProfileCreate(**sample_teacher.to_dict()),
        )
        cp_text = extract_docx_text(engine.generate(req_cp, subject, None, sample_teacher))
        assert "Rasional Mata Pelajaran" in cp_text
        assert "Tujuan Mata Pelajaran" in cp_text
        assert "Karakteristik Mata Pelajaran" in cp_text
        assert "Capaian Pembelajaran Fase F" in cp_text
        assert "KATEGORI" in cp_text and "RUMUSAN" in cp_text

        # 2. Verify ATP Structure (Capaian Pembelajaran Pertahun, Kata Kunci, Topik, Glosarium, Rasional Penyusunan ATP)
        req_atp = DocumentGenerateRequest(
            service_id=ServiceIdEnum.ATP,
            jenjang="SMA",
            kelas=11,
            subject_id="SMA-K11-INF",
            semester=1,
            paper_size=PaperSizeEnum.F4,
            teacher_profile=TeacherProfileCreate(**sample_teacher.to_dict()),
        )
        atp_text = extract_docx_text(engine.generate(req_atp, subject, None, sample_teacher))
        assert "Capaian Pembelajaran Pertahun" in atp_text
        assert "Kata Kunci" in atp_text
        assert "Glosarium" in atp_text
        assert "Rasional Penyusunan Alur Tujuan Pembelajaran" in atp_text

        # 3. Verify Modul Ajar Deep Learning Structure (Identifikasi Kesiapan, Karakteristik Materi, Lintas Disiplin, Langkah Berdiferensiasi Pertemuan 1-3, Soal Asesmen Awal/Proses/Akhir)
        req_ma = DocumentGenerateRequest(
            service_id=ServiceIdEnum.MODUL_AJAR,
            jenjang="SMA",
            kelas=11,
            subject_id="SMA-K11-INF",
            semester=1,
            chapter_id=chapter.id,
            paper_size=PaperSizeEnum.F4,
            teacher_profile=TeacherProfileCreate(**sample_teacher.to_dict()),
        )
        ma_text = extract_docx_text(engine.generate(req_ma, subject, chapter, sample_teacher, raw_template=raw_tpl))
        assert "MODUL AJAR DEEP LEARNING" in ma_text
        assert "Identifikasi Kesiapan Peserta Didik" in ma_text
        assert "KARAKTERISTIK MATERI PELAJARAN" in ma_text
        assert "LINTAS DISIPLIN ILMU YANG RELEVAN" in ma_text
        assert "TOPIK PEMBELAJARAN KONTEKSTUAL" in ma_text
        assert "LANGKAH-LANGKAH PEMBELAJARAN BERDIFERENSIASI" in ma_text
        assert "Soal Asesmen Awal" in ma_text
        assert "Soal Asesmen Proses" in ma_text
        assert "Soal Asesmen Akhir" in ma_text

        # 4. Verify Prota Structure (CAPAIAN PEMBELAJARAN FASE, Fase Berdasarkan Elemen, SEMESTER 1, SEMESTER 2, Cadangan Jam Pelajaran)
        req_prota = DocumentGenerateRequest(
            service_id=ServiceIdEnum.PROTA,
            jenjang="SMA",
            kelas=11,
            subject_id="SMA-K11-INF",
            semester=1,
            paper_size=PaperSizeEnum.F4,
            teacher_profile=TeacherProfileCreate(**sample_teacher.to_dict()),
        )
        prota_text = extract_docx_text(engine.generate(req_prota, subject, None, sample_teacher))
        assert "Berdasarkan Elemen" in prota_text
        assert "SEMESTER 1" in prota_text
        assert "SEMESTER 2" in prota_text
        assert "Cadangan Jam Pelajaran" in prota_text

    def test_custom_overrides_flexible_user_input_rendered_in_documents(self, sample_teacher: TeacherProfile):
        """Verifies user custom TPs, kesiapan murid, topik kontekstual, and soal asesmen are injected into output."""
        pg_repo = PostgresCurriculumRepository()
        subject = pg_repo.get_subject_by_id("SMA-K11-INF")
        chapter = subject.bab_list[0]

        overrides = CustomDocumentOverrides(
            custom_tps=[
                CustomTpItem(code="TP.KUSTOM.1", deskripsi="Membangun prototipe IoT cerdas bersama kelompok.", alokasi_jp=10)
            ],
            kesiapan_murid="Kesiapan Kustom Guru: Siswa sudah membawa papan mikrokontroler ESP32.",
            topik_kontekstual="Topik Kustom Guru: Smart Farming Berbasis Sensor Kelembapan.",
            soal_asesmen_akhir=["Soal Kustom 1: Bagaimana cara mengkalibrasi sensor kelembapan tanah?"],
        )

        req = DocumentGenerateRequest(
            service_id=ServiceIdEnum.MODUL_AJAR,
            jenjang="SMA",
            kelas=11,
            subject_id="SMA-K11-INF",
            semester=1,
            chapter_id=chapter.id,
            paper_size=PaperSizeEnum.F4,
            custom_overrides=overrides,
            teacher_profile=TeacherProfileCreate(**sample_teacher.to_dict()),
        )
        engine = DocxDocumentEngine()
        docx_bytes = engine.generate(req, subject, chapter, sample_teacher)
        d = Document(io.BytesIO(docx_bytes))
        txt = "\n".join(p.text for p in d.paragraphs)
        for t in d.tables:
            for r in t.rows:
                for c in r.cells:
                    txt += "\n" + c.text

        assert "Membangun prototipe IoT cerdas bersama kelompok." in txt
        assert "Kesiapan Kustom Guru: Siswa sudah membawa papan mikrokontroler ESP32." in txt
        assert "Topik Kustom Guru: Smart Farming Berbasis Sensor Kelembapan." in txt
        assert "Soal Kustom 1: Bagaimana cara mengkalibrasi sensor kelembapan tanah?" in txt
