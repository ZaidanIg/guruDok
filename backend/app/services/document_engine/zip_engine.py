import io
import zipfile
from typing import List, Optional, Tuple

from app.core.exceptions import DocumentGenerationError
from app.models.curriculum import ChapterTopic, CurriculumSubject
from app.models.teacher import TeacherProfile
from app.schemas.generation import DocumentGenerateRequest, OutputFormatEnum, ServiceIdEnum
from app.services.document_engine.base_engine import DocumentEngine
from app.services.document_engine.docx_engine import DocxDocumentEngine
from app.services.document_engine.pdf_engine import PdfDocumentEngine
from app.services.document_engine.xlsx_engine import XlsxDocumentEngine


class ZipBundleEngine(DocumentEngine):
    """Generates a complete Master Bundle (.zip) archive for Service 18 (Paket Siap Supervisi)."""

    def __init__(self) -> None:
        self._docx_engine = DocxDocumentEngine()
        self._xlsx_engine = XlsxDocumentEngine()
        self._pdf_engine = PdfDocumentEngine()

    def generate(
        self,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
        raw_template: Optional[dict] = None,
    ) -> bytes:
        try:
            effective_chapter = chapter or (subject.bab_list[0] if subject.bab_list else None)
            entries: List[Tuple[str, ServiceIdEnum, OutputFormatEnum]] = [
                ("01_Cover_Pengesahan_Instrumen_Supervisi.docx", ServiceIdEnum.PAKET_SUPERVISI, OutputFormatEnum.DOCX),
                ("02_Administrasi_Kelas.docx", ServiceIdEnum.ADMIN_KELAS, OutputFormatEnum.DOCX),
                ("03_CP_dan_TP.docx", ServiceIdEnum.CP_TP, OutputFormatEnum.DOCX),
                ("04_Alur_Tujuan_Pembelajaran_ATP.docx", ServiceIdEnum.ATP, OutputFormatEnum.DOCX),
                ("05_Program_Tahunan_Prota.docx", ServiceIdEnum.PROTA, OutputFormatEnum.DOCX),
                ("06_Program_Semester_Promes.xlsx", ServiceIdEnum.PROMES, OutputFormatEnum.XLSX),
                ("07_KKTP.docx", ServiceIdEnum.KKTP, OutputFormatEnum.DOCX),
                ("08_Modul_Ajar_DeepLearning_3M.docx", ServiceIdEnum.MODUL_AJAR, OutputFormatEnum.DOCX),
                ("09_LKPD_Mandiri.docx", ServiceIdEnum.LKPD, OutputFormatEnum.DOCX),
                ("13_Presensi_Siswa_Bulanan.xlsx", ServiceIdEnum.PRESENSI, OutputFormatEnum.XLSX),
                ("14_Jurnal_Mengajar_Harian.docx", ServiceIdEnum.JURNAL_MENGAJAR, OutputFormatEnum.DOCX),
                ("15_Daftar_Nilai_Siswa.xlsx", ServiceIdEnum.DAFTAR_NILAI, OutputFormatEnum.XLSX),
                ("16_Deskripsi_eRapor.docx", ServiceIdEnum.DESKRIPSI_RAPOR, OutputFormatEnum.DOCX),
                ("17_Rekap_Nilai_Rapor.xlsx", ServiceIdEnum.REKAP_RAPOR, OutputFormatEnum.XLSX),
                ("18_Binder_Supervisi_Siap_Cetak.pdf", ServiceIdEnum.PAKET_SUPERVISI, OutputFormatEnum.PDF),
            ]

            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for arcname, svc_id, fmt in entries:
                    sub_req = request.model_copy(
                        update={
                            "service_id": svc_id,
                            "output_format": fmt,
                        }
                    )
                    if fmt == OutputFormatEnum.XLSX:
                        content = self._xlsx_engine.generate(
                            sub_req, subject, effective_chapter, teacher, raw_template
                        )
                    elif fmt == OutputFormatEnum.PDF:
                        content = self._pdf_engine.generate(
                            sub_req, subject, effective_chapter, teacher, raw_template
                        )
                    else:
                        content = self._docx_engine.generate(
                            sub_req, subject, effective_chapter, teacher, raw_template
                        )
                    zf.writestr(arcname, content)

            buffer.seek(0)
            return buffer.getvalue()
        except Exception as e:
            raise DocumentGenerationError(f"Failed to build Supervisi ZIP bundle: {str(e)}")
