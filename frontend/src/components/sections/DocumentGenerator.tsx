import React, { useState, useEffect } from 'react';
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
  Users,
  FileSpreadsheet,
  CheckCircle2,
  Calculator,
  ArrowUp,
  ArrowDown,
  Layers,
  Save,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RefreshCw,
} from 'lucide-react';
import {
  ChapterTopic,
  CurriculumSubject,
  CustomChapterItem,
  CustomCpElementItem,
  CustomDocumentOverrides,
  CustomRubrikDplItem,
  CustomTpItem,
  DocumentGenerateRequest,
  GenerationMode,
  Jenjang,
  OutputFormat,
  PaperSize,
  ServiceCatalogItem,
  ServiceId,
  StudentOverrideItem,
  TeacherProfile,
} from '../../types';
import { apiClient } from '../../services/api';
import { WordPagePaginator, ZoomSetting } from '../preview/WordPagePaginator';
import { PdfCanvasPreview } from '../preview/PdfCanvasPreview';
import { getServiceOrientation } from '../preview/paperDimensions';
import {
  CORE_SERVICES,
  FASE_BY_GRADE,
  GRADES_BY_JENJANG,
  PEDAGOGICAL_MODELS,
  DELAPAN_DIMENSI_PROFIL_LULUSAN,
} from '../../constants/services';
import { AddChapterModal } from '../modals/AddChapterModal';
import { ChapterEditorModal } from '../curriculum/ChapterEditorModal';
import { CpElementEditorModal } from '../curriculum/CpElementEditorModal';
import { QuestionBuilderSection } from '../curriculum/QuestionBuilderSection';
import { JurnalEditorSection } from '../curriculum/JurnalEditorSection';
import { CurriculumPlanningPreviews } from '../preview/services/CurriculumPlanningPreviews';
import { AssessmentLkpdPreviews } from '../preview/services/AssessmentLkpdPreviews';
import { ClassroomTrackingPreviews } from '../preview/services/ClassroomTrackingPreviews';
import {
  getCustomCurriculum,
  saveCustomCurriculum,
  resetCustomCurriculum,
  convertChapterTopicsToCustom,
  getCustomCpElements,
  saveCustomCpElements,
  resetCustomCpElements,
} from '../../services/curriculumStorage';
import {
  getClassrooms,
  getActiveClassroom,
  setActiveClassroomId,
  ClassroomRombel,
  StudentItem,
} from '../../services/classroomStorage';

interface DocumentGeneratorProps {
  activeService: ServiceCatalogItem;
  generationMode: GenerationMode;
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
  onOpenClassroomModal?: () => void;
  onChangeGenerationMode?: (mode: GenerationMode) => void;
  onBackToCatalog: () => void;
  onGenerate: () => void;
  onChapterCreated: (newChapter: ChapterTopic) => void;
}

