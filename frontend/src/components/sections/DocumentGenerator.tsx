import React, { useState } from 'react';
import {
  ArrowLeft,
  Loader2,
  Edit3,
  AlertCircle,
  Plus,
  Trash2,
  RotateCcw,
  FileDown,
  Eye,
  Sliders,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  ChapterTopic,
  CurriculumSubject,
  CustomDocumentOverrides,
  CustomTpItem,
  Jenjang,
  OutputFormat,
  PaperSize,
  ServiceCatalogItem,
  ServiceId,
  TeacherProfile,
} from '../../types';
import {
  CORE_SERVICES,
  FASE_BY_GRADE,
  GRADES_BY_JENJANG,
  PEDAGOGICAL_MODELS,
} from '../../constants/services';
import { AddChapterModal } from '../modals/AddChapterModal';

interface DocumentGeneratorProps {
  activeService: ServiceCatalogItem;
  jenjang: Jenjang;
  kelas: number;
  subjects: CurriculumSubject[];
  selectedSubject: CurriculumSubject | null;
  semester: number;
  chapters: ChapterTopic[];
  selectedChapter: ChapterTopic | null;
  modelPembelajaran: string;
  paperSize: PaperSize;
  outputFormat: OutputFormat;
  includeLkpd: boolean;
  includeAsesmen: boolean;
  includeRubrik: boolean;
  teacher: TeacherProfile;
  customOverrides: CustomDocumentOverrides;
  isGenerating: boolean;
  errorMsg: string | null;
  onSelectService: (serviceId: ServiceId) => void;
  onChangeJenjang: (val: Jenjang) => void;
  onChangeKelas: (val: number) => void;
  onChangeSubject: (subjectId: string) => void;
  onChangeSemester: (val: number) => void;
  onChangeChapter: (chapterId: string) => void;
  onChangeModelPembelajaran: (val: string) => void;
  onChangePaperSize: (val: PaperSize) => void;
  onChangeOutputFormat: (val: OutputFormat) => void;
  onToggleLkpd: () => void;
  onToggleAsesmen: () => void;
  onToggleRubrik: () => void;
  onChangeCustomOverrides: (next: CustomDocumentOverrides) => void;
  onResetCustomOverrides: () => void;
  onOpenProfileModal: () => void;
  onBackToCatalog: () => void;
  onGenerate: () => void;
  onChapterCreated: (newChapter: ChapterTopic) => void;
}

