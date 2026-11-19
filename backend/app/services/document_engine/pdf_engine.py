import re
from typing import Optional, List, Dict, Any
from fpdf import FPDF

from app.core.exceptions import DocumentGenerationError
from app.models.curriculum import CurriculumSubject, ChapterTopic, LearningObjective
from app.models.teacher import TeacherProfile
from app.schemas.generation import DocumentGenerateRequest, ServiceIdEnum
from app.services.document_engine.base_engine import DocumentEngine


def _resolve_effective_tps(chapter: Optional[ChapterTopic], request: DocumentGenerateRequest) -> List[LearningObjective]:
    """Returns customized TPs if teacher provided custom_overrides (custom_tps or tujuan_pembelajaran_custom), otherwise chapter's default TPs."""
    ov = request.custom_overrides
    custom_list = (ov.custom_tps if (ov and ov.custom_tps) else None) or (ov.tujuan_pembelajaran_custom if (ov and ov.tujuan_pembelajaran_custom) else None)
    if custom_list:
        return [
            LearningObjective(
                code=item.code,
                deskripsi=item.deskripsi,
                alokasi_jp=item.alokasi_jp,
                urutan_atp=idx,
            )
            for idx, item in enumerate(custom_list, start=1)
        ]
    return list(chapter.tujuan_pembelajaran) if chapter else []


def _resolve_effective_alokasi_jp(chapter: Optional[ChapterTopic], request: DocumentGenerateRequest) -> int:
    """Returns customized JP if teacher provided custom_overrides (custom_alokasi_jp or alokasi_jp_bab), otherwise chapter's default JP."""
    ov = request.custom_overrides
    if ov:
        if ov.custom_alokasi_jp is not None:
            return ov.custom_alokasi_jp
        if ov.alokasi_jp_bab is not None:
            return ov.alokasi_jp_bab
    if chapter:
        return chapter.calculate_total_jp()
    return 16