export const DocumentGenerator: React.FC<DocumentGeneratorProps> = ({
  activeService,
  generationMode = 'template',
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
  onOpenClassroomModal,
  onChangeGenerationMode,
  onBackToCatalog,
  onGenerate,
  onChapterCreated,
}) => {
  const [mobileViewMode, setMobileViewMode] = useState<'form' | 'preview'>('form');
  const [showPedagogicalEditor, setShowPedagogicalEditor] = useState<boolean>(true);
  const [showAssessmentEditor, setShowAssessmentEditor] = useState<boolean>(true);
  const [isAddChapterModalOpen, setIsAddChapterModalOpen] = useState<boolean>(false);

  // Initialize or read custom rubrik dpl
  const effectiveRubrikDpl: CustomRubrikDplItem[] =
    customOverrides.custom_rubrik_dpl && customOverrides.custom_rubrik_dpl.length > 0
      ? customOverrides.custom_rubrik_dpl
      : DELAPAN_DIMENSI_PROFIL_LULUSAN.map((d, i) => ({
          no: i + 1,
          nama_dimensi: d.nama,
          indikator: d.indikator,
          is_active: true,
        }));

  const handleUpdateDplIndicator = (index: number, newIndikator: string) => {
    const updated = effectiveRubrikDpl.map((item, idx) =>
      idx === index ? { ...item, indikator: newIndikator } : item
    );
    onChangeCustomOverrides({
      ...customOverrides,
      custom_rubrik_dpl: updated,
    });
  };

  const handleToggleDplActive = (index: number) => {
    const updated = effectiveRubrikDpl.map((item, idx) =>
      idx === index ? { ...item, is_active: !item.is_active } : item
    );
    onChangeCustomOverrides({
      ...customOverrides,
      custom_rubrik_dpl: updated,
    });
  };

  const handleResetDplDefault = () => {
    const standardDpl: CustomRubrikDplItem[] = DELAPAN_DIMENSI_PROFIL_LULUSAN.map((d, i) => ({
      no: i + 1,
      nama_dimensi: d.nama,
      indikator: d.indikator,
      is_active: true,
    }));
    onChangeCustomOverrides({
      ...customOverrides,
      custom_rubrik_dpl: standardDpl,
    });
  };

  const activeDplList = effectiveRubrikDpl.filter((d) => d.is_active);

  // Dual-Mode & Chapter Management State (Alternatif 1 + 4 & Crash-Safe Cache)
  const [isChapterEditorOpen, setIsChapterEditorOpen] = useState<boolean>(false);
  const [chapterEditing, setChapterEditing] = useState<CustomChapterItem | null>(null);
  const [isCpEditorOpen, setIsCpEditorOpen] = useState<boolean>(false);
  const [cpEditing, setCpEditing] = useState<CustomCpElementItem | null>(null);
  const [justSavedNotification, setJustSavedNotification] = useState<boolean>(false);

  // Load and Synchronize Custom Chapters & CP Elements across services for the active subject
  useEffect(() => {
    if (!selectedSubject) return;

    // 1. Sync custom chapters
    const cachedChapters = getCustomCurriculum(generationMode, selectedSubject.id);
    let chaptersToSync = customOverrides.custom_chapters;

    if (cachedChapters && cachedChapters.length > 0) {
      if (
        !customOverrides.custom_chapters ||
        JSON.stringify(customOverrides.custom_chapters) !== JSON.stringify(cachedChapters)
      ) {
        chaptersToSync = cachedChapters;
      }
    } else {
      if (generationMode === 'template') {
        const sourceList =
          chapters && chapters.length > 0
            ? chapters
            : selectedSubject.bab_list && selectedSubject.bab_list.length > 0
            ? selectedSubject.bab_list
            : [];
        if (sourceList.length > 0) {
          const converted = convertChapterTopicsToCustom(sourceList);
          saveCustomCurriculum(generationMode, selectedSubject.id, converted);
          chaptersToSync = converted;
        }
      } else {
        if (!customOverrides.custom_chapters || customOverrides.custom_chapters.length > 0) {
          chaptersToSync = [];
        }
      }
    }

    // 2. Sync custom CP elements
    const cachedCp = getCustomCpElements(generationMode, selectedSubject.id);
    let cpToSync = customOverrides.custom_elemen_cp;
    if (cachedCp && cachedCp.length > 0) {
      if (
        !customOverrides.custom_elemen_cp ||
        JSON.stringify(customOverrides.custom_elemen_cp) !== JSON.stringify(cachedCp)
      ) {
        cpToSync = cachedCp;
      }
    }

    if (chaptersToSync !== customOverrides.custom_chapters || cpToSync !== customOverrides.custom_elemen_cp) {
      onChangeCustomOverrides({
        ...customOverrides,
        custom_chapters: chaptersToSync,
        custom_elemen_cp: cpToSync,
      });
    }
  }, [selectedSubject?.id, generationMode, chapters]);

  // Service Category Helpers
  const isModulAjar = activeService.id === '08_modul_ajar';
  const isCpTp = activeService.id === '03_cp_tp';
  const isAtp = activeService.id === '04_atp';
  const isProta = activeService.id === '05_prota';
  const isPromes = activeService.id === '06_promes';
  const isKktp = activeService.id === '07_kktp';
  const isLkpd = activeService.id === '09_lkpd';
  const isKuis = activeService.id === '10_kuis';
  const isSumatifBab = activeService.id === '11_sumatif_bab';
  const isStsSas = activeService.id === '12_sts_sas';
  const isExamService = isKuis || isSumatifBab || isStsSas;
  const isPresensi = activeService.id === '13_presensi';
  const isJurnal = activeService.id === '14_jurnal_mengajar';
  const isDaftarNilai = activeService.id === '15_daftar_nilai';
  const isClassroomService = isPresensi || isDaftarNilai;

  // Form Field Toggles by Service
  const showChapterSelector = Boolean(activeService.requiresChapter || isModulAjar || isLkpd || isKuis || isSumatifBab);
  const showAlokasiJpBab = isModulAjar;
  const showPedagogicalModel = isModulAjar;
  const isAnnualScope = isProta;

  const [classrooms, setClassrooms] = useState<ClassroomRombel[]>(() => getClassrooms());

  // Reload classrooms when props or focus change
  useEffect(() => {
    setClassrooms(getClassrooms());
  }, [activeService.id]);

  const activeClassroom =
    classrooms.find((c) => c.nama_rombel === customOverrides.nama_rombel) ||
    getActiveClassroom() ||
    classrooms[0] ||
    null;

  const effectiveStudents: StudentOverrideItem[] =
    customOverrides.students && customOverrides.students.length > 0
      ? customOverrides.students
      : (activeClassroom?.students || []).map((s: StudentItem) => ({
          nomor_absen: s.nomor_absen,
          nisn: s.nisn,
          nama_lengkap: s.nama_lengkap,
          jenis_kelamin: s.jenis_kelamin,
        }));

  const handleSelectRombel = (rombelId: string) => {
    const found = classrooms.find((c) => c.id === rombelId);
    if (found) {
      setActiveClassroomId(found.id);
      onChangeCustomOverrides({
        ...customOverrides,
        nama_rombel: found.nama_rombel,
        wali_kelas: found.wali_kelas,
        students: found.students.map((s: StudentItem) => ({
          nomor_absen: s.nomor_absen,
          nisn: s.nisn,
          nama_lengkap: s.nama_lengkap,
          jenis_kelamin: s.jenis_kelamin,
        })),
      });
    }
  };

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
  const allTpsFromSubject =
    selectedSubject?.bab_list && selectedSubject.bab_list.length > 0
      ? selectedSubject.bab_list.flatMap((b) => b.tujuan_pembelajaran || [])
      : [];

  const defaultTps: CustomTpItem[] = (
    !showChapterSelector && allTpsFromSubject.length > 0
      ? allTpsFromSubject
      : selectedChapter?.tujuan_pembelajaran ||
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

  const activeCpElements: CustomCpElementItem[] =
    customOverrides.custom_elemen_cp && customOverrides.custom_elemen_cp.length > 0
      ? customOverrides.custom_elemen_cp
      : officialElements;

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

  // Alternatif 1 & 4 CRUD Chapter Handlers
  const triggerSaveAlert = () => {
    setJustSavedNotification(true);
    setTimeout(() => setJustSavedNotification(false), 2500);
  };

  const handleOpenAddChapter = () => {
    setChapterEditing(null);
    setIsChapterEditorOpen(true);
  };

  const handleOpenEditChapter = (ch: CustomChapterItem) => {
    setChapterEditing(ch);
    setIsChapterEditorOpen(true);
  };

  const handleSaveChapterFromModal = (savedChapter: CustomChapterItem) => {
    if (!selectedSubject) return;
    const currentList = customOverrides.custom_chapters || [];
    let updatedList: CustomChapterItem[];

    const existingIdx = currentList.findIndex(
      (c) => c.id_bab === savedChapter.id_bab || c.nomor_bab === savedChapter.nomor_bab
    );

    if (existingIdx >= 0) {
      updatedList = currentList.map((item, idx) => (idx === existingIdx ? savedChapter : item));
    } else {
      updatedList = [...currentList, savedChapter];
    }

    updatedList.sort((a, b) => a.semester - b.semester || a.nomor_bab - b.nomor_bab);

    saveCustomCurriculum(generationMode, selectedSubject.id, updatedList);
    onChangeCustomOverrides({
      ...customOverrides,
      custom_chapters: updatedList,
    });
    triggerSaveAlert();
  };

  const handleDeleteChapter = (indexToDelete: number) => {
    if (!selectedSubject) return;
    const currentList = customOverrides.custom_chapters || [];
    const updatedList = currentList.filter((_, idx) => idx !== indexToDelete);

    saveCustomCurriculum(generationMode, selectedSubject.id, updatedList);
    onChangeCustomOverrides({
      ...customOverrides,
      custom_chapters: updatedList,
    });
    triggerSaveAlert();
  };

  const handleMoveChapter = (index: number, direction: 'up' | 'down') => {
    if (!selectedSubject) return;
    const currentList = [...(customOverrides.custom_chapters || [])];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= currentList.length) return;

    const temp = currentList[index];
    currentList[index] = currentList[targetIndex];
    currentList[targetIndex] = temp;

    saveCustomCurriculum(generationMode, selectedSubject.id, currentList);
    onChangeCustomOverrides({
      ...customOverrides,
      custom_chapters: currentList,
    });
    triggerSaveAlert();
  };

  const handleResetCurriculum = () => {
    if (!selectedSubject) return;
    resetCustomCurriculum(generationMode, selectedSubject.id);

    if (generationMode === 'template') {
      const sourceList =
        chapters && chapters.length > 0
          ? chapters
          : selectedSubject.bab_list && selectedSubject.bab_list.length > 0
          ? selectedSubject.bab_list
          : [];
      const converted = convertChapterTopicsToCustom(sourceList);
      saveCustomCurriculum(generationMode, selectedSubject.id, converted);
      onChangeCustomOverrides({
        ...customOverrides,
        custom_chapters: converted,
      });
    } else {
      saveCustomCurriculum(generationMode, selectedSubject.id, []);
      onChangeCustomOverrides({
        ...customOverrides,
        custom_chapters: [],
      });
    }
    triggerSaveAlert();
  };

  const handleSwitchGenerationMode = (nextMode: GenerationMode) => {
    if (nextMode === generationMode) return;
    onChangeGenerationMode?.(nextMode);
    if (!selectedSubject) return;

    const cached = getCustomCurriculum(nextMode, selectedSubject.id);
    if (cached) {
      onChangeCustomOverrides({
        ...customOverrides,
        custom_chapters: cached,
      });
    } else if (nextMode === 'template') {
      const sourceList =
        chapters && chapters.length > 0
          ? chapters
          : selectedSubject.bab_list && selectedSubject.bab_list.length > 0
          ? selectedSubject.bab_list
          : [];
      const converted = convertChapterTopicsToCustom(sourceList);
      saveCustomCurriculum(nextMode, selectedSubject.id, converted);
      onChangeCustomOverrides({
        ...customOverrides,
        custom_chapters: converted,
      });
    } else {
      saveCustomCurriculum(nextMode, selectedSubject.id, []);
      onChangeCustomOverrides({
        ...customOverrides,
        custom_chapters: [],
      });
    }
    triggerSaveAlert();
  };

  const handleOpenAddCp = () => {
    setCpEditing(null);
    setIsCpEditorOpen(true);
  };

  const handleOpenEditCp = (cp: CustomCpElementItem) => {
    setCpEditing(cp);
    setIsCpEditorOpen(true);
  };

  const handleSaveCpFromModal = (savedCp: CustomCpElementItem) => {
    if (!selectedSubject) return;
    const currentList = customOverrides.custom_elemen_cp && customOverrides.custom_elemen_cp.length > 0
      ? customOverrides.custom_elemen_cp
      : officialElements;
    let updatedList: CustomCpElementItem[];

    const existingIdx = currentList.findIndex(
      (c) => c.kode_elemen === savedCp.kode_elemen || c.nama_elemen.toLowerCase() === savedCp.nama_elemen.toLowerCase()
    );

    if (existingIdx >= 0) {
      updatedList = currentList.map((item, idx) => (idx === existingIdx ? savedCp : item));
    } else {
      updatedList = [...currentList, savedCp];
    }

    saveCustomCpElements(generationMode, selectedSubject.id, updatedList);
    onChangeCustomOverrides({
      ...customOverrides,
      custom_elemen_cp: updatedList,
    });
    triggerSaveAlert();
  };

  const handleDeleteCp = (indexToDelete: number) => {
    if (!selectedSubject) return;
    const currentList = customOverrides.custom_elemen_cp && customOverrides.custom_elemen_cp.length > 0
      ? customOverrides.custom_elemen_cp
      : officialElements;
    if (currentList.length <= 1) {
      alert('Mata pelajaran minimal harus memiliki 1 Elemen Capaian Pembelajaran (CP).');
      return;
    }
    const updatedList = currentList.filter((_, idx) => idx !== indexToDelete);

    saveCustomCpElements(generationMode, selectedSubject.id, updatedList);
    onChangeCustomOverrides({
      ...customOverrides,
      custom_elemen_cp: updatedList,
    });
    triggerSaveAlert();
  };

  const handleResetCp = () => {
    if (!selectedSubject) return;
    resetCustomCpElements(generationMode, selectedSubject.id);
    const bskapList = selectedSubject.elemen_cp_resmi && selectedSubject.elemen_cp_resmi.length > 0
      ? selectedSubject.elemen_cp_resmi
      : [
          {
            kode_elemen: 'EL-01',
            nama_elemen: 'Pemahaman Konsep',
            deskripsi_cp: `Peserta didik mampu memahami dan menerapkan konsep inti ${selectedSubject.nama_mapel} pada ${faseLabel} secara sistematis dan kontekstual.`,
          },
          {
            kode_elemen: 'EL-02',
            nama_elemen: 'Keterampilan Proses',
            deskripsi_cp: `Peserta didik mampu mengamati, menanya, merencanakan penyelidikan, menganalisis data, dan mengomunikasikan hasil karya ${selectedSubject.nama_mapel} secara kolaboratif.`,
          },
        ];
    onChangeCustomOverrides({
      ...customOverrides,
      custom_elemen_cp: bskapList,
    });
    triggerSaveAlert();
  };

  // Effective Chapters for Live Preview & Calculators
  const activeCustomChapters = customOverrides.custom_chapters;
  const hasCustomChapters = Boolean(activeCustomChapters && activeCustomChapters.length > 0);

  const effectiveSubjectChapters: ChapterTopic[] = hasCustomChapters
    ? (activeCustomChapters || []).map((cb) => ({
        id: cb.id_bab || `CUSTOM-${cb.nomor_bab}`,
        nomor_bab: cb.nomor_bab,
        semester: cb.semester,
        judul_bab: cb.judul_bab,
        alokasi_jp: cb.alokasi_jp_bab,
        elemen_cp: cb.elemen_cp || 'Pemahaman Konsep & Keterampilan Proses',
        estimasi_pertemuan: cb.estimasi_jumlah_pertemuan || Math.ceil(cb.alokasi_jp_bab / 3),
        rentang_minggu_promes: cb.rentang_minggu_promes || `Minggu Semester ${cb.semester}`,
        model_pembelajaran_default: 'Problem-Based Learning',
        dimensi_profil_lulusan: ['Penalaran Kritis', 'Kreativitas', 'Kolaborasi', 'Kemandirian'],
        tujuan_pembelajaran: (cb.tujuan_pembelajaran || []).map((tp) => ({
          code: tp.code,
          deskripsi: tp.deskripsi,
          alokasi_jp: tp.alokasi_jp || 2,
        })),
      }))
    : selectedSubject?.bab_list && selectedSubject.bab_list.length > 0
    ? selectedSubject.bab_list
    : chapters;

  const allSubjectChapters = effectiveSubjectChapters;
  const sem1Chapters = allSubjectChapters.filter((c) => c.semester === 1);
  const sem2Chapters = allSubjectChapters.filter((c) => c.semester === 2);
  const currentSemesterChapters =
    semester === 1
      ? sem1Chapters.length > 0
        ? sem1Chapters
        : allSubjectChapters
      : sem2Chapters.length > 0
      ? sem2Chapters
      : allSubjectChapters;

  const totalCustomJp = (activeCustomChapters || []).reduce(
    (acc, c) => acc + (Number(c.alokasi_jp_bab) || 0),
    0
  );
  const targetJpTahunan = selectedSubject?.total_alokasi_jp_tahun || 108;
  const isCurriculumService =
    isProta || isPromes || isAtp || isCpTp || isKktp || isModulAjar || isLkpd;

  const monthLabels =
    semester === 1
      ? ['JUL', 'AGU', 'SEP', 'OKT', 'NOV', 'DES']
      : ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN'];

  const activeCoreServices = CORE_SERVICES.filter((s) => !s.isComingSoon && s.id !== '01_data_kelas');

  const [previewMode, setPreviewMode] = useState<'word' | 'pdf'>('word');
  const [previewZoom, setPreviewZoom] = useState<ZoomSetting>('fit');
  const [previewPageCount, setPreviewPageCount] = useState<number>(1);
  const [pdfPreviewBuffer, setPdfPreviewBuffer] = useState<ArrayBuffer | null>(null);
  const [isLoadingPdfPreview, setIsLoadingPdfPreview] = useState<boolean>(false);
  const [pdfPreviewError, setPdfPreviewError] = useState<string | null>(null);

  const pageOrientation = getServiceOrientation(activeService.id);

  // Reset to live Word layout when switching service
  useEffect(() => {
    setPreviewMode('word');
    setPdfPreviewBuffer(null);
    setPdfPreviewError(null);
  }, [activeService.id]);

  const handleFetchPdfPreview = async () => {
    if (!selectedSubject || activeService.id === 'coming_soon' || activeService.id === '01_data_kelas') return;
    setIsLoadingPdfPreview(true);
    setPdfPreviewError(null);
    try {
      const sanitizedOverrides: CustomDocumentOverrides = { ...customOverrides };

      // Sanitize custom question items so half-typed/empty cards don't trigger HTTP 422 in preview
      if (sanitizedOverrides.butir_soal_kustom && sanitizedOverrides.butir_soal_kustom.length > 0) {
        sanitizedOverrides.butir_soal_kustom = sanitizedOverrides.butir_soal_kustom.map((q) => ({
          ...q,
          pertanyaan:
            q.pertanyaan && q.pertanyaan.trim().length >= 2
              ? q.pertanyaan
              : '(Belum ada teks pertanyaan)',
        }));
      }

      // Sanitize custom CP / TP items if incomplete
      if (sanitizedOverrides.custom_elemen_cp) {
        sanitizedOverrides.custom_elemen_cp = sanitizedOverrides.custom_elemen_cp.filter(
          (el) => el.kode_elemen?.trim() && el.nama_elemen?.trim().length >= 2 && el.deskripsi_cp?.trim().length >= 5
        );
      }

      // Sanitize custom Jurnal rows so empty tanggal fields never trigger HTTP 422
      if (sanitizedOverrides.custom_jurnal_rows && sanitizedOverrides.custom_jurnal_rows.length > 0) {
        sanitizedOverrides.custom_jurnal_rows = sanitizedOverrides.custom_jurnal_rows.map((row, idx) => ({
          ...row,
          no: idx + 1,
          hari_tanggal: row.hari_tanggal?.trim() || `Pertemuan Ke-${idx + 1}`,
        }));
      }

      // Include teacher_profile only when required fields meet backend Zero-Trust schema constraints
      const hasCompleteProfile = Boolean(
        teacher.nama_guru?.trim().length >= 2 &&
          teacher.nama_sekolah?.trim().length >= 3 &&
          teacher.kabupaten_kota?.trim().length >= 3 &&
          teacher.provinsi?.trim().length >= 3 &&
          teacher.nama_kepala_sekolah?.trim().length >= 2 &&
          (teacher.no_whatsapp || '').replace(/\D/g, '').length >= 9
      );

      const payload: DocumentGenerateRequest = {
        service_id: activeService.id,
        jenjang,
        kelas,
        subject_id: selectedSubject.id,
        semester,
        chapter_id: selectedChapter?.id,
        model_pembelajaran: modelPembelajaran,
        paper_size: paperSize,
        output_format: 'pdf',
        include_lkpd: includeLkpd,
        include_asesmen: includeAsesmen,
        include_rubrik: includeRubrik,
        teacher_profile: hasCompleteProfile ? teacher : undefined,
        custom_overrides: sanitizedOverrides,
      };
      const { buffer, pageCount } = await apiClient.previewDocumentPdf(payload);
      setPdfPreviewBuffer(buffer);
      setPreviewPageCount(pageCount);
    } catch (err) {
      setPdfPreviewError(err instanceof Error ? err.message : 'Gagal memuat pratinjau PDF.');
    } finally {
      setIsLoadingPdfPreview(false);
    }
  };

  const handleSwitchPreviewMode = (mode: 'word' | 'pdf') => {
    setPreviewMode(mode);
    if (mode === 'pdf') {
      handleFetchPdfPreview();
    }
  };

  const handleStepZoom = (delta: number) => {
    setPreviewZoom((prev) => {
      const base = prev === 'fit' ? 0.85 : prev;
      return Math.min(1.25, Math.max(0.45, Math.round((base + delta) * 100) / 100));
    });
  };

  const paginatorContentKey = JSON.stringify({
    s: activeService.id,
    p: paperSize,
    j: jenjang,
    k: kelas,
    sub: selectedSubject?.id,
    sem: semester,
    ch: selectedChapter?.id,
    m: modelPembelajaran,
    lk: includeLkpd,
    as: includeAsesmen,
    rb: includeRubrik,
    t: teacher,
    ov: customOverrides,
  });

  const renderOfficialKop = () => (
    <div data-keep-together="true" className="border-b-2 border-slate-900 pb-3 text-center">
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
  );

  const renderOfficialPengesahan = () => (
    <div data-keep-together="true" className="mt-8 grid grid-cols-2 gap-4 border-t border-slate-300 pt-5 text-xs">
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
  );

  const renderExamPreviewFlow = () => {
    const allCustom =
      customOverrides.butir_soal_kustom && customOverrides.butir_soal_kustom.length > 0
        ? customOverrides.butir_soal_kustom
        : [
            {
              tipe_soal: 'PG' as const,
              pertanyaan: '(Ketik soal Anda pada kartu di sebelah kiri...)',
              opsi: ['Opsi A', 'Opsi B', 'Opsi C', 'Opsi D'],
              kunci_jawaban: 'A',
              tp_code: activeTps[0]?.code || 'TP.1',
              level_kognitif: 'C1-C2',
              stimulus: '',
              bobot_skor: 4,
              pembahasan: '',
            },
          ];

    const pgQuestions = allCustom.filter((q) => q.tipe_soal === 'PG');
    const essaiQuestions = allCustom.filter((q) => q.tipe_soal !== 'PG');
    const sortedQuestions = [...pgQuestions, ...essaiQuestions];

    return (
      <>
        {renderOfficialKop()}

        <div data-keep-together="true" className="mt-4 text-center">
          <h2 className="text-base font-extrabold uppercase text-slate-900">
            {isKuis
              ? 'KUIS HARIAN & PENILAIAN FORMATIF'
              : isSumatifBab
              ? 'ASESMEN SUMATIF LINGKUP MATERI (BAB)'
              : `PENILAIAN ${customOverrides.jenis_ujian || 'STS'} — PAKET ${customOverrides.paket_soal || 'A'}`}
          </h2>
          <p className="font-bold uppercase text-slate-700">
            {selectedSubject?.nama_mapel} | {jenjang} KELAS {kelas} | SEMESTER {semester}
          </p>
        </div>

        {/* Identitas Ujian */}
        <div data-keep-together="true" className="mt-3 grid grid-cols-2 gap-2 rounded border border-slate-200 bg-slate-50/50 p-2.5 text-[11px]">
          <div className="space-y-0.5">
            <p><span className="font-semibold text-slate-500">Mata Pelajaran:</span> {selectedSubject?.nama_mapel}</p>
            <p><span className="font-semibold text-slate-500">Kelas / Fase:</span> Kelas {kelas} / {faseLabel}</p>
            <p><span className="font-semibold text-slate-500">Materi Pokok:</span> {selectedChapter?.judul_bab || 'Materi Pokok Pembelajaran'}</p>
          </div>
          <div className="space-y-0.5">
            <p><span className="font-semibold text-slate-500">Hari, Tanggal:</span> ............................................</p>
            <p>
              <span className="font-semibold text-slate-500">Alokasi Waktu:</span>{' '}
              {customOverrides.alokasi_waktu_menit ?? (isKuis ? 20 : isSumatifBab ? 60 : 90)} Menit
            </p>
            <p><span className="font-semibold text-slate-500">Nama Siswa / No:</span> ............................................</p>
          </div>
        </div>

        {/* Petunjuk Umum */}
        <div data-keep-together="true" className="mt-3 p-2.5 text-[11px] leading-relaxed text-slate-700">
          <p className="font-bold text-slate-900">PETUNJUK UMUM PENGERJAAN:</p>
          <ol className="mt-1 list-decimal pl-4 space-y-0.5">
            <li>Berdoalah sebelum mulai mengerjakan soal evaluasi.</li>
            <li>Tuliskan identitas nama lengkap dan nomor peserta pada lembar pengerjaan.</li>
            <li>Kerjakan soal Bagian A (Pilihan Ganda) dan Bagian B (Essai) dengan teliti, tertib, dan mandiri.</li>
            <li>Dahulukan menjawab butir soal yang Anda anggap paling mudah.</li>
            <li>Periksa kembali kelengkapan seluruh jawaban sebelum diserahkan kepada pengawas ujian.</li>
          </ol>
        </div>

        {/* Bagian A: Soal Pilihan Ganda */}
        {pgQuestions.length > 0 && (
          <>
            <h4
              data-keep-with-next="true"
              className="mt-4 font-bold text-slate-900 border-b border-slate-200 pb-1 text-xs uppercase"
            >
              A. SOAL PILIHAN GANDA (Pilihlah salah satu jawaban yang paling tepat)
            </h4>
            {pgQuestions.map((q, pgIdx) => (
              <div key={`pg-${pgIdx}`} data-keep-together="true" className="mt-2.5 space-y-1 text-xs">
                {q.stimulus && (
                  <p className="text-slate-800 leading-relaxed font-normal">
                    {q.stimulus}
                  </p>
                )}
                <p className="font-bold text-slate-900">
                  {pgIdx + 1}. {q.pertanyaan || '(Belum ada teks pertanyaan)'}
                </p>
                {q.opsi && (
                  <ul className="pl-5 space-y-0.5 text-slate-700">
                    {q.opsi.map((opt, oIdx) => (
                      <li key={oIdx}>
                        {['A', 'B', 'C', 'D', 'E'][oIdx]}. {opt || '...'}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </>
        )}

        {/* Bagian B: Soal Essai */}
        {essaiQuestions.length > 0 && (
          <>
            <h4
              data-keep-with-next="true"
              className="mt-4 font-bold text-slate-900 border-b border-slate-200 pb-1 text-xs uppercase"
            >
              B. SOAL ESSAI (Jawablah pertanyaan berikut dengan singkat, jelas, dan tepat)
            </h4>
            {essaiQuestions.map((q, esIdx) => (
              <div key={`es-${esIdx}`} data-keep-together="true" className="mt-2.5 space-y-1 text-xs">
                {q.stimulus && (
                  <p className="text-slate-800 leading-relaxed font-normal">
                    {q.stimulus}
                  </p>
                )}
                <p className="font-bold text-slate-900">
                  {esIdx + 1}. {q.pertanyaan || '(Belum ada teks pertanyaan)'}
                </p>
                <p className="text-[11px] italic text-slate-400 pl-4">
                  Jawaban: _________________________________________________________________
                </p>
              </div>
            ))}
          </>
        )}

        {/* HALAMAN BARU: KUNCI JAWABAN & KISI-KISI (PEGANGAN GURU) */}
        <div
          data-page-break="before"
          data-keep-together="true"
          className="border-b-2 border-slate-900 pb-2 text-center"
        >
          <p className="text-[10px] font-bold uppercase tracking-wide text-slate-600">
            PEMERINTAH {(teacher.kabupaten_kota || 'KABUPATEN/KOTA').toUpperCase()} — DINAS PENDIDIKAN
          </p>
          <p className="text-sm font-extrabold uppercase text-slate-900">
            {teacher.nama_sekolah || 'NAMA SATUAN PENDIDIKAN'}
          </p>
          <p className="mt-0.5 text-[10px] text-slate-500">
            {selectedSubject?.nama_mapel} • {jenjang} Kelas {kelas} • Semester {semester} • Paket {customOverrides.paket_soal || 'A'}
          </p>
        </div>

        {/* 1. Kunci Jawaban & Pedoman Penskoran */}
        <h3 data-keep-with-next="true" className="mt-4 font-extrabold uppercase text-slate-900 text-xs">
          1. KUNCI JAWABAN DAN PEDOMAN PENSKORAN
        </h3>
        <div data-splittable-table="true" className="paper-table-container mt-1.5">
          <table className="paper-table">
            <thead>
              <tr>
                <th>No</th>
                <th>Bentuk &amp; Level</th>
                <th>Kunci Jawaban / Poin Rubrik</th>
                <th>Skor</th>
              </tr>
            </thead>
            <tbody>
              {sortedQuestions.map((q, idx) => {
                const isPg = q.tipe_soal === 'PG';
                const sectionIdx = isPg
                  ? pgQuestions.indexOf(q) + 1
                  : essaiQuestions.indexOf(q) + 1;
                return (
                  <tr key={idx}>
                    <td>{isPg ? `A.${sectionIdx}` : `B.${sectionIdx}`}</td>
                    <td>
                      {isPg ? 'PG' : 'Essai'} ({q.level_kognitif || 'C1-C2'})
                    </td>
                    <td>
                      <span className="font-bold">{q.kunci_jawaban || '-'}</span>
                      {q.pembahasan ? ` — ${q.pembahasan}` : ''}
                    </td>
                    <td>{q.bobot_skor || (isPg ? 4 : 10)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="mt-1 text-[11px] text-slate-600">
          Nilai Akhir = (Total Skor Diperoleh / Total Skor Maksimal) × 100
        </p>

        {/* 2. Tabel Kisi-Kisi Penulisan Soal (7 Kolom) */}
        <h3 data-keep-with-next="true" className="mt-4 font-extrabold uppercase text-slate-900 text-xs">
          2. TABEL KISI-KISI PENULISAN SOAL
        </h3>
        <div data-splittable-table="true" className="paper-table-container mt-1.5">
          <table className="paper-table">
            <thead>
              <tr>
                <th>No</th>
                <th>TP</th>
                <th>Materi Pokok</th>
                <th>Indikator Soal</th>
                <th>Level</th>
                <th>Bentuk</th>
                <th>No Soal</th>
              </tr>
            </thead>
            <tbody>
              {sortedQuestions.map((q, idx) => {
                const isPg = q.tipe_soal === 'PG';
                const sectionIdx = isPg
                  ? pgQuestions.indexOf(q) + 1
                  : essaiQuestions.indexOf(q) + 1;
                return (
                  <tr key={idx}>
                    <td>{idx + 1}</td>
                    <td>{q.tp_code || '-'}</td>
                    <td>{selectedChapter?.judul_bab || selectedSubject?.nama_mapel}</td>
                    <td>Menguasai indikator {q.tp_code || 'materi pokok'}</td>
                    <td>{q.level_kognitif || 'C1-C2'}</td>
                    <td>{isPg ? 'Pilihan Ganda' : 'Essai'}</td>
                    <td>{isPg ? `A.${sectionIdx}` : `B.${sectionIdx}`}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* 3. Lembar Pengesahan */}
        {renderOfficialPengesahan()}
      </>
    );
  };

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
            {activeService.title}
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
          {/* Sticky Top Action Bar: Akses Download 1-Klik tanpa perlu scroll ke bawah */}
          <div className="sticky top-[68px] z-30 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-blue-200/90 bg-white/95 px-4 py-3 shadow-md backdrop-blur">
            <div className="min-w-0">
              <p className="text-[11px] font-bold uppercase tracking-wider text-blue-700 truncate">
                {activeService.codeLabel} • {outputFormat.toUpperCase()} ({paperSize})
              </p>
              <p className="text-xs font-extrabold text-slate-900 truncate">
                {selectedSubject?.nama_mapel || activeService.shortTitle}
              </p>
            </div>
            <button
              type="button"
              onClick={onGenerate}
              disabled={isGenerating}
              className="clay-btn-primary inline-flex shrink-0 items-center gap-2 px-4 py-2 text-xs font-extrabold disabled:opacity-60"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Menyusun...</span>
                </>
              ) : (
                <>
                  <FileDown className="h-3.5 w-3.5" />
                  <span>Download Dokumen</span>
                </>
              )}
            </button>
          </div>

          {/* Mode Banner & Switcher In-Place (Hanya untuk Layanan Kurikulum 03-09) */}
          {isCurriculumService && (
            <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="inline-flex rounded-xl border border-slate-200 bg-slate-100 p-1 text-xs font-bold">
                  <button
                    type="button"
                    onClick={() => handleSwitchGenerationMode('template')}
                    className={`rounded-lg px-3 py-1 transition ${
                      generationMode === 'template'
                        ? 'bg-blue-700 text-white shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Template BSKAP
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSwitchGenerationMode('manual')}
                    className={`rounded-lg px-3 py-1 transition ${
                      generationMode === 'manual'
                        ? 'bg-slate-800 text-white shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Buat Manual
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  {justSavedNotification ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-md animate-in fade-in duration-200">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Tersimpan
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500">
                      <Save className="h-3 w-3 text-slate-400" />
                      Auto-save
                    </span>
                  )}

                  <button
                    type="button"
                    onClick={handleResetCurriculum}
                    title={generationMode === 'template' ? 'Reset ke Template BSKAP 2025' : 'Bersihkan seluruh bab'}
                    className="rounded-lg border border-slate-200 px-2.5 py-1 text-[11px] font-bold text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors"
                  >
                    <RotateCcw className="inline mr-1 h-3 w-3" />
                    {generationMode === 'template' ? 'Reset Template' : 'Bersihkan'}
                  </button>
                </div>
              </div>
            </div>
          )}

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

              {/* Semester & Alokasi JP Bab */}
              <div className={`grid grid-cols-1 gap-3 ${showAlokasiJpBab ? 'sm:grid-cols-2' : ''}`}>
                {isAnnualScope ? (
                  <div>
                    <label className="mb-1 block text-xs font-bold text-slate-700">
                      Cakupan Waktu Kurikulum
                    </label>
                    <div className="clay-input flex items-center justify-between px-3 py-2.5 text-xs font-bold text-blue-800 bg-blue-50/50">
                      <span>1 Tahun Ajaran Penuh</span>
                      <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] text-blue-700">
                        Semester 1 &amp; 2
                      </span>
                    </div>
                  </div>
                ) : (
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
                )}

                {showAlokasiJpBab && (
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
                )}
              </div>

              {/* Bab / Materi Pokok (Hanya ditampilkan jika layanan membutuhkan Bab) */}
              {showChapterSelector && (
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
              )}

              {/* Model Pembelajaran (Hanya ditampilkan jika Modul Ajar) */}
              {showPedagogicalModel && (
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
              )}

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

          {/* Card 1: Editor Capaian Pembelajaran (CP) Berdasarkan Elemen (Seluruh Layanan Kurikulum) */}
          {isCurriculumService && (
            <div className="clay-card p-5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
                <div>
                  <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800 flex items-center gap-2">
                    2. Capaian Pembelajaran (CP) Berdasarkan Elemen
                  </h2>
                  <p className="text-[11px] font-medium text-slate-500">
                    Kelola rumusan elemen dan narasi CP fase ini sesuai BSKAP 046/2025 atau kurikulum sekolah Anda.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {customOverrides.custom_elemen_cp && customOverrides.custom_elemen_cp.length > 0 && (
                    <button
                      type="button"
                      onClick={handleResetCp}
                      className="text-[11px] font-bold text-slate-600 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 px-2.5 py-1.5 rounded-lg transition-colors flex items-center gap-1"
                      title="Kembalikan ke rumusan resmi BSKAP 046/2025"
                    >
                      <RotateCcw className="w-3 h-3" />
                      <span>Reset BSKAP</span>
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={handleOpenAddCp}
                    className="clay-btn-primary text-xs font-bold px-3 py-1.5 flex items-center gap-1.5"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Tambah CP</span>
                  </button>
                </div>
              </div>

              <div className="mt-4 space-y-3">
                {activeCpElements.map((elem, idx) => {
                  const isCustom = Boolean(customOverrides.custom_elemen_cp && customOverrides.custom_elemen_cp.length > 0);
                  return (
                    <div
                      key={elem.kode_elemen || idx}
                      className="p-3.5 rounded-2xl bg-white border border-slate-200/80 shadow-sm hover:border-indigo-300 transition-all"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="px-2 py-0.5 text-[10px] font-black rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200">
                            {elem.kode_elemen || `EL-${idx + 1}`}
                          </span>
                          <h4 className="text-xs font-extrabold text-slate-800">
                            {elem.nama_elemen}
                          </h4>
                          {isCustom ? (
                            <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-amber-50 text-amber-700 border border-amber-200">
                              Kustom
                            </span>
                          ) : (
                            <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-slate-100 text-slate-600 border border-slate-200">
                              BSKAP 046/2025
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          <button
                            type="button"
                            onClick={() => handleOpenEditCp(elem)}
                            className="p-1 text-slate-400 hover:text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors"
                            title="Edit Rumusan CP"
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteCp(idx)}
                            className="p-1 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition-colors"
                            title="Hapus Elemen CP"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                      <p className="mt-2 text-[11px] text-slate-600 leading-relaxed bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                        {elem.deskripsi_cp}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Card CRUD Lingkup Materi / Bab & Alokasi JP (Alternatif 1 & 4) */}
          {isCurriculumService && (
            <div className="clay-card p-5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
                <div>
                  <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800">
                    3. Lingkup Materi / Bab &amp; Alokasi JP
                  </h2>
                  <p className="text-[11px] font-medium text-slate-500">
                    Kontrol penuh CRUD bab, urutan materi, alokasi JP, dan butir TP yang tersinkronisasi lintas layanan.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleOpenAddChapter}
                    className="clay-btn-primary inline-flex items-center gap-1 px-3 py-1.5 text-xs font-bold"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    <span>Tambah Bab</span>
                  </button>
                </div>
              </div>

              {/* Kalkulator JP Banner */}
              <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-xl bg-slate-50 border border-slate-200/80 p-3 text-xs">
                <div className="flex items-center gap-2">
                  <Calculator className="h-4 w-4 text-blue-700" />
                  <span className="font-bold text-slate-700">
                    Total: <span className="text-blue-700 font-extrabold">{totalCustomJp} JP</span> ({activeCustomChapters?.length || 0} Bab)
                  </span>
                </div>
                <div className="text-[11px] font-medium text-slate-600">
                  Target Standar: <strong>{targetJpTahunan} JP/Tahun</strong> ({jpPerMinggu} JP/Minggu)
                </div>
              </div>

              {/* Chapter Items List */}
              <div className="mt-3.5 space-y-2.5">
                {(!activeCustomChapters || activeCustomChapters.length === 0) ? (
                  <div className="rounded-xl border-2 border-dashed border-slate-200 p-6 text-center">
                    <p className="text-xs font-semibold text-slate-600">
                      Belum ada materi bab yang terdaftar.
                    </p>
                    <p className="mt-1 text-[11px] text-slate-400">
                      Klik tombol &quot;+ Tambah Bab&quot; di atas untuk menyusun materi pokok dan TP pertama Anda.
                    </p>
                  </div>
                ) : (
                  activeCustomChapters.map((ch, idx) => (
                    <div
                      key={ch.id_bab || idx}
                      className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 rounded-xl border border-slate-200 bg-white p-3 hover:border-blue-300 transition-all shadow-sm"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-1.5 mb-1">
                          <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-bold text-blue-800">
                            Bab {ch.nomor_bab}
                          </span>
                          <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600">
                            Sem {ch.semester}
                          </span>
                          <span className="rounded bg-emerald-50 text-emerald-700 border border-emerald-200 px-1.5 py-0.5 text-[10px] font-bold">
                            {ch.alokasi_jp_bab} JP
                          </span>
                          <span className="rounded bg-indigo-50 text-indigo-700 border border-indigo-200 px-1.5 py-0.5 text-[10px] font-semibold">
                            {(ch.tujuan_pembelajaran || []).length} TP
                          </span>
                        </div>
                        <p className="text-xs font-bold text-slate-800 truncate">
                          {ch.judul_bab}
                        </p>
                        <p className="text-[10px] text-slate-500 truncate">
                          Elemen CP: {ch.elemen_cp}
                        </p>
                      </div>

                      <div className="flex items-center gap-1 shrink-0 self-end sm:self-center">
                        <button
                          type="button"
                          disabled={idx === 0}
                          onClick={() => handleMoveChapter(idx, 'up')}
                          title="Geser Naik"
                          className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                          <ArrowUp className="h-3.5 w-3.5" />
                        </button>
                        <button
                          type="button"
                          disabled={idx === (activeCustomChapters.length - 1)}
                          onClick={() => handleMoveChapter(idx, 'down')}
                          title="Geser Turun"
                          className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                          <ArrowDown className="h-3.5 w-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleOpenEditChapter(ch)}
                          title="Edit Bab & TP"
                          className="p-1.5 rounded-lg border border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100"
                        >
                          <Edit3 className="h-3.5 w-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteChapter(idx)}
                          title="Hapus Bab"
                          className="p-1.5 rounded-lg border border-rose-200 bg-rose-50 text-rose-600 hover:bg-rose-100"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Card Khusus 1: Layanan Administrasi Kelas (Presensi Siswa / Daftar Nilai) */}
          {isClassroomService && (
            <div className="clay-card p-5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
                <div>
                  <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800">
                    2. Data Rombel &amp; Siswa (Lokal Browser)
                  </h2>
                  <p className="text-[11px] font-medium text-slate-500">
                    Pilih rombel aktif atau upload spreadsheet Excel data siswa kelas Anda.
                  </p>
                </div>
                {onOpenClassroomModal && (
                  <button
                    type="button"
                    onClick={onOpenClassroomModal}
                    className="clay-btn-white inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-bold text-blue-700"
                  >
                    <FileSpreadsheet className="h-3.5 w-3.5" />
                    <span>Kelola / Upload Siswa</span>
                  </button>
                )}
              </div>

              <div className="mt-4 space-y-3.5">
                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Pilih Rombel / Kelas Aktif
                  </label>
                  <select
                    value={activeClassroom?.id || ''}
                    onChange={(e) => handleSelectRombel(e.target.value)}
                    className="clay-input w-full px-3 py-2.5 text-xs font-bold text-slate-800 sm:text-sm"
                  >
                    {classrooms.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.nama_rombel} — {c.students?.length || 0} Siswa ({c.jenjang} Kelas {c.tingkat_kelas})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center justify-between rounded-lg bg-blue-50/70 border border-blue-200/80 p-2.5 text-xs">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-blue-700" />
                    <span className="font-bold text-blue-900">
                      {effectiveStudents.length} Siswa Terdaftar
                    </span>
                  </div>
                  <span className="text-[11px] font-semibold text-blue-700">
                    L: {effectiveStudents.filter((s: StudentOverrideItem) => s.jenis_kelamin === 'L').length} | P:{' '}
                    {effectiveStudents.filter((s: StudentOverrideItem) => s.jenis_kelamin === 'P').length}
                  </span>
                </div>

                {isPresensi && (
                  <div>
                    <label className="mb-1 block text-xs font-bold text-slate-700">
                      Bulan Pelaksanaan Presensi
                    </label>
                    <select
                      value={customOverrides.bulan_presensi || 'Agustus'}
                      onChange={(e) =>
                        onChangeCustomOverrides({
                          ...customOverrides,
                          bulan_presensi: e.target.value,
                        })
                      }
                      className="clay-input w-full px-3 py-2.5 text-xs font-bold text-slate-800 sm:text-sm"
                    >
                      {[
                        'Juli',
                        'Agustus',
                        'September',
                        'Oktober',
                        'November',
                        'Desember',
                        'Januari',
                        'Februari',
                        'Maret',
                        'April',
                        'Mei',
                        'Juni',
                      ].map((m) => (
                        <option key={m} value={m}>
                          {m}
                        </option>
                      ))}
                    </select>
                    <p className="mt-1 text-[11px] text-slate-500">
                      Kolom tanggal 1 s.d. 31 dilengkapi formula aktif <code className="bg-slate-100 px-1 py-0.5 rounded text-blue-700 font-bold">=COUNTIF</code> untuk rekap otomatis Hadir (H), Sakit (S), Izin (I), Alpa (A), serta persentase kehadiran kelas.
                    </p>
                  </div>
                )}

                {isDaftarNilai && (
                  <div>
                    <label className="mb-1 block text-xs font-bold text-slate-700">
                      Kriteria Ketercapaian Tujuan Pembelajaran (KKTP)
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        min={50}
                        max={100}
                        value={customOverrides.kktp_nilai ?? 75}
                        onChange={(e) =>
                          onChangeCustomOverrides({
                            ...customOverrides,
                            kktp_nilai: Math.max(50, Math.min(100, Number(e.target.value) || 75)),
                          })
                        }
                        className="clay-input w-28 px-3 py-2 text-xs font-bold text-slate-800 sm:text-sm"
                      />
                      <span className="text-xs font-bold text-slate-600">Nilai Ambang Batas Ketuntasan</span>
                    </div>
                    <p className="mt-1 text-[11px] text-slate-500">
                      Formula aktif <code className="bg-slate-100 px-1 py-0.5 rounded text-blue-700 font-bold">=AVERAGE</code> menghitung rata-rata formatif, pembobotan sumatif STS &amp; SAS, serta formula logika <code className="bg-slate-100 px-1 py-0.5 rounded text-blue-700 font-bold">=IF(NA&gt;=KKTP,"TUNTAS","BELUM TUNTAS")</code> dan statistik kelas otomatis.
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Card Khusus 1B: Jurnal Mengajar Harian (Service 14 — Full CRUD) */}
          {isJurnal && (
            <JurnalEditorSection
              kelas={kelas}
              semester={semester}
              subjectName={selectedSubject?.nama_mapel}
              defaultRombel={activeClassroom?.nama_rombel}
              semesterChapters={currentSemesterChapters}
              customOverrides={customOverrides}
              onChangeCustomOverrides={onChangeCustomOverrides}
            />
          )}

          {/* Card Khusus 2: Program Tahunan (Prota) */}
          {isProta && (
            <div className="clay-card p-5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
                <div>
                  <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800">
                    2. Pengaturan Alokasi Jam Tahunan (Prota)
                  </h2>
                  <p className="text-[11px] font-medium text-slate-500">
                    Distribusi alokasi waktu JP seluruh bab selama 1 tahun ajaran penuh (Semester 1 &amp; 2).
                  </p>
                </div>
              </div>

              <div className="mt-4 space-y-3.5">
                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Cadangan Jam Pelajaran Tahunan (JP)
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={60}
                    value={customOverrides.cadangan_jp ?? 4}
                    onChange={(e) =>
                      onChangeCustomOverrides({
                        ...customOverrides,
                        cadangan_jp: Math.max(0, Number(e.target.value) || 0),
                      })
                    }
                    className="clay-input w-full px-3 py-2 text-xs font-bold text-slate-800"
                  />
                  <p className="mt-1 text-[11px] text-slate-500">
                    Dialokasikan untuk ujian semester, remedi klasikal, atau jeda kalender sekolah.
                  </p>
                </div>

                <div className="rounded-lg bg-blue-50/70 border border-blue-200/80 p-2.5 text-xs text-blue-900">
                  <span className="font-bold">Total Alokasi JP Tahunan Standar:</span>{' '}
                  {selectedSubject?.total_alokasi_jp_tahun || 108} JP/Tahun ({jpPerMinggu} JP/Minggu)
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Catatan Khusus Penggunaan Dokumen Prota
                  </label>
                  <input
                    type="text"
                    value={customOverrides.catatan_khusus || ''}
                    placeholder="Contoh: Disesuaikan dengan kalender pendidikan provinsi..."
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
            </div>
          )}

          {/* Card Khusus 3: Program Semester (Promes) */}
          {isPromes && (
            <div className="clay-card p-5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
                <div>
                  <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800">
                    2. Pengaturan Matriks Program Semester (Promes)
                  </h2>
                  <p className="text-[11px] font-medium text-slate-500">
                    Distribusi alokasi mingguan kalender 26 minggu dengan rumus otomatis =SUM.
                  </p>
                </div>
              </div>

              <div className="mt-4 space-y-3.5">
                <div className="rounded-lg bg-emerald-50/70 border border-emerald-200/80 p-3 text-xs text-emerald-900">
                  <p className="font-bold">Semester {semester} ({semester === 1 ? 'Juli — Desember' : 'Januari — Juni'})</p>
                  <p className="mt-1 text-[11px] text-emerald-700">
                    Beban belajar: <strong>{jpPerMinggu} JP/Minggu</strong> (Durasi {durasiMenitJp} menit/JP).
                  </p>
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Catatan Khusus Agenda Semester
                  </label>
                  <input
                    type="text"
                    value={customOverrides.catatan_khusus || ''}
                    placeholder="Contoh: Termasuk alokasi Asesmen Sumatif Tengah Semester (ASTS)..."
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
            </div>
          )}

          {/* Card Khusus 4: KKTP (Skala Interval) */}
          {isKktp && (
            <div className="clay-card p-5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
                <div>
                  <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800">
                    2. Parameter &amp; Rubrik Kriteria Ketuntasan (KKTP)
                  </h2>
                  <p className="text-[11px] font-medium text-slate-500">
                    Rubrik 4 skala interval nilai &amp; kriteria ketuntasan sesuai PPA Revisi 2025.
                  </p>
                </div>
              </div>

              <div className="mt-4 space-y-3.5">
                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Nilai Ambang Batas Ketuntasan (KKTP Default)
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      min={50}
                      max={100}
                      value={customOverrides.kktp_nilai ?? 75}
                      onChange={(e) =>
                        onChangeCustomOverrides({
                          ...customOverrides,
                          kktp_nilai: Math.max(50, Math.min(100, Number(e.target.value) || 75)),
                        })
                      }
                      className="clay-input w-28 px-3 py-2 text-xs font-bold text-slate-800 sm:text-sm"
                    />
                    <span className="text-xs font-bold text-slate-600">Skala 0 - 100</span>
                  </div>
                </div>

                <div className="rounded-lg bg-slate-50 border border-slate-200 p-2.5 text-[11px] space-y-1 text-slate-700">
                  <p className="font-bold text-slate-800">Pedoman 4 Skala Interval PPA 2025:</p>
                  <p>• <strong>0 - 40%:</strong> Belum mencapai, remedial di seluruh bagian</p>
                  <p>• <strong>41 - 65%:</strong> Belum mencapai ketuntasan, remedial di bagian tertentu</p>
                  <p>• <strong>66 - 85%:</strong> Sudah mencapai ketuntasan, tidak perlu remedial</p>
                  <p>• <strong>86 - 100%:</strong> Sudah mencapai ketuntasan, perlu tantangan/pengayaan</p>
                </div>
              </div>
            </div>
          )}

          {/* Card Khusus: Pengaturan Ujian & Pembuat Soal Ala Google Form (Service 10, 11, 12) */}
          {isExamService && (
            <>
              <div className="clay-card p-5 space-y-4">
                <div className="border-b border-slate-200 pb-3">
                  <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800">
                    Pengaturan Naskah {isKuis ? 'Kuis Harian' : isSumatifBab ? 'Asesmen Sumatif Bab' : 'Ujian STS / SAS'}
                  </h2>
                  <p className="text-[11px] font-medium text-slate-500">
                    Atur jenis ujian, cakupan bab, waktu, dan paket soal deterministik.
                  </p>
                </div>

                {isStsSas && (
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                    <div>
                      <label className="mb-1 block text-xs font-bold text-slate-700">Jenis Ujian</label>
                      <div className="grid grid-cols-2 gap-1.5">
                        {(['STS', 'SAS'] as const).map((ju) => (
                          <button
                            key={ju}
                            type="button"
                            onClick={() => onChangeCustomOverrides({ ...customOverrides, jenis_ujian: ju })}
                            className={`py-2 text-xs font-bold ${
                              (customOverrides.jenis_ujian || 'STS') === ju ? 'clay-btn-primary' : 'clay-btn-white'
                            }`}
                          >
                            {ju}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div>
                      <label className="mb-1 block text-xs font-bold text-slate-700">Alokasi Waktu (Menit)</label>
                      <input
                        type="number"
                        min={0}
                        max={240}
                        value={customOverrides.alokasi_waktu_menit ?? 90}
                        onChange={(e) => {
                          const raw = e.target.value;
                          const val = raw === '' ? 0 : Math.max(0, Math.min(240, Number(raw) || 0));
                          onChangeCustomOverrides({
                            ...customOverrides,
                            alokasi_waktu_menit: val,
                          });
                        }}
                        className="clay-input w-full px-3 py-2 text-xs font-bold text-slate-800"
                      />
                    </div>

                    <div>
                      <label className="mb-1 block text-xs font-bold text-slate-700">Paket Soal (Acak)</label>
                      <div className="grid grid-cols-2 gap-1.5">
                        {(['A', 'B'] as const).map((pk) => (
                          <button
                            key={pk}
                            type="button"
                            onClick={() => onChangeCustomOverrides({ ...customOverrides, paket_soal: pk })}
                            className={`py-2 text-xs font-bold ${
                              (customOverrides.paket_soal || 'A') === pk ? 'clay-btn-success' : 'clay-btn-white'
                            }`}
                          >
                            Paket {pk}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {isStsSas && chapters.length > 0 && (
                  <div>
                    <label className="mb-1.5 block text-xs font-bold text-slate-700">
                      Cakupan Bab yang Diujikan (Multi-Pilih)
                    </label>
                    <div className="flex flex-wrap gap-1.5">
                      {chapters.map((ch) => {
                        const selectedIds = customOverrides.cakupan_bab_ids || chapters.map((c) => c.id);
                        const active = selectedIds.includes(ch.id);
                        return (
                          <button
                            key={ch.id}
                            type="button"
                            onClick={() => {
                              const nextIds = active
                                ? selectedIds.filter((id) => id !== ch.id)
                                : [...selectedIds, ch.id];
                              onChangeCustomOverrides({
                                ...customOverrides,
                                cakupan_bab_ids: nextIds.length > 0 ? nextIds : [ch.id],
                              });
                            }}
                            className={`px-2.5 py-1 text-xs font-bold ${
                              active ? 'clay-btn-success' : 'clay-btn-white'
                            }`}
                          >
                            Bab {ch.nomor_bab}: {ch.judul_bab.slice(0, 28)}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {!isStsSas && (
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-xs font-bold text-slate-700">Alokasi Waktu (Menit)</label>
                      <input
                        type="number"
                        min={0}
                        max={240}
                        value={customOverrides.alokasi_waktu_menit ?? (isKuis ? 20 : 60)}
                        onChange={(e) => {
                          const raw = e.target.value;
                          const val = raw === '' ? 0 : Math.max(0, Math.min(240, Number(raw) || 0));
                          onChangeCustomOverrides({
                            ...customOverrides,
                            alokasi_waktu_menit: val,
                          });
                        }}
                        className="clay-input w-full px-3 py-2 text-xs font-bold text-slate-800"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs font-bold text-slate-700">Paket Soal</label>
                      <div className="grid grid-cols-2 gap-1.5">
                        {(['A', 'B'] as const).map((pk) => (
                          <button
                            key={pk}
                            type="button"
                            onClick={() => onChangeCustomOverrides({ ...customOverrides, paket_soal: pk })}
                            className={`py-2 text-xs font-bold ${
                              (customOverrides.paket_soal || 'A') === pk ? 'clay-btn-success' : 'clay-btn-white'
                            }`}
                          >
                            Paket {pk}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <QuestionBuilderSection
                serviceId={activeService.id as ServiceId}
                jenjang={jenjang}
                subjectId={selectedSubject?.id || ''}
                chapterId={isStsSas ? undefined : selectedChapter?.id}
                availableTps={
                  isStsSas
                    ? chapters.flatMap((c) => c.tujuan_pembelajaran || [])
                    : activeTps
                }
                questions={customOverrides.butir_soal_kustom || []}
                onChangeQuestions={(nextQs) =>
                  onChangeCustomOverrides({
                    ...customOverrides,
                    butir_soal_kustom: nextQs,
                  })
                }
              />
            </>
          )}

          {/* Card Khusus 5: LKPD Mandiri (Aktivitas 3M & Tugas Siswa) */}
          {isLkpd && (
            <div className="clay-card p-5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
                <div>
                  <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800">
                    2. Aktivitas Pembelajaran Mendalam (3M) &amp; Tugas LKPD
                  </h2>
                  <p className="text-[11px] font-medium text-slate-500">
                    Kustomisasi instruksi lembar kerja siswa siap cetak.
                  </p>
                </div>
              </div>

              <div className="mt-4 space-y-3.5">
                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Tahap 1: Memahami (Instruksi Aktivitas Konseptual)
                  </label>
                  <textarea
                    rows={2}
                    value={
                      customOverrides.langkah_inti_memahami?.[0] ||
                      selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.memahami ||
                      `Membaca dan memahami konsep inti pada materi ${selectedChapter?.judul_bab || selectedSubject?.nama_mapel}.`
                    }
                    onChange={(e) =>
                      onChangeCustomOverrides({
                        ...customOverrides,
                        langkah_inti_memahami: [e.target.value],
                      })
                    }
                    className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Tahap 2: Mengaplikasi (Instruksi Studi Kasus / Praktik)
                  </label>
                  <textarea
                    rows={2}
                    value={
                      customOverrides.langkah_inti_mengaplikasi?.[0] ||
                      selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.mengaplikasi ||
                      'Mengerjakan studi kasus atau praktik pemecahan masalah secara terstruktur.'
                    }
                    onChange={(e) =>
                      onChangeCustomOverrides({
                        ...customOverrides,
                        langkah_inti_mengaplikasi: [e.target.value],
                      })
                    }
                    className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-xs font-bold text-slate-700">
                    Tahap 3: Merefleksi (Refleksi Pemahaman Diri Siswa)
                  </label>
                  <textarea
                    rows={2}
                    value={
                      customOverrides.langkah_inti_merefleksi?.[0] ||
                      selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.merefleksi ||
                      'Menuliskan kesimpulan dan refleksi pemahaman diri setelah aktivitas.'
                    }
                    onChange={(e) =>
                      onChangeCustomOverrides({
                        ...customOverrides,
                        langkah_inti_merefleksi: [e.target.value],
                      })
                    }
                    className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Card Khusus: Editor Tujuan Pembelajaran (Hanya untuk Layanan yang Memerlukan Editor TP) */}
          {(isModulAjar || isCpTp || isAtp || isKktp) && (
            <div className="clay-card p-5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
                <div>
                  <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800">
                    {isModulAjar
                      ? '4. Editor Tujuan Pembelajaran (TP) Bab Terpilih'
                      : isKktp
                      ? '4. Editor Butir Tujuan Pembelajaran & KKTP'
                      : '4. Editor Capaian & Tujuan Pembelajaran (TP)'}
                  </h2>
                  <p className="text-[11px] font-medium text-slate-500">
                    Tambah, ubah, atau hapus butir TP sesuai kebutuhan kurikulum Anda.
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
          )}

          {/* Card Khusus 7: Kustomisasi Isi Dokumen & Pedagogis (KHUSUS MODUL AJAR) */}
          {isModulAjar && (
            <div className="clay-card p-5">
              <button
                type="button"
                onClick={() => setShowPedagogicalEditor((v) => !v)}
                className="flex w-full items-center justify-between text-left"
              >
                <div>
                  <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800">
                    5. Kustomisasi Isi Dokumen &amp; Pedagogis
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
          )}

          {/* Card Khusus 5: Editor Soal Asesmen & Lampiran (KHUSUS MODUL AJAR) */}
          {isModulAjar && (
            <div className="clay-card p-5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
                <div>
                  <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800 flex items-center gap-2">
                    6. Lampiran, Asesmen &amp; Rubrik 8 Dimensi
                  </h2>
                </div>
              </div>

              <div className="mt-4 space-y-4">
                {/* 1. SEKSI ASESMEN 3 TAHAP */}
                <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-blue-100 text-blue-800 text-xs font-bold">
                        A
                      </span>
                      <h3 className="text-xs font-extrabold text-slate-800">
                        Instrumen Asesmen Pembelajaran (Awal, Proses &amp; Akhir)
                      </h3>
                    </div>
                    <span className="text-[10px] text-slate-500 font-medium">Formatif &amp; Sumatif 3 Tahap</span>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="mb-1 block text-[11px] font-bold text-slate-700">
                        Soal Asesmen Awal / Diagnostik (1 baris per butir)
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
                        placeholder="Tuliskan pertanyaan pemantik / diagnostik awal materi..."
                      />
                    </div>

                    <div>
                      <label className="mb-1 block text-[11px] font-bold text-slate-700">
                        Soal Asesmen Proses / Formatif (1 baris per butir)
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
                        placeholder="Tuliskan tugas / latihan terbimbing selama proses KBM..."
                      />
                    </div>

                    <div>
                      <label className="mb-1 block text-[11px] font-bold text-slate-700">
                        Soal Asesmen Akhir / Sumatif (1 baris per butir)
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
                        placeholder="Tuliskan soal evaluasi akhir bab..."
                      />
                    </div>
                  </div>
                </div>

                {/* 2. SEKSI LKPD 3M */}
                <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-emerald-100 text-emerald-800 text-xs font-bold">
                        B
                      </span>
                      <h3 className="text-xs font-extrabold text-slate-800">
                        Lampiran Lembar Kerja Peserta Didik (LKPD - Deep Learning 3M)
                      </h3>
                    </div>
                    <span className="text-[10px] text-slate-500 font-medium">Memahami, Mengaplikasi, Merefleksi</span>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="mb-1 block text-[11px] font-bold text-slate-700">
                        Judul LKPD
                      </label>
                      <input
                        type="text"
                        value={
                          customOverrides.judul_lkpd ??
                          selectedChapter?.modul_ajar_template?.lampiran?.lkpd?.judul_lkpd ??
                          `LKPD: ${selectedChapter?.judul_bab || 'Materi Pokok'} (Deep Learning 3M)`
                        }
                        onChange={(e) =>
                          onChangeCustomOverrides({
                            ...customOverrides,
                            judul_lkpd: e.target.value,
                          })
                        }
                        className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                      />
                    </div>

                    <div>
                      <label className="mb-1 block text-[11px] font-bold text-slate-700">
                        Tujuan Aktivitas LKPD
                      </label>
                      <input
                        type="text"
                        value={
                          customOverrides.tujuan_lkpd ??
                          selectedChapter?.modul_ajar_template?.lampiran?.lkpd?.tujuan_aktivitas ??
                          `Mengembangkan penguasaan konsep dan pemecahan masalah materi ${selectedChapter?.judul_bab || selectedSubject?.nama_mapel || ''}.`
                        }
                        onChange={(e) =>
                          onChangeCustomOverrides({
                            ...customOverrides,
                            tujuan_lkpd: e.target.value,
                          })
                        }
                        className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                      />
                    </div>

                    <div>
                      <label className="mb-1 block text-[11px] font-bold text-slate-700">
                        Petunjuk Pengerjaan
                      </label>
                      <textarea
                        rows={2}
                        value={
                          customOverrides.petunjuk_lkpd ??
                          "1. Berdoalah sebelum memulai kegiatan bersama anggota kelompok Anda.\n2. Bacalah dengan cermat instruksi pemecahan masalah dan bahan ajar yang diberikan.\n3. Bekerjasamalah secara aktif dan selesaikan tugas-tugas di bawah ini dengan tepat waktu."
                        }
                        onChange={(e) =>
                          onChangeCustomOverrides({
                            ...customOverrides,
                            petunjuk_lkpd: e.target.value,
                          })
                        }
                        className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                      />
                    </div>

                    <div className="space-y-2 pt-1 border-t border-slate-100">
                      <p className="text-[11px] font-extrabold uppercase text-slate-700">
                        Tugas Pembelajaran Mendalam (Deep Learning 3M):
                      </p>
                      <div>
                        <label className="mb-0.5 block text-[10px] font-bold text-slate-600">
                          1. Tahap Memahami (Eksplorasi Konsep Inti)
                        </label>
                        <textarea
                          rows={2}
                          value={
                            customOverrides.tugas_lkpd_memahami ??
                            customOverrides.langkah_inti_memahami?.[0] ??
                            selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.memahami ??
                            `Pahamilah konsep dasar mengenai ${selectedChapter?.judul_bab || selectedSubject?.nama_mapel}. Tuliskan intisari pengertian dan prinsip utamanya!`
                          }
                          onChange={(e) =>
                            onChangeCustomOverrides({
                              ...customOverrides,
                              tugas_lkpd_memahami: e.target.value,
                            })
                          }
                          className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                        />
                      </div>

                      <div>
                        <label className="mb-0.5 block text-[10px] font-bold text-slate-600">
                          2. Tahap Mengaplikasi (Praktik / Kasus Kontekstual)
                        </label>
                        <textarea
                          rows={2}
                          value={
                            customOverrides.tugas_lkpd_mengaplikasi ??
                            customOverrides.langkah_inti_mengaplikasi?.[0] ??
                            selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.mengaplikasi ??
                            `Diskusikan bersama kelompok studi kasus kontekstual penerapan ${selectedChapter?.judul_bab || selectedSubject?.nama_mapel}. Tuliskan langkah-langkah solusinya!`
                          }
                          onChange={(e) =>
                            onChangeCustomOverrides({
                              ...customOverrides,
                              tugas_lkpd_mengaplikasi: e.target.value,
                            })
                          }
                          className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                        />
                      </div>

                      <div>
                        <label className="mb-0.5 block text-[10px] font-bold text-slate-600">
                          3. Tahap Merefleksi (Evaluasi Diri &amp; Kesimpulan)
                        </label>
                        <textarea
                          rows={2}
                          value={
                            customOverrides.tugas_lkpd_merefleksi ??
                            customOverrides.langkah_inti_merefleksi?.[0] ??
                            selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.merefleksi ??
                            "Simpulkan manfaat pembelajaran hari ini dan hal apa yang masih perlu diperdalam pada pertemuan selanjutnya!"
                          }
                          onChange={(e) =>
                            onChangeCustomOverrides({
                              ...customOverrides,
                              tugas_lkpd_merefleksi: e.target.value,
                            })
                          }
                          className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* 3. SEKSI RUBRIK 8 DIMENSI PROFIL LULUSAN */}
                <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-amber-100 text-amber-800 text-xs font-bold">
                        C
                      </span>
                      <h3 className="text-xs font-extrabold text-slate-800">
                        Rubrik 8 Dimensi Profil Lulusan (Permendikdasmen No. 10/2025)
                      </h3>
                    </div>
                    <button
                      type="button"
                      onClick={handleResetDplDefault}
                      className="font-bold text-xs text-blue-700 hover:underline flex items-center gap-1"
                    >
                      <RotateCcw className="h-3 w-3" />
                      <span>Reset Standar BSKAP</span>
                    </button>
                  </div>

                  <p className="text-[11px] text-slate-600 font-medium">
                    Pilih dimensi amatan dan sesuaikan indikator deskriptor perilaku di kelas:
                  </p>

                  <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                    {effectiveRubrikDpl.map((dpl, idx) => (
                      <div
                        key={dpl.no}
                        className={`rounded-xl border p-3 transition-colors ${
                          dpl.is_active ? 'border-slate-300 bg-slate-50/50' : 'border-slate-200 bg-slate-100/60 opacity-60'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <label className="flex cursor-pointer items-center gap-2 text-xs font-bold text-slate-800">
                            <input
                              type="checkbox"
                              checked={dpl.is_active}
                              onChange={() => handleToggleDplActive(idx)}
                              className="h-3.5 w-3.5 rounded border-slate-300 text-blue-700"
                            />
                            <span>{dpl.no}. {dpl.nama_dimensi}</span>
                          </label>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${dpl.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-500'}`}>
                            {dpl.is_active ? 'Aktif Dinilai' : 'Tidak Dinilai'}
                          </span>
                        </div>
                        {dpl.is_active && (
                          <textarea
                            rows={2}
                            value={dpl.indikator}
                            onChange={(e) => handleUpdateDplIndicator(idx, e.target.value)}
                            placeholder="Rumusan indikator amatan perilaku di kelas..."
                            className="clay-input w-full px-2.5 py-1.5 text-[11px] font-medium text-slate-800 mt-1"
                          />
                        )}
                      </div>
                    ))}
                  </div>
                  <p className="text-[10px] text-slate-500 italic">
                    * Indikator rubrik ini akan dicantumkan pada tabel lampiran Modul Ajar untuk memandu penilaian autentik guru.
                  </p>
                </div>
              </div>
            </div>
          )}

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
                <span>Menyusun Dokumen...</span>
              </>
            ) : (
              <>
                <FileDown className="h-4 w-4" />
                <span>Download Dokumen</span>
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
            {/* Preview Toolbar (Clean MS Word-style controls) */}
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2">
              <div className="flex flex-wrap items-center gap-2">
                <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-0.5 text-[11px] font-bold">
                  <button
                    type="button"
                    onClick={() => handleSwitchPreviewMode('word')}
                    className={`rounded-md px-2.5 py-1 transition ${
                      previewMode === 'word'
                        ? 'bg-white text-blue-700 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Live Layout
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSwitchPreviewMode('pdf')}
                    className={`rounded-md px-2.5 py-1 transition ${
                      previewMode === 'pdf'
                        ? 'bg-white text-blue-700 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    PDF Asli
                  </button>
                </div>

                <span className="text-[11px] font-bold text-slate-600">
                  {previewPageCount} Hal • {paperSize} ({pageOrientation === 'landscape' ? 'Landscape' : 'Portrait'})
                </span>
              </div>

              <div className="flex items-center gap-1">
                {previewMode === 'pdf' && (
                  <button
                    type="button"
                    onClick={handleFetchPdfPreview}
                    title="Muat ulang PDF"
                    className="rounded-lg border border-slate-200 bg-white p-1.5 text-slate-600 hover:bg-slate-50"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${isLoadingPdfPreview ? 'animate-spin' : ''}`} />
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => handleStepZoom(-0.1)}
                  title="Perkecil"
                  className="rounded-lg border border-slate-200 bg-white p-1.5 text-slate-600 hover:bg-slate-50"
                >
                  <ZoomOut className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewZoom('fit')}
                  className={`rounded-lg border px-2 py-1 text-[11px] font-bold ${
                    previewZoom === 'fit'
                      ? 'border-blue-600 bg-blue-50 text-blue-700'
                      : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  Fit
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewZoom(1)}
                  title="Ukuran 100%"
                  className={`rounded-lg border px-2 py-1 text-[11px] font-bold ${
                    previewZoom === 1
                      ? 'border-blue-600 bg-blue-50 text-blue-700'
                      : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <Maximize2 className="h-3 w-3 inline mr-0.5" />
                  100%
                </button>
                <button
                  type="button"
                  onClick={() => handleStepZoom(0.1)}
                  title="Perbesar"
                  className="rounded-lg border border-slate-200 bg-white p-1.5 text-slate-600 hover:bg-slate-50"
                >
                  <ZoomIn className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            {/* Hybrid Preview Viewport: Word Auto-Paginator or Watermarked PDF Canvas */}
            {previewMode === 'pdf' ? (
              <PdfCanvasPreview
                pdfBuffer={pdfPreviewBuffer}
                isLoading={isLoadingPdfPreview}
                errorMsg={pdfPreviewError}
                paperSize={paperSize}
                orientation={pageOrientation}
                zoom={previewZoom}
                onRetry={handleFetchPdfPreview}
                onPageCountChange={setPreviewPageCount}
              />
            ) : (
              <WordPagePaginator
                paperSize={paperSize}
                orientation={pageOrientation}
                zoom={previewZoom}
                contentKey={paginatorContentKey}
                onPageCountChange={setPreviewPageCount}
              >
                {isExamService ? (
                  renderExamPreviewFlow()
                ) : (
                  <>
                    {renderOfficialKop()}

                    {/* 2. DYNAMIC DOCUMENT BODY BY SERVICE_ID (Modularized per Cluster) */}
                    {(activeService.id === '03_cp_tp' ||
                      activeService.id === '04_atp' ||
                      activeService.id === '05_prota' ||
                      activeService.id === '06_promes' ||
                      activeService.id === '07_kktp' ||
                      activeService.id === '08_modul_ajar') && (
                      <CurriculumPlanningPreviews
                        serviceId={activeService.id}
                        jenjang={jenjang}
                        kelas={kelas}
                        semester={semester}
                        faseCode={faseCode}
                        faseLabel={faseLabel}
                        selectedSubject={selectedSubject}
                        selectedChapter={selectedChapter}
                        allSubjectChapters={allSubjectChapters}
                        currentSemesterChapters={currentSemesterChapters}
                        teacher={teacher}
                        activeCpElements={activeCpElements}
                        officialElements={officialElements}
                        activeTps={activeTps}
                        activeDimensions={activeDimensions}
                        activeDplList={activeDplList}
                        currentAlokasiJp={currentAlokasiJp}
                        pertemuanCount={pertemuanCount}
                        jpPerMinggu={jpPerMinggu}
                        durasiMenitJp={durasiMenitJp}
                        modelPembelajaran={modelPembelajaran}
                        monthLabels={monthLabels}
                        includeLkpd={includeLkpd}
                        includeAsesmen={includeAsesmen}
                        includeRubrik={includeRubrik}
                        effectiveKesiapanMurid={effectiveKesiapanMurid}
                        effectiveKarakteristikMateri={effectiveKarakteristikMateri}
                        effectiveLintasDisiplin={effectiveLintasDisiplin}
                        effectiveTopikKontekstual={effectiveTopikKontekstual}
                        effectivePemantik={effectivePemantik}
                        effectiveSoalAwal={effectiveSoalAwal}
                        effectiveSoalProses={effectiveSoalProses}
                        effectiveSoalAkhir={effectiveSoalAkhir}
                        customOverrides={customOverrides}
                      />
                    )}

                    {activeService.id === '09_lkpd' && (
                      <AssessmentLkpdPreviews
                        selectedSubject={selectedSubject}
                        selectedChapter={selectedChapter}
                        activeTps={activeTps}
                      />
                    )}

                    {(activeService.id === '13_presensi' ||
                      activeService.id === '14_jurnal_mengajar' ||
                      activeService.id === '15_daftar_nilai') && (
                      <ClassroomTrackingPreviews
                        serviceId={activeService.id}
                        kelas={kelas}
                        semester={semester}
                        selectedSubject={selectedSubject}
                        currentSemesterChapters={currentSemesterChapters}
                        teacher={teacher}
                        activeClassroomRombel={activeClassroom?.nama_rombel}
                        effectiveStudents={effectiveStudents}
                        customOverrides={customOverrides}
                      />
                    )}

                    {/* 3. LEMBAR PENGESAHAN RESMI */}
                    {renderOfficialPengesahan()}
                  </>
                )}
              </WordPagePaginator>
            )}
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

      {/* Modal Editor Bab & TP Komprehensif (Sprint 34) */}
      <ChapterEditorModal
        isOpen={isChapterEditorOpen}
        chapterToEdit={chapterEditing}
        defaultSemester={semester}
        suggestedChapterNumber={(activeCustomChapters?.length || 0) + 1}
        availableCpElements={activeCpElements}
        onSave={handleSaveChapterFromModal}
        onClose={() => {
          setIsChapterEditorOpen(false);
          setChapterEditing(null);
        }}
      />

      {/* Modal Editor Elemen Capaian Pembelajaran (CP) Multi-Service */}
      <CpElementEditorModal
        isOpen={isCpEditorOpen}
        elementToEdit={cpEditing}
        suggestedCode={`EL-${String(activeCpElements.length + 1).padStart(2, '0')}`}
        onSave={handleSaveCpFromModal}
        onClose={() => {
          setIsCpEditorOpen(false);
          setCpEditing(null);
        }}
      />
    </section>
  );
};
