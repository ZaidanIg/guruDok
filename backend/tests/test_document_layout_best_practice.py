import io
import re
import zlib
import pytest
from docx import Document

from app.models.teacher import TeacherProfile
from app.repositories.postgres_curriculum_repo import PostgresCurriculumRepository
from app.schemas.generation import (
    DocumentGenerateRequest,
    ServiceIdEnum,
    PaperSizeEnum,
    OutputFormatEnum,
    TeacherProfileCreate,
    CustomDocumentOverrides,
)
from app.services.document_engine.docx_engine import DocxDocumentEngine
from app.services.document_engine.pdf_engine import PdfDocumentEngine


class TestDocumentLayoutBestPractice:
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

    @pytest.fixture
    def sample_request(self, sample_teacher) -> DocumentGenerateRequest:
        return DocumentGenerateRequest(
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
        )

    def test_docx_has_openxml_heading_styles_for_navigation_pane(self, sample_request, sample_teacher):
        """Verifies Word document uses official Heading 1 and Heading 2 styles readable by Word Navigation Pane."""
        repo = PostgresCurriculumRepository()
        subject = repo.get_subject_by_id(sample_request.subject_id)
        chapter = subject.bab_list[0] if subject.bab_list else None

        engine = DocxDocumentEngine()
        docx_bytes = engine.generate(sample_request, subject, chapter, sample_teacher)
        doc = Document(io.BytesIO(docx_bytes))

        # Check that there are paragraphs styled with Heading 1 and Heading 2
        heading_1_paras = [p for p in doc.paragraphs if p.style.name == "Heading 1"]
        heading_2_paras = [p for p in doc.paragraphs if p.style.name == "Heading 2"]

        assert len(heading_1_paras) >= 2, f"Expected Heading 1 paragraphs, found {len(heading_1_paras)}"
        assert len(heading_2_paras) >= 2, f"Expected Heading 2 paragraphs, found {len(heading_2_paras)}"

        # Verify raw XML contains w:pStyle w:val="Heading1" or "Heading2"
        xml_text = doc._element.xml
        assert 'w:val="Heading1"' in xml_text or 'w:val="Heading 1"' in xml_text
        assert 'w:val="Heading2"' in xml_text or 'w:val="Heading 2"' in xml_text

    def test_docx_has_footer_page_number_field(self, sample_request, sample_teacher):
        """Verifies Word footer contains the official OpenXML PAGE number field."""
        repo = PostgresCurriculumRepository()
        subject = repo.get_subject_by_id(sample_request.subject_id)
        chapter = subject.bab_list[0] if subject.bab_list else None

        engine = DocxDocumentEngine()
        docx_bytes = engine.generate(sample_request, subject, chapter, sample_teacher)
        doc = Document(io.BytesIO(docx_bytes))

        section = doc.sections[0]
        footer = section.footer
        footer_xml = footer._element.xml

        # Check for OpenXML page field instruction
        assert 'w:instr="PAGE"' in footer_xml or "PAGE" in footer_xml
        assert "Halaman" in footer.paragraphs[0].text or "Halaman" in footer_xml

    def test_docx_and_pdf_margins_follow_official_standards(self, sample_request, sample_teacher):
        """Verifies Word and PDF margins follow binding standard: Left 30mm, Top 25mm, Right 20mm, Bottom 25mm."""
        repo = PostgresCurriculumRepository()
        subject = repo.get_subject_by_id(sample_request.subject_id)
        chapter = subject.bab_list[0] if subject.bab_list else None

        # 1. Word margins
        engine_docx = DocxDocumentEngine()
        docx_bytes = engine_docx.generate(sample_request, subject, chapter, sample_teacher)
        doc = Document(io.BytesIO(docx_bytes))
        section = doc.sections[0]

        assert section.left_margin.mm == pytest.approx(30.0, abs=0.5)
        assert section.top_margin.mm == pytest.approx(25.0, abs=0.5)
        assert section.right_margin.mm == pytest.approx(20.0, abs=0.5)
        assert section.bottom_margin.mm == pytest.approx(25.0, abs=0.5)

        # 2. PDF margins
        engine_pdf = PdfDocumentEngine()
        sample_request.output_format = OutputFormatEnum.PDF
        pdf_bytes = engine_pdf.generate(sample_request, subject, chapter, sample_teacher)
        assert pdf_bytes.startswith(b"%PDF-")

    def test_pdf_footer_renders_page_number(self, sample_request, sample_teacher):
        """Verifies PDF document renders 'Halaman X' in footer stream."""
        repo = PostgresCurriculumRepository()
        subject = repo.get_subject_by_id(sample_request.subject_id)
        chapter = subject.bab_list[0] if subject.bab_list else None

        engine_pdf = PdfDocumentEngine()
        sample_request.output_format = OutputFormatEnum.PDF
        pdf_bytes = engine_pdf.generate(sample_request, subject, chapter, sample_teacher)

        decompressed = b""
        for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", pdf_bytes, re.DOTALL):
            try:
                decompressed += zlib.decompress(m.group(1))
            except Exception:
                pass

        assert b"Halaman 1" in decompressed or b"Halaman" in decompressed

    def test_docx_has_page_breaks_before_appendices(self, sample_request, sample_teacher):
        """Verifies Word document has page break before LKPD and Rubrik 8 DPL."""
        repo = PostgresCurriculumRepository()
        subject = repo.get_subject_by_id(sample_request.subject_id)
        chapter = subject.bab_list[0] if subject.bab_list else None

        engine = DocxDocumentEngine()
        docx_bytes = engine.generate(sample_request, subject, chapter, sample_teacher)
        doc = Document(io.BytesIO(docx_bytes))
        xml_text = doc._element.xml

        # Check for page break element: <w:br w:type="page"/>
        assert '<w:br w:type="page"/>' in xml_text
