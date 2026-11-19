from typing import Optional
from app.schemas.generation import ServiceIdEnum, OutputFormatEnum
from app.services.document_engine.base_engine import DocumentEngine
from app.services.document_engine.docx_engine import DocxDocumentEngine
from app.services.document_engine.xlsx_engine import XlsxDocumentEngine
from app.services.document_engine.pdf_engine import PdfDocumentEngine


class DocumentEngineFactory:
    """Factory to instantiate and return the correct document engine strategy for .docx, .xlsx, or .pdf."""

    _docx_engine = DocxDocumentEngine()
    _xlsx_engine = XlsxDocumentEngine()
    _pdf_engine = PdfDocumentEngine()

    @classmethod
    def get_engine(
        cls,
        service_id: ServiceIdEnum,
        output_format: Optional[OutputFormatEnum] = None,
    ) -> DocumentEngine:
        """Returns the appropriate DocumentEngine instance based on requested output format or service default."""
        if output_format == OutputFormatEnum.PDF:
            return cls._pdf_engine
        if output_format == OutputFormatEnum.XLSX:
            return cls._xlsx_engine
        if output_format == OutputFormatEnum.DOCX:
            return cls._docx_engine

        # Default fallback by service type when output_format is not explicitly specified
        if service_id == ServiceIdEnum.PROMES:
            return cls._xlsx_engine
        return cls._docx_engine