def _ascii_safe(text: Any) -> str:
    """Normalizes Unicode punctuation into Latin-1 safe characters for built-in PDF fonts."""
    if text is None:
        return "-"
    s = str(text)
    replacements = {
        "—": "-",
        "–": "-",
        "―": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "*",
        "…": "...",
        "×": "x",
        "≥": ">=",
        "≤": "<=",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    # Strip remaining non-latin-1 characters safely
    return s.encode("latin-1", "ignore").decode("latin-1")


class PdfDocumentEngine(DocumentEngine):
    """Engine responsible for generating official PDF (.pdf) documents on F4/A4 paper."""

    def generate(
        self,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
        raw_template: Optional[dict] = None,
    ) -> bytes:
        try:
            is_landscape = request.service_id == ServiceIdEnum.PROMES
            orientation = "L" if is_landscape else "P"
            if request.paper_size.value == "F4":
                page_format = (self.F4_WIDTH_MM, self.F4_HEIGHT_MM)
            else:
                page_format = (self.A4_WIDTH_MM, self.A4_HEIGHT_MM)

            pdf = FPDF(orientation=orientation, unit="mm", format=page_format)
            pdf.set_margins(left=18, top=16, right=18)
            pdf.set_auto_page_break(auto=True, margin=18)
            pdf.add_page()

            # 1. KOP Surat Sekolah
            self._add_kop_surat(pdf, teacher)

            # 2. Content by Service ID
            tpl = raw_template or (chapter.modul_ajar_template if chapter else {}) or {}
            if request.service_id == ServiceIdEnum.MODUL_AJAR:
                self._build_modul_ajar(pdf, request, subject, chapter, teacher, tpl)
            elif request.service_id == ServiceIdEnum.ATP:
                self._build_atp(pdf, request, subject, chapter)
            elif request.service_id == ServiceIdEnum.CP_TP:
                self._build_cp_tp(pdf, request, subject, chapter)
            elif request.service_id == ServiceIdEnum.PROTA:
                self._build_prota(pdf, request, subject, chapter)
            elif request.service_id == ServiceIdEnum.PROMES:
                self._build_promes(pdf, request, subject, chapter, tpl)

            # 3. Lembar Pengesahan
            self._add_lembar_pengesahan(pdf, teacher)

            return bytes(pdf.output())

        except Exception as e:
            raise DocumentGenerationError(f"Failed to generate PDF document: {str(e)}")

    def _add_kop_surat(self, pdf: FPDF, teacher: TeacherProfile) -> None:
        kop = teacher.get_formatted_kop()
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 5, _ascii_safe(f"PEMERINTAH {kop['kabupaten_kota'].upper()}"), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 6, _ascii_safe(kop["nama_sekolah"]), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(
            0,
            5,
            _ascii_safe(f"NPSN: {kop['npsn']} | {kop['kabupaten_kota']}, {kop['provinsi']}"),
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
        pdf.ln(1)
        y = pdf.get_y()
        pdf.set_line_width(0.5)
        pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
        pdf.ln(5)

    def _add_section_title(self, pdf: FPDF, title: str) -> None:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(29, 78, 216)
        pdf.cell(0, 6, _ascii_safe(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(15, 23, 42)

    def _add_kv_line(self, pdf: FPDF, label: str, value: str) -> None:
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(48, 5.5, _ascii_safe(label))
        pdf.cell(4, 5.5, ":")
        pdf.set_font("Helvetica", "", 9.5)
        pdf.multi_cell(0, 5.5, _ascii_safe(value), new_x="LMARGIN", new_y="NEXT")

    def _build_modul_ajar(
        self,
        pdf: FPDF,
        request: DocumentGenerateRequest,
        subject: CurriculumSubject,
        chapter: Optional[ChapterTopic],
        teacher: TeacherProfile,
        tpl: dict,
    ) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "MODUL AJAR / RPP PENDEKATAN PEMBELAJARAN MENDALAM (3M)", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(0, 5, "Sesuai Kepka BSKAP No. 046/H/KR/2025 & Permendikdasmen No. 13/2025", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(2)

        ident = tpl.get("identifikasi", {}) if isinstance(tpl, dict) else {}
        desain = tpl.get("desain_pembelajaran", {}) if isinstance(tpl, dict) else {}
        inti = tpl.get("komponen_inti", {}) if isinstance(tpl, dict) else {}
        asesmen = tpl.get("asesmen", {}) if isinstance(tpl, dict) else {}
        lampiran = tpl.get("lampiran", {}) if isinstance(tpl, dict) else {}
        ov = request.custom_overrides

        self._add_section_title(pdf, "A. IDENTITAS MODUL & KESESUAIAN PESERTA DIDIK")
        self._add_kv_line(pdf, "Nama Sekolah", teacher.nama_sekolah)
        self._add_kv_line(pdf, "Nama Penyusun", teacher.nama_guru)
        self._add_kv_line(pdf, "Jenjang / Fase / Kelas", f"{subject.jenjang} / Fase {subject.fase} / Kelas {subject.kelas}")
        self._add_kv_line(pdf, "Mata Pelajaran", f"{subject.nama_mapel} ({subject.id_mapel_bskap})")
        self._add_kv_line(pdf, "Bab / Topik Materi", f"Bab {chapter.nomor_bab}: {chapter.judul_bab}" if chapter else "-")
        alokasi_jp = (ov.custom_alokasi_jp if (ov and ov.custom_alokasi_jp) else None) or (chapter.alokasi_jp if chapter else subject.alokasi_jp_mingguan)
        self._add_kv_line(
            pdf,
            "Alokasi Waktu",
            f"{alokasi_jp} JP (1 JP = {subject.durasi_1_jp_menit} Menit)",
        )
        self._add_kv_line(
            pdf,
            "Identifikasi Kesiapan",
            (ov.kesiapan_murid if (ov and ov.kesiapan_murid) else None) or ident.get("kesiapan_murid", "Murid siap mengikuti pembelajaran secara aktif."),
        )
        self._add_kv_line(
            pdf,
            "Karakteristik Materi",
            (ov.karakteristik_materi if (ov and ov.karakteristik_materi) else None) or ident.get("karakteristik_materi", "Materi kontekstual dan aplikatif."),
        )
        self._add_kv_line(
            pdf,
            "Lintas Disiplin Ilmu",
            (ov.lintas_disiplin_ilmu if (ov and ov.lintas_disiplin_ilmu) else None) or desain.get("lintas_disiplin_ilmu", "Bahasa Indonesia, Matematika, Sains, IPS."),
        )
        self._add_kv_line(
            pdf,
            "Topik Kontekstual",
            (ov.topik_kontekstual if (ov and ov.topik_kontekstual) else None) or desain.get("topik_pembelajaran_kontekstual", "Penerapan kontekstual dalam kehidupan nyata."),
        )
        self._add_kv_line(
            pdf,
            "Sarana & Prasarana",
            (ov.sarana_prasarana if (ov and ov.sarana_prasarana) else None) or desain.get("sarana_dan_prasarana", subject.buku_rujukan_sibi or "Buku Teks SIBI"),
        )

        self._add_section_title(pdf, "B. DESAIN & TUJUAN PEMBELAJARAN")
        tps_to_render = (ov.custom_tps if (ov and ov.custom_tps) else None) or (chapter.tujuan_pembelajaran if chapter else [])
        for tp in tps_to_render:
            pdf.set_font("Helvetica", "", 9.5)
            pdf.multi_cell(
                0,
                5,
                _ascii_safe(f"* [{tp.code}] {tp.deskripsi} ({tp.alokasi_jp} JP)"),
                new_x="LMARGIN",
                new_y="NEXT",
            )

        if inti.get("pemahaman_bermakna"):
            pdf.ln(1)
            self._add_kv_line(pdf, "Pemahaman Bermakna", inti["pemahaman_bermakna"])

        pemantik_list = inti.get("pertanyaan_pemantik", [])
        if pemantik_list:
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.cell(0, 5.5, "Pertanyaan Pemantik:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9.5)
            for q in pemantik_list:
                pdf.multi_cell(0, 5, _ascii_safe(f"  - {q}"), new_x="LMARGIN", new_y="NEXT")

        self._add_section_title(pdf, "III. PENGALAMAN BELAJAR (3M: MEMAHAMI, MENGAPLIKASI, MEREFLEKSI)")
        pb = inti.get("pengalaman_belajar", {})
        stages = [
            ("1. Tahap Memahami (Berkesadaran & Bermakna)", pb.get("tahap_memahami", ["Eksplorasi konsep utama materi."])),
            ("2. Tahap Mengaplikasi (Bermakna & Menggembirakan)", pb.get("tahap_mengaplikasi", ["Penyelidikan kolaboratif menggunakan LKPD."])),
            ("3. Tahap Merefleksi (Evaluasi & Metakognisi)", pb.get("tahap_merefleksi", ["Kesimpulan dan refleksi bersama."])),
        ]
        for st_title, st_items in stages:
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.cell(0, 5.5, _ascii_safe(st_title), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9.5)
            for act in st_items:
                pdf.multi_cell(0, 5, _ascii_safe(f"  * {act}"), new_x="LMARGIN", new_y="NEXT")

        if request.include_asesmen:
            self._add_section_title(pdf, "IV. ASESMEN PEMBELAJARAN")
            self._add_kv_line(pdf, "Asesmen Diagnostik", asesmen.get("asesmen_awal_diagnostik", "Tanya jawab kesiapan awal."))
            self._add_kv_line(pdf, "Asesmen Formatif", asesmen.get("asesmen_formatif_proses", "Observasi diskusi & LKPD."))
            self._add_kv_line(pdf, "Asesmen Sumatif", asesmen.get("asesmen_sumatif_akhir", "Tes evaluasi akhir bab."))

        if request.include_lkpd or request.include_rubrik:
            self._add_section_title(pdf, "V. LAMPIRAN LKPD, REMEDIAL/PENGAYAAN & GLOSARIUM")
            lkpd = lampiran.get("lkpd", {})
            if lkpd.get("judul_lkpd"):
                self._add_kv_line(pdf, "Judul LKPD", lkpd["judul_lkpd"])
                for lk_step in lkpd.get("langkah_kerja", []):
                    pdf.multi_cell(0, 5, _ascii_safe(f"  {lk_step}"), new_x="LMARGIN", new_y="NEXT")
            if lampiran.get("glosarium"):
                self._add_kv_line(pdf, "Glosarium", lampiran["glosarium"])

    def _build_cp_tp(self, pdf: FPDF, request: DocumentGenerateRequest, subject: CurriculumSubject, chapter: Optional[ChapterTopic] = None) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "CAPAIAN PEMBELAJARAN (CP) & TUJUAN PEMBELAJARAN (TP)", new_x="LMARGIN", new_y="NEXT", align="C")
        self._add_section_title(pdf, f"MATA PELAJARAN: {subject.nama_mapel} (FASE {subject.fase} - KELAS {subject.kelas})")

        for elem in subject.elemen_cp_resmi:
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.cell(0, 5.5, _ascii_safe(f"Elemen [{elem.get('kode_elemen')}] {elem.get('nama_elemen')}"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 5, _ascii_safe(elem.get("deskripsi_cp", "")), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)

        self._add_section_title(pdf, "PEMETAAN TUJUAN PEMBELAJARAN (TP) PER BAB")
        for ch in subject.bab_list:
            is_current = (request.chapter_id and ch.id == request.chapter_id) or (chapter and ch.id == chapter.id)
            tps = _resolve_effective_tps(ch, request) if is_current else ch.tujuan_pembelajaran
            bab_jp = _resolve_effective_alokasi_jp(ch, request) if is_current else ch.alokasi_jp
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.cell(0, 5.5, _ascii_safe(f"Bab {ch.nomor_bab}: {ch.judul_bab} ({bab_jp} JP)"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            for tp in tps:
                pdf.multi_cell(0, 5, _ascii_safe(f"  - [{tp.code}] {tp.deskripsi} ({tp.alokasi_jp} JP)"), new_x="LMARGIN", new_y="NEXT")

    def _build_atp(self, pdf: FPDF, request: DocumentGenerateRequest, subject: CurriculumSubject, chapter: Optional[ChapterTopic] = None) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "ALUR TUJUAN PEMBELAJARAN (ATP) KURIKULUM MERDEKA", new_x="LMARGIN", new_y="NEXT", align="C")
        self._add_section_title(pdf, f"{subject.nama_mapel} | Fase {subject.fase} | Kelas {subject.kelas} (1 JP = {subject.durasi_1_jp_menit} Menit)")
        for ch in subject.bab_list:
            is_current = (request.chapter_id and ch.id == request.chapter_id) or (chapter and ch.id == chapter.id)
            tps = _resolve_effective_tps(ch, request) if is_current else ch.tujuan_pembelajaran
            bab_jp = _resolve_effective_alokasi_jp(ch, request) if is_current else ch.alokasi_jp
            for tp in tps:
                pdf.set_font("Helvetica", "B", 9.5)
                pdf.cell(0, 5.5, _ascii_safe(f"Alur #{tp.urutan_atp} - [{tp.code}] (Bab {ch.nomor_bab}: {ch.judul_bab} | {tp.alokasi_jp} JP)"), new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 9)
                pdf.multi_cell(0, 5, _ascii_safe(f"  TP: {tp.deskripsi} | DPL: {', '.join(ch.dimensi_profil_lulusan)}"), new_x="LMARGIN", new_y="NEXT")

    def _build_prota(self, pdf: FPDF, request: DocumentGenerateRequest, subject: CurriculumSubject, chapter: Optional[ChapterTopic] = None) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, "PROGRAM TAHUNAN (PROTA) TAHUN AJARAN 2026/2027", new_x="LMARGIN", new_y="NEXT", align="C")
        self._add_section_title(pdf, f"{subject.nama_mapel} | Kelas {subject.kelas} (Total Target: {subject.total_alokasi_jp_tahun} JP/Tahun)")
        total_jp = 0
        for ch in subject.bab_list:
            is_current = (request.chapter_id and ch.id == request.chapter_id) or (chapter and ch.id == chapter.id)
            bab_jp = _resolve_effective_alokasi_jp(ch, request) if is_current else ch.alokasi_jp
            pdf.set_font("Helvetica", "", 9.5)
            pdf.multi_cell(
                0,
                5.5,
                _ascii_safe(f"Semester {ch.semester} | Bab {ch.nomor_bab}: {ch.judul_bab} -> {bab_jp} JP ({ch.estimasi_pertemuan} Pertemuan)"),
                new_x="LMARGIN",
                new_y="NEXT",
            )
            total_jp += bab_jp
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, _ascii_safe(f"TOTAL ALOKASI WAKTU TAHUNAN: {total_jp} JP"), new_x="LMARGIN", new_y="NEXT")

    def _build_promes(self, pdf: FPDF, request: DocumentGenerateRequest, subject: CurriculumSubject, chapter: Optional[ChapterTopic] = None, tpl: Optional[dict] = None) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(
            0,
            6,
            _ascii_safe(f"PROGRAM SEMESTER (PROMES) - SEMESTER {request.semester} TAHUN AJARAN 2026/2027"),
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
        self._add_section_title(pdf, f"{subject.nama_mapel} | Kelas {subject.kelas} (Fase {subject.fase}) | {subject.alokasi_jp_mingguan} JP/Minggu")
        chapters = subject.get_chapters_by_semester(request.semester) or subject.bab_list
        for ch in chapters:
            is_current = (request.chapter_id and ch.id == request.chapter_id) or (chapter and ch.id == chapter.id)
            tps = _resolve_effective_tps(ch, request) if is_current else ch.tujuan_pembelajaran
            bab_jp = _resolve_effective_alokasi_jp(ch, request) if is_current else ch.alokasi_jp
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.cell(
                0,
                5.5,
                _ascii_safe(f"Bab {ch.nomor_bab}: {ch.judul_bab} | Alokasi: {bab_jp} JP | Distribusi: {ch.rentang_minggu_promes or 'Minggu Efektif'}"),
                new_x="LMARGIN",
                new_y="NEXT",
            )
            pdf.set_font("Helvetica", "", 9)
            for tp in tps:
                pdf.multi_cell(0, 5, _ascii_safe(f"  - [{tp.code}] {tp.deskripsi} ({tp.alokasi_jp} JP)"), new_x="LMARGIN", new_y="NEXT")

    def _add_lembar_pengesahan(self, pdf: FPDF, teacher: TeacherProfile) -> None:
        pengesahan = teacher.get_lembar_pengesahan()
        pdf.ln(8)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.cell(0, 5, _ascii_safe(pengesahan["titimangsa"]), new_x="LMARGIN", new_y="NEXT", align="R")
        pdf.ln(2)

        col_w = (pdf.w - pdf.l_margin - pdf.r_margin) / 2.0
        pdf.set_font("Helvetica", "", 9.5)
        pdf.cell(col_w, 5, "Mengetahui, Kepala Sekolah", align="C")
        pdf.cell(col_w, 5, _ascii_safe(pengesahan["jabatan_guru"]), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(14)

        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(col_w, 5, _ascii_safe(pengesahan["nama_kepala_sekolah"]), align="C")
        pdf.cell(col_w, 5, _ascii_safe(pengesahan["nama_guru"]), new_x="LMARGIN", new_y="NEXT", align="C")

        pdf.set_font("Helvetica", "", 9)
        pdf.cell(col_w, 5, _ascii_safe(pengesahan["nip_kepala_sekolah"]), align="C")
        pdf.cell(col_w, 5, _ascii_safe(pengesahan["nip_guru"]), new_x="LMARGIN", new_y="NEXT", align="C")