export const DocumentGenerator: React.FC<DocumentGeneratorProps> = ({
  activeService,
  jenjang,
  kelas,
  subjects,
  selectedSubject,
  semester,
  chapters,
  selectedChapter,
  modelPembelajaran,
  paperSize,
  outputFormat,
  includeLkpd,
  includeAsesmen,
  includeRubrik,
  teacher,
  customOverrides,
  isGenerating,
  errorMsg,
  onSelectService,
  onChangeJenjang,
  onChangeKelas,
  onChangeSubject,
  onChangeSemester,
  onChangeChapter,
  onChangeModelPembelajaran,
  onChangePaperSize,
  onChangeOutputFormat,
  onToggleLkpd,
  onToggleAsesmen,
  onToggleRubrik,
  onChangeCustomOverrides,
  onResetCustomOverrides,
  onOpenProfileModal,
  onBackToCatalog,
  onGenerate,
  onChapterCreated,
}) => {
  const [mobileViewMode, setMobileViewMode] = useState<'form' | 'preview'>('form');
  const [showPedagogicalEditor, setShowPedagogicalEditor] = useState<boolean>(true);
  const [showAssessmentEditor, setShowAssessmentEditor] = useState<boolean>(false);
  const [isAddChapterModalOpen, setIsAddChapterModalOpen] = useState<boolean>(false);

  const grades = GRADES_BY_JENJANG[jenjang];
  const faseCode = selectedSubject
    ? selectedSubject.fase.replace('Fase ', '').trim()
    : (FASE_BY_GRADE[kelas] || 'Fase D').replace('Fase ', '').trim();
  const faseLabel = `Fase ${faseCode}`;

  const rawTpl = selectedChapter?.modul_ajar_template || {};
  const identifikasiObj = rawTpl.identifikasi || {};
  const desainObj = rawTpl.desain_pembelajaran || {};
  const komponenIntiObj = rawTpl.komponen_inti || {};
  const asesmenObj = rawTpl.asesmen || {};

  // Effective TP list (custom overrides or chapter default)
  const defaultTps: CustomTpItem[] = (
    selectedChapter?.tujuan_pembelajaran ||
    selectedSubject?.bab_list?.[0]?.tujuan_pembelajaran ||
    []
  ).map((t) => ({
    code: t.code,
    deskripsi: t.deskripsi,
    alokasi_jp: t.alokasi_jp,
  }));

  const activeTps: CustomTpItem[] =
    customOverrides.tujuan_pembelajaran_custom &&
    customOverrides.tujuan_pembelajaran_custom.length > 0
      ? customOverrides.tujuan_pembelajaran_custom
      : defaultTps;

  const currentAlokasiJp =
    customOverrides.alokasi_jp_bab ||
    selectedChapter?.alokasi_jp ||
    activeTps.reduce((acc, t) => acc + (Number(t.alokasi_jp) || 0), 0) ||
    12;

  const jpPerMinggu = selectedSubject?.alokasi_jp_mingguan || 3;
  const durasiMenitJp =
    selectedSubject?.durasi_1_jp_menit ||
    (jenjang === 'SD' ? 35 : jenjang === 'SMP' ? 40 : 45);
  const pertemuanCount = Math.max(1, Math.round(currentAlokasiJp / jpPerMinggu));

  const formatExtLabel =
    outputFormat === 'xlsx'
      ? 'EXCEL (.XLSX)'
      : outputFormat === 'pdf'
      ? 'PDF (.PDF)'
      : 'WORD (.DOCX)';

  const officialElements =
    selectedSubject?.elemen_cp_resmi && selectedSubject.elemen_cp_resmi.length > 0
      ? selectedSubject.elemen_cp_resmi
      : [
          {
            kode_elemen: 'EL-01',
            nama_elemen: selectedChapter?.elemen_cp || 'Pemahaman Konsep',
            deskripsi_cp: `Peserta didik mampu memahami dan menerapkan konsep inti ${
              selectedSubject?.nama_mapel || 'Mata Pelajaran'
            } pada ${faseLabel} secara sistematis dan kontekstual.`,
          },
          {
            kode_elemen: 'EL-02',
            nama_elemen: 'Keterampilan Proses',
            deskripsi_cp: `Peserta didik mampu mengamati, menanya, merencanakan penyelidikan, menganalisis data, dan mengomunikasikan hasil karya ${
              selectedSubject?.nama_mapel || 'Mata Pelajaran'
            } secara kolaboratif.`,
          },
        ];

  const effectiveKesiapanMurid =
    customOverrides.kesiapan_murid ??
    identifikasiObj.kesiapan_murid ??
    `Sebagian besar peserta didik Kelas ${kelas} telah memiliki pengetahuan awal dasar terkait ${
      selectedChapter?.judul_bab || 'materi pokok'
    }, namun perlu penguatan dalam analisis pemecahan masalah kontekstual dan kerja kolaboratif.`;

  const effectiveKarakteristikMateri =
    customOverrides.karakteristik_materi ??
    identifikasiObj.karakteristik_materi ??
    `Materi ${selectedChapter?.judul_bab || 'Bab ini'} mencakup pengetahuan konseptual, prosedural, dan metakognitif yang relevan dengan kehidupan nyata peserta didik.`;

  const effectiveLintasDisiplin =
    customOverrides.lintas_disiplin_ilmu ??
    desainObj.lintas_disiplin_ilmu ??
    `Bahasa Indonesia (komunikasi ilmiah & presentasi), Matematika (penalaran logis & pengolahan data), serta Informatika (literasi digital).`;

  const effectiveTopikKontekstual =
    customOverrides.topik_kontekstual ??
    desainObj.topik_pembelajaran_kontekstual ??
    `Penerapan konsep ${selectedChapter?.judul_bab || 'Materi Pokok'} dalam pemecahan masalah kehidupan sehari-hari di lingkungan sekolah dan masyarakat.`;

  const effectivePemantik: string[] =
    customOverrides.pertanyaan_pemantik && customOverrides.pertanyaan_pemantik.length > 0
      ? customOverrides.pertanyaan_pemantik
      : komponenIntiObj.pertanyaan_pemantik || [
          `Mengapa konsep ${selectedChapter?.judul_bab || 'materi ini'} penting dipelajari dalam kehidupan sehari-hari?`,
          `Bagaimana cara menerapkan prinsip ${selectedChapter?.judul_bab || 'materi ini'} untuk menyelesaikan masalah di sekitar kita?`,
        ];

  const effectiveSoalAwal: string[] =
    customOverrides.soal_asesmen_awal && customOverrides.soal_asesmen_awal.length > 0
      ? customOverrides.soal_asesmen_awal
      : asesmenObj.soal_asesmen_awal || [
          `Jelaskan pengertian dasar dari ${selectedChapter?.judul_bab || 'materi pokok'} menurut pemahaman awal Anda!`,
          `Sebutkan contoh penerapan ${selectedChapter?.judul_bab || 'materi ini'} yang pernah Anda temui!`,
        ];

  const effectiveSoalProses: string[] =
    customOverrides.soal_asesmen_proses && customOverrides.soal_asesmen_proses.length > 0
      ? customOverrides.soal_asesmen_proses
      : asesmenObj.soal_asesmen_proses || [
          `Identifikasi komponen utama dan hubungan sebab-akibat pada studi kasus ${selectedChapter?.judul_bab || 'materi ini'} di LKPD!`,
          `Presentasikan hasil analisis kelompok Anda dan berikan tanggapan konstruktif kepada kelompok lain!`,
        ];

  const effectiveSoalAkhir: string[] =
    customOverrides.soal_asesmen_akhir && customOverrides.soal_asesmen_akhir.length > 0
      ? customOverrides.soal_asesmen_akhir
      : asesmenObj.soal_asesmen_akhir || [
          `Analisislah permasalahan kontekstual berikut menggunakan konsep ${selectedChapter?.judul_bab || 'materi ini'} secara sistematis!`,
          `Simpulkan solusi terbaik beserta alasan ilmiah yang mendukung keputusan tersebut!`,
        ];

  // Handlers for TP manipulation
  const handleUpdateTp = (idx: number, field: keyof CustomTpItem, value: string | number) => {
    const nextList = activeTps.map((item, i) =>
      i === idx ? { ...item, [field]: value } : item
    );
    const totalJp = nextList.reduce((acc, t) => acc + (Number(t.alokasi_jp) || 0), 0);
    onChangeCustomOverrides({
      ...customOverrides,
      tujuan_pembelajaran_custom: nextList,
      alokasi_jp_bab: totalJp > 0 ? totalJp : customOverrides.alokasi_jp_bab,
    });
  };

  const handleAddTp = () => {
    const nextNum = activeTps.length + 1;
    const chNum = selectedChapter?.nomor_bab || 1;
    const newTp: CustomTpItem = {
      code: `TP.${kelas}.${chNum}.${nextNum}`,
      deskripsi: `Menganalisis dan menerapkan konsep lanjutan ${
        selectedChapter?.judul_bab || 'materi pokok'
      } secara kolaboratif.`,
      alokasi_jp: jpPerMinggu,
    };
    const nextList = [...activeTps, newTp];
    const totalJp = nextList.reduce((acc, t) => acc + (Number(t.alokasi_jp) || 0), 0);
    onChangeCustomOverrides({
      ...customOverrides,
      tujuan_pembelajaran_custom: nextList,
      alokasi_jp_bab: totalJp,
    });
  };

  const handleRemoveTp = (idx: number) => {
    if (activeTps.length <= 1) return;
    const nextList = activeTps.filter((_, i) => i !== idx);
    const totalJp = nextList.reduce((acc, t) => acc + (Number(t.alokasi_jp) || 0), 0);
    onChangeCustomOverrides({
      ...customOverrides,
      tujuan_pembelajaran_custom: nextList,
      alokasi_jp_bab: totalJp,
    });
  };

  const activeDimensions = selectedChapter?.dimensi_profil_lulusan || [
    'Penalaran Kritis',
    'Kreativitas',
    'Kolaborasi',
    'Kemandirian',
  ];

  const allSubjectChapters =
    selectedSubject?.bab_list && selectedSubject.bab_list.length > 0
      ? selectedSubject.bab_list
      : chapters;

  const sem1Chapters = allSubjectChapters.filter((c) => c.semester === 1);
  const sem2Chapters = allSubjectChapters.filter((c) => c.semester === 2);
  const currentSemesterChapters =
    semester === 1
      ? sem1Chapters.length > 0
        ? sem1Chapters
        : chapters
      : sem2Chapters.length > 0
      ? sem2Chapters
      : chapters;

  const monthLabels =
    semester === 1
      ? ['JUL', 'AGU', 'SEP', 'OKT', 'NOV', 'DES']
      : ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN'];

  const activeCoreServices = CORE_SERVICES.filter((s) => !s.isComingSoon);

  return (
    <section id="generator-section" className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      {/* Top Bar: Breadcrumb & Back to Catalog */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500">
            <button
              type="button"
              onClick={onBackToCatalog}
              className="text-blue-700 hover:underline"
            >
              Katalog Layanan
            </button>
            <span>/</span>
            <span className="font-bold text-slate-800">{activeService.title}</span>
          </div>
          <h1 className="mt-1 text-xl font-extrabold tracking-tight text-slate-900 sm:text-2xl">
            Studio Generator: {activeService.title}
          </h1>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onOpenProfileModal}
            className="clay-btn-white inline-flex items-center gap-1.5 px-3 py-2 text-xs font-bold text-slate-700"
          >
            <Edit3 className="h-3.5 w-3.5 text-blue-700" />
            <span>Ubah KOP Sekolah</span>
          </button>

          <button
            type="button"
            onClick={onBackToCatalog}
            className="clay-btn-white inline-flex items-center gap-1.5 px-3 py-2 text-xs font-bold text-slate-700"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Kembali ke Katalog</span>
          </button>
        </div>
      </div>

      {/* Service Switcher Bar */}
      <div className="mt-4 flex flex-wrap items-center gap-2">
        {activeCoreServices.map((srv) => {
          const isCurrent = srv.id === activeService.id;
          return (
            <button
              key={srv.id}
              type="button"
              onClick={() => onSelectService(srv.id as ServiceId)}
              className={`rounded-lg px-3.5 py-2 text-xs font-bold transition-all ${
                isCurrent
                  ? 'bg-blue-700 text-white shadow-sm'
                  : 'bg-white text-slate-700 border border-slate-200 hover:border-blue-400'
              }`}
            >
              {srv.codeLabel}: {srv.shortTitle}
            </button>
          );
        })}
      </div>

      {/* Mobile View Mode Toggle (< 768px only: 1 Column Form vs 1 Column Preview) */}
      <div className="mt-4 grid grid-cols-2 gap-2 rounded-xl bg-slate-200/80 p-1 md:hidden">
        <button
          type="button"
          onClick={() => setMobileViewMode('form')}
          className={`flex items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-bold ${
            mobileViewMode === 'form'
              ? 'bg-white text-blue-700 shadow-sm'
              : 'text-slate-600'
          }`}
        >
          <Sliders className="h-3.5 w-3.5" />
          <span>Form &amp; Editor Data</span>
        </button>
        <button
          type="button"
          onClick={() => setMobileViewMode('preview')}
          className={`flex items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-bold ${
            mobileViewMode === 'preview'
              ? 'bg-white text-blue-700 shadow-sm'
              : 'text-slate-600'
          }`}
        >
          <Eye className="h-3.5 w-3.5" />
          <span>Pratinjau Dokumen</span>
        </button>
      </div>

      {/* Error Alert */}
      {errorMsg && (
        <div className="mt-4 flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-xs font-bold text-red-700 sm:text-sm">
          <AlertCircle className="h-5 w-5 shrink-0 text-red-600" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/*
        RESPONSIVE SPLIT-VIEW GRID:
        - Mobile (<768px): grid-cols-1 (1 column! Form or Preview via toggle)
        - Tablet (md: 768px-1023px): md:grid-cols-2 (1 col Form + 1 col Live Preview)
        - Laptop (lg: 1024px-1279px): lg:grid-cols-3 (1 col Form + 2 cols Live Preview)
        - Large Monitor (xl: >=1280px): xl:grid-cols-5 (2 cols Form + 3 cols Live Preview)
      */}
      <div className="mt-5 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {/* LEFT PANEL: FORM KURIKULUM & EDITOR DATA FLEKSIBEL */}
        <div
          className={`space-y-5 md:col-span-1 lg:col-span-1 xl:col-span-2 ${
            mobileViewMode === 'preview' ? 'hidden md:block' : 'block'
          }`}
        >
          {/* Card 1: Parameter Kurikulum & Format Cetak */}
          <div className="clay-card p-5">
            <h2 className="border-b border-slate-200 pb-3 text-sm font-extrabold uppercase tracking-wider text-slate-800">
              1. Parameter Kurikulum &amp; Format
            </h2>

            <div className="mt-4 space-y-3.5">
              {/* Jenjang & Kelas */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Jenjang Pendidikan
                  </label>
                  <select
                    value={jenjang}
                    onChange={(e) => onChangeJenjang(e.target.value as Jenjang)}
                    className="clay-input w-full px-3 py-2.5 text-xs font-bold text-slate-800 sm:text-sm"
                  >
                    <option value="SD">SD / MI</option>
                    <option value="SMP">SMP / MTs</option>
                    <option value="SMA">SMA / MA</option>
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Kelas ({faseLabel})
                  </label>
                  <select
                    value={kelas}
                    onChange={(e) => onChangeKelas(Number(e.target.value))}
                    className="clay-input w-full px-3 py-2.5 text-xs font-bold text-slate-800 sm:text-sm"
                  >
                    {grades.map((g) => (
                      <option key={g} value={g}>
                        Kelas {g}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Mata Pelajaran */}
              <div>
                <label className="mb-1 block text-xs font-bold text-slate-700">
                  Mata Pelajaran (Database GuruDocDB)
                </label>
                <select
                  value={selectedSubject?.id || ''}
                  onChange={(e) => onChangeSubject(e.target.value)}
                  className="clay-input w-full px-3 py-2.5 text-xs font-bold text-slate-800 sm:text-sm"
                >
                  {subjects.map((subj) => (
                    <option key={subj.id} value={subj.id}>
                      {subj.nama_mapel} — Kelas {subj.kelas} ({subj.fase})
                    </option>
                  ))}
                </select>
              </div>

              {/* Semester & Bab */}
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Semester
                  </label>
                  <select
                    value={semester}
                    onChange={(e) => onChangeSemester(Number(e.target.value))}
                    className="clay-input w-full px-3 py-2.5 text-xs font-bold text-slate-800 sm:text-sm"
                  >
                    <option value={1}>Semester 1 (Ganjil)</option>
                    <option value={2}>Semester 2 (Genap)</option>
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Alokasi JP Bab
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={120}
                    value={currentAlokasiJp}
                    onChange={(e) =>
                      onChangeCustomOverrides({
                        ...customOverrides,
                        alokasi_jp_bab: Math.max(1, Number(e.target.value) || 2),
                      })
                    }
                    className="clay-input w-full px-3 py-2.5 text-xs font-bold text-slate-800 sm:text-sm"
                  />
                </div>
              </div>

              {/* Bab / Materi Pokok */}
              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <label className="block text-xs font-bold text-slate-700">
                    Bab / Lingkup Materi Pokok
                  </label>
                  <button
                    type="button"
                    onClick={() => setIsAddChapterModalOpen(true)}
                    className="inline-flex items-center gap-1 rounded-md border border-blue-200 bg-blue-50 px-2 py-0.5 text-xs font-bold text-blue-700 hover:bg-blue-100 transition-colors"
                  >
                    <Plus className="h-3 w-3" />
                    <span>Tambah Bab</span>
                  </button>
                </div>
                <select
                  value={selectedChapter?.id || ''}
                  onChange={(e) => onChangeChapter(e.target.value)}
                  className="clay-input w-full px-3 py-2.5 text-xs font-bold text-slate-800 sm:text-sm"
                >
                  {chapters.map((ch) => (
                    <option key={ch.id} value={ch.id}>
                      Bab {ch.nomor_bab} (Sem {ch.semester}): {ch.judul_bab}
                    </option>
                  ))}
                </select>
              </div>

              {/* Model Pembelajaran */}
              <div>
                <label className="mb-1 block text-xs font-bold text-slate-700">
                  Model Pembelajaran Pedagogis
                </label>
                <select
                  value={modelPembelajaran}
                  onChange={(e) => onChangeModelPembelajaran(e.target.value)}
                  className="clay-input w-full px-3 py-2.5 text-xs font-bold text-slate-800 sm:text-sm"
                >
                  {PEDAGOGICAL_MODELS.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>

              {/* Format Output & Ukuran Kertas */}
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Format File Output
                  </label>
                  {(() => {
                    const supported = (activeService.formats || ['DOCX', 'PDF']).map((f) => f.toLowerCase() as OutputFormat);
                    const formatOptions = (
                      [
                        { id: 'docx', label: 'DOCX' },
                        { id: 'xlsx', label: 'XLSX' },
                        { id: 'pdf', label: 'PDF' },
                      ] as { id: OutputFormat; label: string }[]
                    ).filter((fmt) => supported.includes(fmt.id));

                    return (
                      <div className={`grid gap-1.5 ${formatOptions.length === 2 ? 'grid-cols-2' : 'grid-cols-3'}`}>
                        {formatOptions.map((fmt) => (
                          <button
                            key={fmt.id}
                            type="button"
                            onClick={() => onChangeOutputFormat(fmt.id)}
                            className={`py-2 text-xs font-bold ${
                              outputFormat === fmt.id ? 'clay-btn-primary' : 'clay-btn-white'
                            }`}
                          >
                            {fmt.label}
                          </button>
                        ))}
                      </div>
                    );
                  })()}
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Ukuran Kertas Cetak
                  </label>
                  <div className="grid grid-cols-2 gap-1.5">
                    <button
                      type="button"
                      onClick={() => onChangePaperSize('F4')}
                      className={`py-2 text-xs font-bold ${
                        paperSize === 'F4' ? 'clay-btn-primary' : 'clay-btn-white'
                      }`}
                    >
                      F4 / Folio
                    </button>
                    <button
                      type="button"
                      onClick={() => onChangePaperSize('A4')}
                      className={`py-2 text-xs font-bold ${
                        paperSize === 'A4' ? 'clay-btn-primary' : 'clay-btn-white'
                      }`}
                    >
                      A4 Standar
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Editor Fleksibel Tujuan Pembelajaran (TP) */}
          <div className="clay-card p-5">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
              <div>
                <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800">
                  2. Editor Tujuan Pembelajaran (TP)
                </h2>
                <p className="text-[11px] font-medium text-slate-500">
                  Tambah, ubah, atau hapus butir TP sesuai kebutuhan kelas Anda.
                </p>
              </div>
              <button
                type="button"
                onClick={onResetCustomOverrides}
                title="Kembalikan ke data standar database"
                className="inline-flex items-center gap-1 text-xs font-bold text-slate-500 hover:text-blue-700"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Reset Default</span>
              </button>
            </div>

            <div className="mt-4 space-y-3">
              {activeTps.map((tp, idx) => (
                <div key={idx} className="clay-subcard p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={tp.code}
                        onChange={(e) => handleUpdateTp(idx, 'code', e.target.value)}
                        aria-label={`Kode TP ${idx + 1}`}
                        className="clay-input w-24 px-2 py-1 text-xs font-bold text-blue-800"
                      />
                      <div className="flex items-center gap-1">
                        <input
                          type="number"
                          min={1}
                          max={40}
                          value={tp.alokasi_jp}
                          onChange={(e) =>
                            handleUpdateTp(
                              idx,
                              'alokasi_jp',
                              Math.max(1, Number(e.target.value) || 2)
                            )
                          }
                          aria-label={`Alokasi JP TP ${idx + 1}`}
                          className="clay-input w-14 px-2 py-1 text-center text-xs font-bold text-slate-800"
                        />
                        <span className="text-xs font-bold text-slate-500">JP</span>
                      </div>
                    </div>

                    {activeTps.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveTp(idx)}
                        title="Hapus butir TP ini"
                        className="rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>

                  <textarea
                    rows={2}
                    value={tp.deskripsi}
                    onChange={(e) => handleUpdateTp(idx, 'deskripsi', e.target.value)}
                    aria-label={`Deskripsi TP ${idx + 1}`}
                    className="clay-input mt-2 w-full px-2.5 py-1.5 text-xs font-medium text-slate-800"
                  />
                </div>
              ))}

              <button
                type="button"
                onClick={handleAddTp}
                className="clay-btn-white flex w-full items-center justify-center gap-1.5 py-2.5 text-xs font-bold text-blue-700"
              >
                <Plus className="h-4 w-4" />
                <span>Tambah Tujuan Pembelajaran (TP) Baru</span>
              </button>
            </div>
          </div>

          {/* Card 3: Editor Konten Pedagogis & Kontekstual Fleksibel */}
          <div className="clay-card p-5">
            <button
              type="button"
              onClick={() => setShowPedagogicalEditor((v) => !v)}
              className="flex w-full items-center justify-between text-left"
            >
              <div>
                <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800">
                  3. Kustomisasi Isi Dokumen &amp; Pedagogis
                </h2>
                <p className="text-[11px] font-medium text-slate-500">
                  Kesiapan murid, topik kontekstual, pertanyaan pemantik &amp; catatan.
                </p>
              </div>
              {showPedagogicalEditor ? (
                <ChevronUp className="h-4 w-4 text-slate-500" />
              ) : (
                <ChevronDown className="h-4 w-4 text-slate-500" />
              )}
            </button>

            {showPedagogicalEditor && (
              <div className="mt-4 space-y-3 border-t border-slate-200 pt-4">
                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Identifikasi Kesiapan Peserta Didik
                  </label>
                  <textarea
                    rows={2}
                    value={effectiveKesiapanMurid}
                    onChange={(e) =>
                      onChangeCustomOverrides({
                        ...customOverrides,
                        kesiapan_murid: e.target.value,
                      })
                    }
                    className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Karakteristik Materi Pelajaran
                  </label>
                  <textarea
                    rows={2}
                    value={effectiveKarakteristikMateri}
                    onChange={(e) =>
                      onChangeCustomOverrides({
                        ...customOverrides,
                        karakteristik_materi: e.target.value,
                      })
                    }
                    className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Lintas Disiplin Ilmu yang Relevan
                  </label>
                  <input
                    type="text"
                    value={effectiveLintasDisiplin}
                    onChange={(e) =>
                      onChangeCustomOverrides({
                        ...customOverrides,
                        lintas_disiplin_ilmu: e.target.value,
                      })
                    }
                    className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Topik Pembelajaran Kontekstual
                  </label>
                  <textarea
                    rows={2}
                    value={effectiveTopikKontekstual}
                    onChange={(e) =>
                      onChangeCustomOverrides({
                        ...customOverrides,
                        topik_kontekstual: e.target.value,
                      })
                    }
                    className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Pertanyaan Pemantik (1 baris per pertanyaan)
                  </label>
                  <textarea
                    rows={3}
                    value={effectivePemantik.join('\n')}
                    onChange={(e) =>
                      onChangeCustomOverrides({
                        ...customOverrides,
                        pertanyaan_pemantik: e.target.value
                          .split('\n')
                          .map((s) => s.trim())
                          .filter(Boolean),
                      })
                    }
                    className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>

                {activeService.id === '05_prota' && (
                  <div>
                    <label className="mb-1 block text-xs font-bold text-slate-700">
                      Cadangan Jam Pelajaran Tahunan (JP)
                    </label>
                    <input
                      type="number"
                      min={0}
                      max={60}
                      value={customOverrides.cadangan_jp ?? 0}
                      onChange={(e) =>
                        onChangeCustomOverrides({
                          ...customOverrides,
                          cadangan_jp: Math.max(0, Number(e.target.value) || 0),
                        })
                      }
                      className="clay-input w-full px-3 py-2 text-xs font-bold text-slate-800"
                    />
                  </div>
                )}

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Catatan Khusus Penggunaan Dokumen
                  </label>
                  <input
                    type="text"
                    value={customOverrides.catatan_khusus || ''}
                    placeholder="Contoh: Disesuaikan dengan jadwal blok praktikum sekolah..."
                    onChange={(e) =>
                      onChangeCustomOverrides({
                        ...customOverrides,
                        catatan_khusus: e.target.value,
                      })
                    }
                    className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Card 4: Editor Soal Asesmen & Lampiran */}
          <div className="clay-card p-5">
            <button
              type="button"
              onClick={() => setShowAssessmentEditor((v) => !v)}
              className="flex w-full items-center justify-between text-left"
            >
              <div>
                <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800">
                  4. Editor Soal Asesmen &amp; Lampiran
                </h2>
                <p className="text-[11px] font-medium text-slate-500">
                  Kustomisasi butir soal asesmen awal, proses, akhir, dan lampiran LKPD.
                </p>
              </div>
              {showAssessmentEditor ? (
                <ChevronUp className="h-4 w-4 text-slate-500" />
              ) : (
                <ChevronDown className="h-4 w-4 text-slate-500" />
              )}
            </button>

            {showAssessmentEditor && (
              <div className="mt-4 space-y-3 border-t border-slate-200 pt-4">
                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Soal Asesmen Awal / Diagnostik (1 baris per soal)
                  </label>
                  <textarea
                    rows={2}
                    value={effectiveSoalAwal.join('\n')}
                    onChange={(e) =>
                      onChangeCustomOverrides({
                        ...customOverrides,
                        soal_asesmen_awal: e.target.value
                          .split('\n')
                          .map((s) => s.trim())
                          .filter(Boolean),
                      })
                    }
                    className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Soal Asesmen Proses / Formatif (1 baris per soal)
                  </label>
                  <textarea
                    rows={2}
                    value={effectiveSoalProses.join('\n')}
                    onChange={(e) =>
                      onChangeCustomOverrides({
                        ...customOverrides,
                        soal_asesmen_proses: e.target.value
                          .split('\n')
                          .map((s) => s.trim())
                          .filter(Boolean),
                      })
                    }
                    className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Soal Asesmen Akhir / Sumatif (1 baris per soal)
                  </label>
                  <textarea
                    rows={2}
                    value={effectiveSoalAkhir.join('\n')}
                    onChange={(e) =>
                      onChangeCustomOverrides({
                        ...customOverrides,
                        soal_asesmen_akhir: e.target.value
                          .split('\n')
                          .map((s) => s.trim())
                          .filter(Boolean),
                      })
                    }
                    className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>

                <div className="space-y-1.5 pt-2">
                  <label className="flex cursor-pointer items-center gap-2 text-xs font-bold text-slate-700">
                    <input
                      type="checkbox"
                      checked={includeLkpd}
                      onChange={onToggleLkpd}
                      className="h-4 w-4 rounded border-slate-300 text-blue-700"
                    />
                    <span>Sertakan Lampiran Lembar Kerja Peserta Didik (LKPD)</span>
                  </label>

                  <label className="flex cursor-pointer items-center gap-2 text-xs font-bold text-slate-700">
                    <input
                      type="checkbox"
                      checked={includeAsesmen}
                      onChange={onToggleAsesmen}
                      className="h-4 w-4 rounded border-slate-300 text-blue-700"
                    />
                    <span>Sertakan Instrumen Asesmen Awal, Proses &amp; Akhir</span>
                  </label>

                  <label className="flex cursor-pointer items-center gap-2 text-xs font-bold text-slate-700">
                    <input
                      type="checkbox"
                      checked={includeRubrik}
                      onChange={onToggleRubrik}
                      className="h-4 w-4 rounded border-slate-300 text-blue-700"
                    />
                    <span>Sertakan Rubrik 8 Dimensi Profil Lulusan</span>
                  </label>
                </div>
              </div>
            )}
          </div>

          {/* Primary Generate & Download Button */}
          <button
            type="button"
            onClick={onGenerate}
            disabled={isGenerating}
            className="clay-btn-primary flex w-full items-center justify-center gap-2.5 py-3.5 text-sm font-extrabold disabled:opacity-60"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Menyusun Dokumen {formatExtLabel}...</span>
              </>
            ) : (
              <>
                <FileDown className="h-4 w-4" />
                <span>
                  Unduh {activeService.shortTitle} ({formatExtLabel} • {paperSize})
                </span>
              </>
            )}
          </button>
        </div>

        {/* RIGHT PANEL: LIVE DOCUMENT PAPER PREVIEW (SISI KANAN FORM) */}
        <div
          className={`md:col-span-1 lg:col-span-2 xl:col-span-3 ${
            mobileViewMode === 'form' ? 'hidden md:block' : 'block'
          }`}
        >
          <div className="md:sticky md:top-20">
            {/* Preview Header Bar */}
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5">
              <div className="flex items-center gap-2">
                <Eye className="h-4 w-4 text-blue-700" />
                <span className="text-xs font-extrabold uppercase tracking-wider text-slate-800">
                  Live Document Preview — Kertas {paperSize} ({formatExtLabel})
                </span>
              </div>
              <span className="text-[11px] font-semibold text-slate-500">
                Perubahan pada form di samping langsung memperbarui dokumen ini
              </span>
            </div>

            {/* Scrollable Document Sheet Container (Anti-Select & Anti-Copy-Paste Protected) */}
            <div
              onCopy={(e) => e.preventDefault()}
              onCut={(e) => e.preventDefault()}
              onContextMenu={(e) => e.preventDefault()}
              onDragStart={(e) => e.preventDefault()}
              className="paper-sheet preview-protected relative max-h-[calc(100vh-160px)] min-w-0 max-w-full select-none overflow-auto rounded-lg p-6 sm:p-8 lg:p-10"
            >
              {/* Subtle Diagonal Preview Watermark */}
              <div
                aria-hidden="true"
                className="pointer-events-none absolute inset-0 z-20 flex items-center justify-center overflow-hidden opacity-[0.045]"
              >
                <span className="-rotate-30 whitespace-nowrap text-3xl font-black tracking-[0.25em] text-slate-900 sm:text-5xl">
                  PREVIEW DOKUMEN
                </span>
              </div>

              <div className="pointer-events-none relative z-10">
              {/* 1. KOP SEKOLAH RESMI */}
              <div className="border-b-2 border-slate-900 pb-3 text-center">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-700">
                  PEMERINTAH {(teacher.kabupaten_kota || 'KABUPATEN/KOTA').toUpperCase()} — DINAS PENDIDIKAN
                </p>
                <p className="mt-0.5 text-lg font-extrabold uppercase tracking-tight text-slate-900">
                  {teacher.nama_sekolah || 'NAMA SATUAN PENDIDIKAN'}
                </p>
                <p className="mt-0.5 text-[11px] text-slate-600">
                  NPSN: {teacher.npsn || '-'} • {teacher.kabupaten_kota || 'Kabupaten/Kota'}, Provinsi{' '}
                  {teacher.provinsi || 'Provinsi'}
                </p>
              </div>

              {/* 2. DYNAMIC DOCUMENT BODY BY SERVICE_ID */}
              {activeService.id === '03_cp_tp' && (
                <div className="mt-5 space-y-5 text-xs leading-relaxed">
                  <div className="text-center">
                    <h2 className="text-base font-extrabold uppercase text-slate-900">
                      CAPAIAN PEMBELAJARAN DAN TUJUAN PEMBELAJARAN
                    </h2>
                    <p className="font-bold uppercase text-slate-700">
                      MATA PELAJARAN {selectedSubject?.nama_mapel.toUpperCase()} — FASE {faseCode} (KELAS {kelas})
                    </p>
                  </div>

                  {/* Identitas Dokumen */}
                  <div className="paper-table-container">
                    <table className="paper-table">
                      <tbody>
                        <tr>
                          <th className="w-1/3 text-left">Mata Pelajaran</th>
                          <td>{selectedSubject?.nama_mapel}</td>
                        </tr>
                        <tr>
                          <th className="text-left">Jenjang / Fase / Kelas</th>
                          <td>
                            {jenjang} / {faseLabel} / Kelas {kelas}
                          </td>
                        </tr>
                        <tr>
                          <th className="text-left">Alokasi Waktu</th>
                          <td>
                            {selectedSubject?.total_alokasi_jp_tahun || 108} JP/Tahun ({jpPerMinggu}{' '}
                            JP/Minggu × {durasiMenitJp} Menit)
                          </td>
                        </tr>
                        <tr>
                          <th className="text-left">Dasar Hukum</th>
                          <td>
                            Kepka BSKAP Kemendikdasmen No. 046/H/KR/2025 &amp; Permendikdasmen No. 13/2025
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  {/* 1. Rasional */}
                  <div>
                    <h3 className="font-extrabold text-slate-900">
                      1. Rasional Mata Pelajaran {selectedSubject?.nama_mapel}
                    </h3>
                    <p className="mt-1 text-justify text-slate-800">
                      {selectedSubject?.rasional_bskap ||
                        `Mata pelajaran ${selectedSubject?.nama_mapel} membekali peserta didik dengan kemampuan berpikir kritis, analitis, kreatif, serta keterampilan pemecahan masalah secara sistematis sesuai perkembangan ilmu pengetahuan dan teknologi.`}
                    </p>
                  </div>

                  {/* 2. Tujuan Mata Pelajaran */}
                  <div>
                    <h3 className="font-extrabold text-slate-900">
                      2. Tujuan Mata Pelajaran {selectedSubject?.nama_mapel}
                    </h3>
                    <div className="paper-table-container">
                      <table className="paper-table mt-1.5">
                        <thead>
                          <tr>
                            <th className="w-10 text-center">No</th>
                            <th>Rumusan Tujuan Mata Pelajaran</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(selectedSubject?.tujuan_bskap
                            ? selectedSubject.tujuan_bskap
                                .split(';')
                                .map((s) => s.trim())
                                .filter(Boolean)
                            : [
                                `Menguasai konsep dan prinsip esensial ${selectedSubject?.nama_mapel} pada ${faseLabel}.`,
                                `Mengembangkan keterampilan inkuiri, penalaran kritis, dan kolaborasi dalam memecahkan persoalan kontekstual.`,
                                `Menumbuhkan karakter mandiri, kreatif, dan bertanggung jawab sesuai 8 Dimensi Profil Lulusan.`,
                              ]
                          ).map((tuj, idx) => (
                            <tr key={idx}>
                              <td className="text-center font-bold">{idx + 1}</td>
                              <td>{tuj}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* 3. Karakteristik & 4. CP Fase Berdasarkan Elemen */}
                  <div>
                    <h3 className="font-extrabold text-slate-900">
                      3. Karakteristik &amp; 4. Capaian Pembelajaran {faseLabel} Berdasarkan Elemen
                    </h3>
                    <p className="mt-1 text-slate-800">
                      {selectedSubject?.karakteristik_bskap || effectiveKarakteristikMateri}
                    </p>
                    <div className="paper-table-container">
                      <table className="paper-table mt-2">
                        <thead>
                          <tr>
                            <th className="w-1/4">Elemen</th>
                            <th>Deskripsi Capaian Pembelajaran Resmi (BSKAP 046/2025)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {officialElements.map((el, i) => (
                            <tr key={i}>
                              <td className="font-bold">{el.nama_elemen}</td>
                              <td>{el.deskripsi_cp}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* 5. Pemetaan CP & TP Per Bab */}
                  <div>
                    <h3 className="font-extrabold text-slate-900">
                      5. Pemetaan Capaian dan Tujuan Pembelajaran Semester {semester}
                    </h3>
                    {currentSemesterChapters.map((bab) => {
                      const isCurrentSelected = bab.id === selectedChapter?.id;
                      const babTps = isCurrentSelected ? activeTps : bab.tujuan_pembelajaran;
                      const babJp = isCurrentSelected ? currentAlokasiJp : bab.alokasi_jp;
                      return (
                        <div key={bab.id} className="mt-3">
                          <p className="font-bold text-blue-900">
                            BAB {bab.nomor_bab}: {bab.judul_bab.toUpperCase()} (Semester {bab.semester})
                          </p>
                          <div className="paper-table-container">
                            <table className="paper-table mt-1">
                              <thead>
                                <tr>
                                  <th className="w-1/4">KATEGORI</th>
                                  <th>RUMUSAN</th>
                                </tr>
                              </thead>
                              <tbody>
                                <tr>
                                  <td className="font-bold">Elemen</td>
                                  <td>{bab.elemen_cp || officialElements[0]?.nama_elemen}</td>
                                </tr>
                                <tr>
                                  <td className="font-bold">Kalimat CP</td>
                                  <td>
                                    Peserta didik mampu menguasai konsep {bab.judul_bab} pada elemen{' '}
                                    {bab.elemen_cp || officialElements[0]?.nama_elemen} serta
                                    menerapkannya secara kontekstual.
                                  </td>
                                </tr>
                                <tr>
                                  <td className="font-bold">Tujuan Pembelajaran</td>
                                  <td>
                                    <ol className="list-decimal pl-4 space-y-1">
                                      {babTps.map((t, idx) => (
                                        <li key={idx}>
                                          <strong>[{t.code}]</strong> {t.deskripsi} ({t.alokasi_jp} JP)
                                        </li>
                                      ))}
                                    </ol>
                                  </td>
                                </tr>
                                <tr>
                                  <td className="font-bold">Alokasi Waktu</td>
                                  <td className="font-bold">{babJp} Jam Pelajaran (JP)</td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {activeService.id === '04_atp' && (
                <div className="mt-5 space-y-5 text-xs leading-relaxed">
                  <div className="text-center">
                    <h2 className="text-base font-extrabold uppercase text-slate-900">
                      ALUR TUJUAN PEMBELAJARAN (ATP)
                    </h2>
                    <p className="font-bold uppercase text-slate-700">
                      MATA PELAJARAN {selectedSubject?.nama_mapel.toUpperCase()} — FASE {faseCode} KELAS {kelas}
                    </p>
                  </div>

                  {/* Capaian Pembelajaran Fase Berdasarkan Elemen */}
                  <div>
                    <h3 className="font-extrabold uppercase text-slate-900">
                      CAPAIAN PEMBELAJARAN FASE {faseCode} BERDASARKAN ELEMEN
                    </h3>
                    <div className="paper-table-container">
                      <table className="paper-table mt-1.5">
                        <thead>
                          <tr>
                            <th className="w-1/4">Elemen</th>
                            <th>Capaian Pembelajaran</th>
                          </tr>
                        </thead>
                        <tbody>
                          {officialElements.map((el, i) => (
                            <tr key={i}>
                              <td className="font-bold">{el.nama_elemen}</td>
                              <td>{el.deskripsi_cp}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Per-Bab Structured Block Table matching ATP_-_Informatika_11.docx */}
                  <div>
                    <h3 className="font-extrabold uppercase text-slate-900">
                      RINCIAN ALUR TUJUAN PEMBELAJARAN SEMESTER {semester}
                    </h3>
                    {currentSemesterChapters.map((bab) => {
                      const isCurrentSelected = bab.id === selectedChapter?.id;
                      const babTps = isCurrentSelected ? activeTps : bab.tujuan_pembelajaran;
                      const babJp = isCurrentSelected ? currentAlokasiJp : bab.alokasi_jp;
                      return (
                        <div key={bab.id} className="mt-3">
                          <div className="paper-table-container">
                            <table className="paper-table">
                              <thead>
                                <tr>
                                  <th colSpan={2} className="text-left">
                                    BAB {bab.nomor_bab}: {bab.judul_bab.toUpperCase()} (SEMESTER {bab.semester})
                                  </th>
                                </tr>
                              </thead>
                              <tbody>
                                <tr>
                                  <td className="w-1/3 font-bold">Elemen</td>
                                  <td>{bab.elemen_cp || officialElements[0]?.nama_elemen}</td>
                                </tr>
                                <tr>
                                  <td className="font-bold">Capaian Pembelajaran Pertahun</td>
                                  <td>
                                    Memahami, menerapkan, dan mengevaluasi konsep {bab.judul_bab} pada{' '}
                                    {selectedSubject?.nama_mapel} Kelas {kelas}.
                                  </td>
                                </tr>
                                <tr>
                                  <td className="font-bold">
                                    Fase {faseCode} / Alur Tujuan Pembelajaran
                                  </td>
                                  <td>
                                    <ol className="list-decimal pl-4 space-y-1">
                                      {babTps.map((t, i) => (
                                        <li key={i}>
                                          <strong>{t.code}:</strong> {t.deskripsi} ({t.alokasi_jp} JP)
                                        </li>
                                      ))}
                                    </ol>
                                  </td>
                                </tr>
                                <tr>
                                  <td className="font-bold">Jumlah Jam</td>
                                  <td className="font-bold">
                                    {babJp} JP ({Math.max(1, Math.round(babJp / jpPerMinggu))} Pertemuan)
                                  </td>
                                </tr>
                                <tr>
                                  <td className="font-bold">Kata Kunci</td>
                                  <td>
                                    {bab.judul_bab}, {bab.elemen_cp || 'Konsep Inti'}, Analisis Kontekstual
                                  </td>
                                </tr>
                                <tr>
                                  <td className="font-bold">Topik / Konten Inti</td>
                                  <td>
                                    {isCurrentSelected ? effectiveTopikKontekstual : bab.judul_bab}
                                  </td>
                                </tr>
                                <tr>
                                  <td className="font-bold">Glosarium</td>
                                  <td>
                                    {bab.judul_bab}: Lingkup kompetensi utama pada mata pelajaran{' '}
                                    {selectedSubject?.nama_mapel} Kelas {kelas}.
                                  </td>
                                </tr>
                                <tr>
                                  <td className="font-bold">Dimensi Profil Lulusan</td>
                                  <td>{(bab.dimensi_profil_lulusan || activeDimensions).join(', ')}</td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Rasional & Catatan ATP */}
                  <div className="space-y-2 border-t border-slate-300 pt-3">
                    <p>
                      <strong>Rasional Penyusunan Alur Tujuan Pembelajaran:</strong> Penyusunan ATP{' '}
                      {selectedSubject?.nama_mapel} Kelas {kelas} dilakukan secara berjenjang dari
                      kompetensi fondasi menuju aplikasi kontekstual dan evaluasi reflektif.
                    </p>
                    {customOverrides.catatan_khusus && (
                      <p>
                        <strong>Catatan Khusus Penggunaan ATP:</strong>{' '}
                        {customOverrides.catatan_khusus}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {activeService.id === '08_modul_ajar' && (
                <div className="mt-5 space-y-5 text-xs leading-relaxed">
                  <div className="text-center">
                    <h2 className="text-base font-extrabold uppercase text-slate-900">
                      MODUL AJAR DEEP LEARNING
                    </h2>
                    <p className="font-bold uppercase text-slate-700">
                      {selectedSubject?.nama_mapel.toUpperCase()} — BAB {selectedChapter?.nomor_bab || 1}:{' '}
                      {(selectedChapter?.judul_bab || '').toUpperCase()}
                    </p>
                  </div>

                  {/* A. Identitas Modul */}
                  <div>
                    <h3 className="font-extrabold uppercase text-slate-900">A. Identitas Modul</h3>
                    <div className="paper-table-container">
                      <table className="paper-table mt-1.5">
                        <tbody>
                          <tr>
                            <th className="w-1/3 text-left">Nama Penyusun</th>
                            <td>
                              {teacher.nama_guru || 'Nama Guru Anda'} (NIP. {teacher.nip_guru || '-'})
                            </td>
                          </tr>
                          <tr>
                            <th className="text-left">Institusi / Sekolah</th>
                            <td>{teacher.nama_sekolah || 'Nama Sekolah Anda'}</td>
                          </tr>
                          <tr>
                            <th className="text-left">Tahun Penyusunan / Semester</th>
                            <td>
                              Tahun Ajaran 2025/2026 / Semester {semester} (
                              {semester === 1 ? 'Ganjil' : 'Genap'})
                            </td>
                          </tr>
                          <tr>
                            <th className="text-left">Jenjang / Fase / Kelas</th>
                            <td>
                              {jenjang} / {faseLabel} / Kelas {kelas}
                            </td>
                          </tr>
                          <tr>
                            <th className="text-left">Mata Pelajaran</th>
                            <td>{selectedSubject?.nama_mapel}</td>
                          </tr>
                          <tr>
                            <th className="text-left">Bab / Materi Pokok</th>
                            <td>
                              Bab {selectedChapter?.nomor_bab || 1}: {selectedChapter?.judul_bab}
                            </td>
                          </tr>
                          <tr>
                            <th className="text-left">Alokasi Waktu</th>
                            <td>
                              {currentAlokasiJp} JP ({pertemuanCount} Pertemuan × {jpPerMinggu} JP @{' '}
                              {durasiMenitJp} Menit)
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* B. Identifikasi Kesiapan Peserta Didik & C. Karakteristik Materi */}
                  <div className="space-y-2.5">
                    <div>
                      <h3 className="font-extrabold uppercase text-slate-900">
                        B. Identifikasi Kesiapan Peserta Didik
                      </h3>
                      <p className="mt-1 text-slate-800">{effectiveKesiapanMurid}</p>
                    </div>
                    <div>
                      <h3 className="font-extrabold uppercase text-slate-900">
                        C. Karakteristik Materi Pelajaran
                      </h3>
                      <p className="mt-1 text-slate-800">{effectiveKarakteristikMateri}</p>
                    </div>
                  </div>

                  {/* D. Dimensi Profil Lulusan */}
                  <div>
                    <h3 className="font-extrabold uppercase text-slate-900">
                      D. Dimensi Profil Lulusan Pembelajaran
                    </h3>
                    <div className="paper-table-container">
                      <table className="paper-table mt-1.5">
                        <thead>
                          <tr>
                            <th className="w-1/3">Dimensi Profil Lulusan</th>
                            <th>Implementasi pada Pembelajaran Bab Ini</th>
                          </tr>
                        </thead>
                        <tbody>
                          {activeDimensions.map((dim, i) => (
                            <tr key={i}>
                              <td className="font-bold">{dim}</td>
                              <td>
                                Dikembangkan melalui aktivitas diskusi, eksplorasi konsep{' '}
                                {selectedChapter?.judul_bab}, dan refleksi pemecahan masalah.
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* DESAIN PEMBELAJARAN */}
                  <div className="space-y-3 border-t-2 border-slate-800 pt-3">
                    <h3 className="text-sm font-extrabold uppercase text-slate-900">
                      DESAIN PEMBELAJARAN
                    </h3>

                    <div className="paper-table-container">
                      <table className="paper-table">
                        <tbody>
                          <tr>
                            <th className="w-1/3 text-left">A. Capaian Pembelajaran (CP)</th>
                            <td>
                              <strong>
                                Elemen {selectedChapter?.elemen_cp || officialElements[0]?.nama_elemen}:
                              </strong>{' '}
                              {officialElements[0]?.deskripsi_cp}
                            </td>
                          </tr>
                          <tr>
                            <th className="text-left">B. Lintas Disiplin Ilmu</th>
                            <td>{effectiveLintasDisiplin}</td>
                          </tr>
                          <tr>
                            <th className="text-left">C. Tujuan Pembelajaran (TP)</th>
                            <td>
                              <ol className="list-decimal pl-4 space-y-1">
                                {activeTps.map((tp, idx) => (
                                  <li key={idx}>
                                    <strong>Pertemuan {idx + 1} [{tp.code}]:</strong> {tp.deskripsi} (
                                    {tp.alokasi_jp} JP)
                                  </li>
                                ))}
                              </ol>
                            </td>
                          </tr>
                          <tr>
                            <th className="text-left">D. Topik Pembelajaran Kontekstual</th>
                            <td>{effectiveTopikKontekstual}</td>
                          </tr>
                          <tr>
                            <th className="text-left">E. Kerangka Pembelajaran</th>
                            <td>
                              <p>
                                <strong>Model Pedagogis:</strong> {modelPembelajaran}
                              </p>
                              <p className="mt-1">
                                <strong>Pertanyaan Pemantik:</strong>{' '}
                                {effectivePemantik.join(' | ')}
                              </p>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>

                    {/* F. Langkah-Langkah Pembelajaran Berdiferensiasi */}
                    <div>
                      <h4 className="font-extrabold uppercase text-slate-900">
                        F. Langkah-Langkah Pembelajaran Berdiferensiasi (Pendekatan Deep Learning 3M)
                      </h4>
                      {activeTps.map((tp, idx) => (
                        <div key={idx} className="paper-table-container">
                          <table className="paper-table mt-2">
                            <thead>
                              <tr>
                                <th colSpan={2} className="text-left">
                                  PERTEMUAN {idx + 1} — Fokus TP: [{tp.code}] {tp.deskripsi} (
                                  {tp.alokasi_jp} JP)
                                </th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr>
                                <td className="w-1/4 font-bold">1. Kegiatan Pendahuluan (15%)</td>
                                <td>
                                  Guru membuka kelas dengan salam, doa, presensi, apersepsi mengaitkan
                                  pengalaman nyata siswa dengan topik {selectedChapter?.judul_bab},
                                  serta menyampaikan pertanyaan pemantik:{' '}
                                  <em>&ldquo;{effectivePemantik[idx % effectivePemantik.length]}&rdquo;</em>.
                                </td>
                              </tr>
                              <tr>
                                <td className="font-bold">
                                  2. Kegiatan Inti — Memahami, Mengaplikasi, Merefleksi (70%)
                                </td>
                                <td>
                                  <ul className="list-disc pl-4 space-y-1">
                                    <li>
                                      <strong>Memahami (Mindful Learning):</strong> Peserta didik
                                      mengeksplorasi konsep dan literatur terkait {tp.deskripsi}.
                                    </li>
                                    <li>
                                      <strong>Mengaplikasi (Meaningful Learning):</strong> Peserta
                                      didik bekerja dalam kelompok mengerjakan studi kasus / LKPD
                                      tentang {selectedChapter?.judul_bab}.
                                    </li>
                                    <li>
                                      <strong>Merefleksi (Joyful Learning):</strong> Kelompok
                                      mempresentasikan hasil karya dan melakukan evaluasi pemahaman
                                      bersama guru.
                                    </li>
                                  </ul>
                                </td>
                              </tr>
                              <tr>
                                <td className="font-bold">3. Kegiatan Penutup (15%)</td>
                                <td>
                                  Peserta didik bersama guru menyimpulkan poin penting pertemuan{' '}
                                  {idx + 1}, melakukan refleksi singkat, dan menerima informasi materi
                                  pertemuan berikutnya.
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      ))}
                    </div>

                    {/* G. Asesmen Pembelajaran */}
                    {includeAsesmen && (
                      <div>
                        <h4 className="font-extrabold uppercase text-slate-900">
                          G. Asesmen Pembelajaran &amp; Butir Soal
                        </h4>
                        <div className="paper-table-container">
                          <table className="paper-table mt-1.5">
                            <thead>
                              <tr>
                                <th className="w-1/4">Jenis Asesmen</th>
                                <th>Teknik &amp; Butir Soal Instrumen</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr>
                                <td className="font-bold">1. Asesmen Awal (Diagnostik)</td>
                                <td>
                                  <p className="font-semibold">Soal Asesmen Awal:</p>
                                  <ol className="list-decimal pl-4">
                                    {effectiveSoalAwal.map((s, i) => (
                                      <li key={i}>{s}</li>
                                    ))}
                                  </ol>
                                </td>
                              </tr>
                              <tr>
                                <td className="font-bold">2. Asesmen Proses (Formatif)</td>
                                <td>
                                  <p className="font-semibold">Soal / Tugas Asesmen Proses:</p>
                                  <ol className="list-decimal pl-4">
                                    {effectiveSoalProses.map((s, i) => (
                                      <li key={i}>{s}</li>
                                    ))}
                                  </ol>
                                </td>
                              </tr>
                              <tr>
                                <td className="font-bold">3. Asesmen Akhir (Sumatif)</td>
                                <td>
                                  <p className="font-semibold">Soal Asesmen Akhir Bab:</p>
                                  <ol className="list-decimal pl-4">
                                    {effectiveSoalAkhir.map((s, i) => (
                                      <li key={i}>{s}</li>
                                    ))}
                                  </ol>
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeService.id === '05_prota' && (
                <div className="mt-5 space-y-5 text-xs leading-relaxed">
                  <div className="text-center">
                    <h2 className="text-base font-extrabold uppercase text-slate-900">
                      PROGRAM TAHUNAN (PROTA)
                    </h2>
                    <p className="font-bold uppercase text-slate-700">
                      MATA PELAJARAN {selectedSubject?.nama_mapel.toUpperCase()} — KELAS {kelas} (
                      {faseLabel}) TAHUN AJARAN 2025/2026
                    </p>
                  </div>

                  {/* CP Fase Berdasarkan Elemen */}
                  <div>
                    <h3 className="font-extrabold uppercase text-slate-900">
                      CAPAIAN PEMBELAJARAN FASE {faseCode} BERDASARKAN ELEMEN
                    </h3>
                    <div className="paper-table-container">
                      <table className="paper-table mt-1.5">
                        <thead>
                          <tr>
                            <th className="w-1/4">Elemen</th>
                            <th>Capaian Pembelajaran</th>
                          </tr>
                        </thead>
                        <tbody>
                          {officialElements.map((el, i) => (
                            <tr key={i}>
                              <td className="font-bold">{el.nama_elemen}</td>
                              <td>{el.deskripsi_cp}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Tabel Distribusi Alokasi Waktu Tahunan */}
                  <div>
                    <h3 className="font-extrabold uppercase text-slate-900">
                      DISTRIBUSI ALOKASI WAKTU TAHUNAN (SEMESTER 1 &amp; SEMESTER 2)
                    </h3>
                    <div className="paper-table-container">
                      <table className="paper-table mt-1.5">
                        <thead>
                          <tr>
                            <th className="w-24 text-center">SEMESTER</th>
                            <th className="w-12 text-center">NO</th>
                            <th>MATERI POKOK / JUDUL BAB &amp; TUJUAN PEMBELAJARAN</th>
                            <th className="w-24 text-center">ALOKASI (JP)</th>
                            <th className="w-28 text-center">KETERANGAN</th>
                          </tr>
                        </thead>
                        <tbody>
                          {allSubjectChapters.map((bab, idx) => {
                            const isCurrent = bab.id === selectedChapter?.id;
                            const babJp = isCurrent ? currentAlokasiJp : bab.alokasi_jp;
                            const babTps = isCurrent ? activeTps : bab.tujuan_pembelajaran;
                            return (
                              <tr key={bab.id}>
                                <td className="text-center font-bold">
                                  SEMESTER {bab.semester}
                                </td>
                                <td className="text-center font-bold">{idx + 1}</td>
                                <td>
                                  <p className="font-bold">
                                    Bab {bab.nomor_bab}: {bab.judul_bab}
                                  </p>
                                  <ul className="mt-1 list-disc pl-4 text-[11px] text-slate-700">
                                    {babTps.map((t, i) => (
                                      <li key={i}>
                                        [{t.code}] {t.deskripsi} ({t.alokasi_jp} JP)
                                      </li>
                                    ))}
                                  </ul>
                                </td>
                                <td className="text-center font-bold">{babJp} JP</td>
                                <td className="text-center">
                                  {Math.max(1, Math.round(babJp / jpPerMinggu))} Pertemuan
                                </td>
                              </tr>
                            );
                          })}
                          <tr>
                            <td colSpan={3} className="text-right font-bold">
                              Cadangan Jam Pelajaran
                            </td>
                            <td className="text-center font-bold">
                              {customOverrides.cadangan_jp ?? 0} JP
                            </td>
                            <td className="text-center">Pengayaan / STS / SAS</td>
                          </tr>
                          <tr className="bg-slate-100">
                            <td colSpan={3} className="text-right font-extrabold">
                              Jumlah Jam Pelajaran Tahunan
                            </td>
                            <td className="text-center font-extrabold">
                              {allSubjectChapters.reduce(
                                (acc, b) =>
                                  acc +
                                  (b.id === selectedChapter?.id ? currentAlokasiJp : b.alokasi_jp),
                                0
                              ) + (customOverrides.cadangan_jp ?? 0)}{' '}
                              JP
                            </td>
                            <td className="text-center font-bold">1 Tahun Ajaran</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {activeService.id === '06_promes' && (
                <div className="mt-5 space-y-5 text-xs leading-relaxed">
                  <div className="text-center">
                    <h2 className="text-base font-extrabold uppercase text-slate-900">
                      PROGRAM SEMESTER (PROMES) — SEMESTER {semester} (
                      {semester === 1 ? 'GANJIL' : 'GENAP'})
                    </h2>
                    <p className="font-bold uppercase text-slate-700">
                      MATA PELAJARAN {selectedSubject?.nama_mapel.toUpperCase()} — KELAS {kelas} (
                      {faseLabel}) TAHUN AJARAN 2025/2026
                    </p>
                  </div>

                  {/* CP Fase Berdasarkan Elemen */}
                  <div>
                    <h3 className="font-extrabold uppercase text-slate-900">
                      CAPAIAN PEMBELAJARAN FASE {faseCode} BERDASARKAN ELEMEN
                    </h3>
                    <div className="paper-table-container">
                      <table className="paper-table mt-1.5">
                        <thead>
                          <tr>
                            <th className="w-1/4">Elemen</th>
                            <th>Capaian Pembelajaran</th>
                          </tr>
                        </thead>
                        <tbody>
                          {officialElements.map((el, i) => (
                            <tr key={i}>
                              <td className="font-bold">{el.nama_elemen}</td>
                              <td>{el.deskripsi_cp}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Matriks 6 Bulan Semester */}
                  <div className="paper-table-container">
                    <h3 className="font-extrabold uppercase text-slate-900">
                      MATRIKS DISTRIBUSI MINGGU EFEKTIF SEMESTER {semester}
                    </h3>
                    <table className="paper-table mt-1.5">
                      <thead>
                        <tr>
                          <th className="w-10 text-center">NO</th>
                          <th>BAB / TUJUAN PEMBELAJARAN (TP)</th>
                          <th className="w-14 text-center">JP</th>
                          {monthLabels.map((m) => (
                            <th key={m} className="w-12 text-center">
                              {m}
                            </th>
                          ))}
                          <th className="w-20 text-center">KET</th>
                        </tr>
                      </thead>
                      <tbody>
                        {currentSemesterChapters.map((bab, bIdx) => {
                          const isCurrent = bab.id === selectedChapter?.id;
                          const babTps = isCurrent ? activeTps : bab.tujuan_pembelajaran;
                          const babJp = isCurrent ? currentAlokasiJp : bab.alokasi_jp;
                          return (
                            <React.Fragment key={bab.id}>
                              <tr className="bg-slate-100 font-bold">
                                <td className="text-center">{bIdx + 1}</td>
                                <td>
                                  BAB {bab.nomor_bab}: {bab.judul_bab.toUpperCase()}
                                </td>
                                <td className="text-center">{babJp}</td>
                                {monthLabels.map((m) => (
                                  <td key={m} className="text-center" />
                                ))}
                                <td className="text-center">Intrakurikuler</td>
                              </tr>
                              {babTps.map((tp, tIdx) => {
                                const targetMonthIdx = (bIdx * 2 + tIdx) % 6;
                                return (
                                  <tr key={`${bab.id}-${tIdx}`}>
                                    <td className="text-center text-slate-500">
                                      {bIdx + 1}.{tIdx + 1}
                                    </td>
                                    <td>
                                      <strong>[{tp.code}]</strong> {tp.deskripsi}
                                    </td>
                                    <td className="text-center font-semibold">{tp.alokasi_jp}</td>
                                    {monthLabels.map((m, mIdx) => (
                                      <td
                                        key={m}
                                        className={`text-center font-bold ${
                                          mIdx === targetMonthIdx
                                            ? 'bg-blue-50 text-blue-800'
                                            : 'text-slate-300'
                                        }`}
                                      >
                                        {mIdx === targetMonthIdx ? tp.alokasi_jp : '-'}
                                      </td>
                                    ))}
                                    <td className="text-center text-[11px]">TM</td>
                                  </tr>
                                );
                              })}
                            </React.Fragment>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {activeService.id === '07_kktp' && (
                <div className="mt-5 space-y-5 text-xs leading-relaxed">
                  <div className="text-center">
                    <h2 className="text-base font-extrabold uppercase text-slate-900">
                      KRITERIA KETERCAPAIAN TUJUAN PEMBELAJARAN (KKTP)
                    </h2>
                    <p className="font-bold uppercase text-slate-700">
                      MATA PELAJARAN {selectedSubject?.nama_mapel.toUpperCase()} — FASE {selectedSubject?.fase} (KELAS {selectedSubject?.kelas})
                    </p>
                  </div>

                  <div>
                    <h3 className="font-extrabold uppercase text-slate-900">Identitas Dokumen</h3>
                    <div className="paper-table-container">
                      <table className="paper-table mt-1.5">
                        <tbody>
                          <tr>
                            <th className="w-1/3 text-left">Mata Pelajaran</th>
                            <td>{selectedSubject?.nama_mapel}</td>
                          </tr>
                          <tr>
                            <th className="text-left">Jenjang / Kelas / Fase</th>
                            <td>
                              {selectedSubject?.jenjang} / Kelas {selectedSubject?.kelas} / Fase {selectedSubject?.fase}
                            </td>
                          </tr>
                          <tr>
                            <th className="text-left">Semester / Tahun Ajaran</th>
                            <td>Semester {semester} / 2025/2026</td>
                          </tr>
                          <tr>
                            <th className="text-left">Materi / Bab</th>
                            <td>{selectedChapter?.judul_bab || 'Semua Bab'}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-extrabold uppercase text-slate-900">
                      A. Skala Interval Nilai KKTP (4 Interval — PPA Revisi 2025)
                    </h3>
                    <div className="paper-table-container">
                      <table className="paper-table mt-1.5">
                        <thead>
                          <tr>
                            <th className="w-24 text-center">Interval</th>
                            <th className="w-40 text-left">Kriteria</th>
                            <th className="text-left">Tindak Lanjut / Intervensi</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td className="text-center font-bold">0 - 40%</td>
                            <td>Belum Mencapai</td>
                            <td>Remedial di seluruh bagian</td>
                          </tr>
                          <tr>
                            <td className="text-center font-bold">41 - 65%</td>
                            <td>Belum Mencapai Ketuntasan</td>
                            <td>Remedial di bagian yang diperlukan</td>
                          </tr>
                          <tr>
                            <td className="text-center font-bold">66 - 85%</td>
                            <td>Sudah Mencapai Ketuntasan</td>
                            <td>Tidak perlu remedial</td>
                          </tr>
                          <tr>
                            <td className="text-center font-bold">86 - 100%</td>
                            <td>Sudah Mencapai Ketuntasan</td>
                            <td>Perlu pengayaan atau tantangan lebih</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-extrabold uppercase text-slate-900">
                      B. Rubrik Ketercapaian Tujuan Pembelajaran (TP)
                    </h3>
                    <div className="paper-table-container">
                      <table className="paper-table mt-1.5">
                        <thead>
                          <tr>
                            <th className="w-20 text-center">Kode TP</th>
                            <th className="text-left">Tujuan Pembelajaran & Indikator Ketercapaian</th>
                            <th className="w-16 text-center">JP</th>
                          </tr>
                        </thead>
                        <tbody>
                          {activeTps.map((tp, idx) => (
                            <tr key={`${tp.code}-${idx}`}>
                              <td className="text-center font-bold">{tp.code}</td>
                              <td>{tp.deskripsi}</td>
                              <td className="text-center">{tp.alokasi_jp}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {activeService.id === '09_lkpd' && (
                <div className="mt-5 space-y-5 text-xs leading-relaxed">
                  <div className="text-center">
                    <h2 className="text-base font-extrabold uppercase text-slate-900">
                      LEMBAR KERJA PESERTA DIDIK (LKPD) MANDIRI
                    </h2>
                    <p className="font-bold uppercase text-slate-700">
                      MATA PELAJARAN {selectedSubject?.nama_mapel.toUpperCase()} — FASE {selectedSubject?.fase} (KELAS {selectedSubject?.kelas})
                    </p>
                  </div>

                  <div>
                    <h3 className="font-extrabold uppercase text-slate-900">Identitas Peserta Didik</h3>
                    <div className="paper-table-container">
                      <table className="paper-table mt-1.5">
                        <tbody>
                          <tr>
                            <th className="w-1/3 text-left">Nama Peserta Didik</th>
                            <td>............................................................</td>
                          </tr>
                          <tr>
                            <th className="text-left">Kelas / No. Absen</th>
                            <td>Kelas {selectedSubject?.kelas} / ........</td>
                          </tr>
                          <tr>
                            <th className="text-left">Topik / Materi Pokok</th>
                            <td>{selectedChapter?.judul_bab || selectedSubject?.nama_mapel}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-extrabold uppercase text-slate-900">A. Tujuan Pembelajaran</h3>
                    <ul className="mt-1.5 list-disc space-y-1 pl-5">
                      {activeTps.map((tp, idx) => (
                        <li key={`${tp.code}-${idx}`}>
                          <strong>[{tp.code}]</strong> {tp.deskripsi}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h3 className="font-extrabold uppercase text-slate-900">
                      B. Langkah Aktivitas Pembelajaran Mendalam (3M)
                    </h3>
                    <div className="paper-table-container">
                      <table className="paper-table mt-1.5">
                        <thead>
                          <tr>
                            <th className="w-32 text-left">Tahap 3M</th>
                            <th className="text-left">Panduan Aktivitas Mandiri / Kelompok</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td className="font-bold">1. Memahami</td>
                            <td>
                              {selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.memahami ||
                                `Membaca dan memahami konsep inti pada materi ${selectedChapter?.judul_bab || selectedSubject?.nama_mapel}.`}
                            </td>
                          </tr>
                          <tr>
                            <td className="font-bold">2. Mengaplikasi</td>
                            <td>
                              {selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.mengaplikasi ||
                                'Mengerjakan studi kasus atau praktik pemecahan masalah secara terstruktur.'}
                            </td>
                          </tr>
                          <tr>
                            <td className="font-bold">3. Merefleksi</td>
                            <td>
                              {selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.merefleksi ||
                                'Menuliskan kesimpulan dan refleksi pemahaman diri setelah aktivitas.'}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-extrabold uppercase text-slate-900">C. Soal Latihan / Tugas Mandiri</h3>
                    <ol className="mt-1.5 list-decimal space-y-1.5 pl-5">
                      <li>
                        Jelaskan konsep utama yang dipelajari pada topik{' '}
                        {selectedChapter?.judul_bab || selectedSubject?.nama_mapel} dengan bahasamu sendiri!
                      </li>
                      <li>
                        Berikan satu contoh penerapan nyata dari materi ini dalam kehidupan sehari-hari!
                      </li>
                      <li>
                        Apa bagian yang paling menantang dan bagaimana kamu menyelesaikannya?
                      </li>
                    </ol>
                  </div>
                </div>
              )}

              {/* 3. LEMBAR PENGESAHAN RESMI */}
              <div className="mt-8 grid grid-cols-2 gap-4 border-t border-slate-300 pt-5 text-xs">
                <div>
                  <p>Mengetahui,</p>
                  <p className="font-bold">Kepala {teacher.nama_sekolah || 'Sekolah'}</p>
                  <div className="h-14" />
                  <p className="font-extrabold underline">
                    {teacher.nama_kepala_sekolah || 'Nama Kepala Sekolah'}
                  </p>
                  <p className="text-[11px] text-slate-600">
                    NIP. {teacher.nip_kepala_sekolah || '-'}
                  </p>
                </div>

                <div className="text-right sm:text-left sm:pl-12">
                  <p>{teacher.kabupaten_kota || 'Kota/Kabupaten'}, Tahun Ajaran 2025/2026</p>
                  <p className="font-bold">Guru Mata Pelajaran</p>
                  <div className="h-14" />
                  <p className="font-extrabold underline">{teacher.nama_guru || 'Nama Guru Anda'}</p>
                  <p className="text-[11px] text-slate-600">NIP. {teacher.nip_guru || '-'}</p>
                </div>
              </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modal Tambah Bab Kustom */}
      <AddChapterModal
        isOpen={isAddChapterModalOpen}
        subject={selectedSubject}
        existingChapters={allSubjectChapters}
        activeSemester={semester}
        onClose={() => setIsAddChapterModalOpen(false)}
        onSuccess={(newCh) => {
          onChapterCreated(newCh);
        }}
      />
    </section>
  );
};
