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
} from 'lucide-react';
import {
  ChapterTopic,
  CurriculumSubject,
  CustomChapterItem,
  CustomCpElementItem,
  CustomDocumentOverrides,
  CustomRubrikDplItem,
  CustomTpItem,
  GenerationMode,
  Jenjang,
  OutputFormat,
  PaperSize,
  ServiceCatalogItem,
  ServiceId,
  StudentOverrideItem,
  TeacherProfile,
} from '../../types';
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

  const activeCoreServices = CORE_SERVICES.filter((s) => !s.isComingSoon);

  const paperSizeClass = paperSize === 'A4' ? 'paper-sheet-a4' : 'paper-sheet-f4';

  const renderWatermark = () => (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 z-20 flex items-center justify-center overflow-hidden opacity-[0.045]"
    >
      <span className="-rotate-30 whitespace-nowrap text-3xl font-black tracking-[0.25em] text-slate-900 sm:text-5xl">
        PREVIEW DOKUMEN
      </span>
    </div>
  );

  const renderOfficialKop = () => (
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
  );

  const renderOfficialPengesahan = () => (
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
  );

  const renderPaperFooter = (pageStr: string) => (
    <div className="paper-sheet-footer">
      <span>Standar Naskah Dinas: Margin Kiri 3.0cm • Atas 2.5cm • Kanan 2.0cm • Bawah 2.5cm | Font: Arial</span>
      <span className="font-bold text-slate-600">{pageStr}</span>
    </div>
  );

  const renderExamPreviewSheets = () => {
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
        {/* LEMBAR 1: NASKAH SOAL SISWA */}
        <div className={`paper-sheet ${paperSizeClass} relative w-full p-6 sm:p-8 lg:p-10 flex flex-col justify-between`}>
          {renderWatermark()}
          <div className="pointer-events-none relative z-10 flex-1">
            {renderOfficialKop()}

            <div className="mt-4 text-center">
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

            {/* Kotak Identitas Ujian Siswa */}
            <div className="mt-3 grid grid-cols-2 gap-2 rounded border border-slate-200 bg-slate-50/50 p-2.5 text-[11px]">
              <div className="space-y-0.5">
                <p><span className="font-semibold text-slate-500">Mata Pelajaran:</span> {selectedSubject?.nama_mapel}</p>
                <p><span className="font-semibold text-slate-500">Kelas / Fase:</span> Kelas {kelas} / {faseLabel}</p>
                <p><span className="font-semibold text-slate-500">Materi Pokok:</span> {selectedChapter?.judul_bab || 'Materi Pokok Pembelajaran'}</p>
              </div>
              <div className="space-y-0.5">
                <p><span className="font-semibold text-slate-500">Hari, Tanggal:</span> ............................................</p>
                <p><span className="font-semibold text-slate-500">Alokasi Waktu:</span> {isKuis ? '30 Menit' : isSumatifBab ? '60 Menit' : '90 Menit'}</p>
                <p><span className="font-semibold text-slate-500">Nama Siswa / No:</span> ............................................</p>
              </div>
            </div>

            {/* Petunjuk Umum Pengerjaan */}
            <div className="mt-3 rounded border border-slate-200 bg-slate-50 p-2.5 text-[11px] leading-relaxed text-slate-700">
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
              <div className="mt-4 space-y-3">
                <h4 className="font-bold text-slate-900 border-b border-slate-200 pb-1 text-xs uppercase">
                  A. SOAL PILIHAN GANDA (Pilihlah salah satu jawaban yang paling tepat)
                </h4>
                {pgQuestions.map((q, pgIdx) => (
                  <div key={pgIdx} className="space-y-1 text-xs">
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
              </div>
            )}

            {/* Bagian B: Soal Essai */}
            {essaiQuestions.length > 0 && (
              <div className="mt-4 space-y-3">
                <h4 className="font-bold text-slate-900 border-b border-slate-200 pb-1 text-xs uppercase">
                  B. SOAL ESSAI (Jawablah pertanyaan berikut dengan singkat, jelas, dan tepat)
                </h4>
                {essaiQuestions.map((q, esIdx) => (
                  <div key={esIdx} className="space-y-1 text-xs">
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
              </div>
            )}
          </div>
          {renderPaperFooter(`Kertas ${paperSize} • Lembar 1 dari 2 (Naskah Siswa)`)}
        </div>

        {/* LEMBAR 2: PEGANGAN GURU (KUNCI JAWABAN & KISI-KISI) */}
        <div className={`paper-sheet ${paperSizeClass} relative w-full p-6 sm:p-8 lg:p-10 flex flex-col justify-between`}>
          {renderWatermark()}
          <div className="pointer-events-none relative z-10 flex-1">
            {/* Sub-KOP Ringkas Dokumen Pegangan Guru */}
            <div className="border-b-2 border-slate-900 pb-2 text-center">
              <p className="text-[10px] font-bold uppercase tracking-wide text-slate-600">
                PEMERINTAH {(teacher.kabupaten_kota || 'KABUPATEN/KOTA').toUpperCase()} — DINAS PENDIDIKAN
              </p>
              <p className="text-sm font-extrabold uppercase text-slate-900">
                {teacher.nama_sekolah || 'NAMA SATUAN PENDIDIKAN'}
              </p>
              <p className="mt-0.5 text-xs font-bold uppercase tracking-wider text-blue-900 bg-blue-50 py-0.5 rounded">
                DOKUMEN PEGANGAN GURU — KUNCI JAWABAN, PEDOMAN PENSKORAN &amp; KISI-KISI
              </p>
              <p className="mt-0.5 text-[10px] text-slate-500">
                {selectedSubject?.nama_mapel} • {jenjang} Kelas {kelas} • Semester {semester} • Paket {customOverrides.paket_soal || 'A'}
              </p>
            </div>

            {/* Bagian 1: Kunci Jawaban & Pedoman Penskoran */}
            <div className="mt-4 space-y-2 text-xs">
              <h3 className="font-extrabold uppercase text-slate-900">
                1. KUNCI JAWABAN DAN PEDOMAN PENSKORAN
              </h3>
              <div className="paper-table-container mt-1.5">
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
              <p className="text-[11px] text-slate-600">
                Rumus Nilai Akhir = (Total Skor Diperoleh / Total Skor Maksimal) × 100
                {isStsSas
                  ? ' • Dilengkapi Kartu Soal & Lembar Jawab Komputer (LJK) pada file unduhan Word & PDF.'
                  : ''}
              </p>
            </div>

            {/* Bagian 2: Tabel Kisi-Kisi Penulisan Soal (7 Kolom BSKAP) */}
            <div className="mt-4 space-y-2 text-xs">
              <h3 className="font-extrabold uppercase text-slate-900">
                2. TABEL KISI-KISI PENULISAN SOAL (BSKAP NO. 046/H/KR/2025)
              </h3>
              <div className="paper-table-container mt-1.5">
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
            </div>

            {/* Bagian 3: Lembar Pengesahan Resmi Guru */}
            {renderOfficialPengesahan()}
          </div>
          {renderPaperFooter(`Kertas ${paperSize} • Lembar 2 dari 2 (Pegangan Guru)`)}
        </div>
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
          {/* Mode Banner & Crash-Safe Status (Sprint 34) */}
          <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ${
                    generationMode === 'template'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-slate-800 text-white'
                  }`}
                >
                  {generationMode === 'template' ? 'Gunakan Template' : 'Buat Manual'}
                </span>
                <span className="text-xs text-slate-600">
                  {generationMode === 'template'
                    ? 'Standar BSKAP No. 046/2025 & SIBI (dapat dimodifikasi bebas)'
                    : 'Penyusunan mandiri / kustom'}
                </span>
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
                    Tersimpan di browser
                  </span>
                )}

                <button
                  type="button"
                  onClick={handleResetCurriculum}
                  title={generationMode === 'template' ? 'Reset ke Template BSKAP 2025' : 'Bersihkan seluruh bab'}
                  className="rounded-lg border border-slate-200 px-2 py-1 text-[11px] font-bold text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors"
                >
                  <RotateCcw className="inline mr-1 h-3 w-3" />
                  {generationMode === 'template' ? 'Reset Template' : 'Bersihkan'}
                </button>

                <button
                  type="button"
                  onClick={onBackToCatalog}
                  className="rounded-lg border border-blue-200 bg-blue-50 px-2 py-1 text-[11px] font-bold text-blue-700 hover:bg-blue-100 transition-colors"
                >
                  Ganti Mode
                </button>
              </div>
            </div>
          </div>

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
                    1. Capaian Pembelajaran (CP) Berdasarkan Elemen
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
                    2. Lingkup Materi / Bab &amp; Alokasi JP
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
                        min={15}
                        max={240}
                        value={customOverrides.alokasi_waktu_menit ?? 90}
                        onChange={(e) =>
                          onChangeCustomOverrides({
                            ...customOverrides,
                            alokasi_waktu_menit: Math.max(15, Math.min(240, Number(e.target.value) || 90)),
                          })
                        }
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
                        min={10}
                        max={180}
                        value={customOverrides.alokasi_waktu_menit ?? (isKuis ? 20 : 60)}
                        onChange={(e) =>
                          onChangeCustomOverrides({
                            ...customOverrides,
                            alokasi_waktu_menit: Math.max(10, Math.min(180, Number(e.target.value) || 30)),
                          })
                        }
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
                      ? '3. Editor Tujuan Pembelajaran (TP) Bab Terpilih'
                      : isKktp
                      ? '3. Editor Butir Tujuan Pembelajaran & KKTP'
                      : '3. Editor Capaian & Tujuan Pembelajaran (TP)'}
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
                    4. Kustomisasi Isi Dokumen &amp; Pedagogis
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
                    5. Lampiran, Asesmen &amp; Rubrik 8 Dimensi
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
            {/* Preview Header Bar */}
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5">
              <div className="flex items-center gap-2">
                <Eye className="h-4 w-4 text-blue-700" />
                <span className="text-xs font-extrabold uppercase tracking-wider text-slate-800">
                  Live Document Preview — Kertas {paperSize} ({formatExtLabel})
                  {isExamService && ' • 2 Lembar Terpisah'}
                </span>
              </div>
              <span className="text-[11px] font-semibold text-slate-500">
                {isExamService
                  ? 'Lembar 1: Naskah Soal Siswa | Lembar 2: Pegangan Guru & Kisi-Kisi'
                  : 'Perubahan pada form di samping langsung memperbarui dokumen ini'}
              </span>
            </div>

            {/* Scrollable Multi-Sheet Canvas Container (Anti-Select & Anti-Copy-Paste Protected) */}
            <div
              onCopy={(e) => e.preventDefault()}
              onCut={(e) => e.preventDefault()}
              onContextMenu={(e) => e.preventDefault()}
              onDragStart={(e) => e.preventDefault()}
              className="paper-canvas preview-protected w-full select-none"
            >
              {isExamService ? (
                renderExamPreviewSheets()
              ) : (
                <div
                  className={`paper-sheet ${paperSizeClass} preview-protected relative w-full min-w-0 max-w-full select-none p-6 sm:p-8 lg:p-10 flex flex-col justify-between`}
                >
                  {renderWatermark()}
                  <div className="pointer-events-none relative z-10 flex-1">
                    {renderOfficialKop()}

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
                          {activeCpElements.map((el, i) => (
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
                          {activeCpElements.map((el, i) => (
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

                    {/* H. Lampiran 1: Lembar Kerja Peserta Didik (LKPD) */}
                    {includeLkpd && (
                      <div className="mt-6 border-t-2 border-dashed border-slate-300 pt-5">
                        <div className="text-center mb-3">
                          <h4 className="text-sm font-extrabold uppercase text-slate-900">
                            {customOverrides.judul_lkpd || selectedChapter?.modul_ajar_template?.lampiran?.lkpd?.judul_lkpd || 'LAMPIRAN 1: LEMBAR KERJA PESERTA DIDIK (LKPD)'}
                          </h4>
                          <p className="text-xs font-bold text-slate-700">
                            {customOverrides.tujuan_lkpd || selectedChapter?.modul_ajar_template?.lampiran?.lkpd?.tujuan_aktivitas || `Materi: ${selectedChapter?.judul_bab || 'Materi Pokok'} — Pendekatan Deep Learning 3M`}
                          </p>
                        </div>

                        {/* Identitas Kelompok LKPD */}
                        <div className="paper-table-container">
                          <table className="paper-table">
                            <tbody>
                              <tr>
                                <th className="w-1/4 text-left">Nama Kelompok / Kelas</th>
                                <td>........................................................... / Kelas {kelas}</td>
                                <th className="w-1/4 text-left">Hari, Tanggal</th>
                                <td>...........................................................</td>
                              </tr>
                              <tr>
                                <th className="text-left">Nama Anggota</th>
                                <td colSpan={3}>
                                  1. ........................................................... 2. ...........................................................<br />
                                  3. ........................................................... 4. ...........................................................
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>

                        {/* Petunjuk & Langkah Kerja LKPD */}
                        <div className="mt-3 space-y-2">
                          <p className="font-bold text-slate-900">Petunjuk Pengerjaan:</p>
                          {customOverrides.petunjuk_lkpd ? (
                            <ol className="list-decimal pl-4 space-y-1 text-[11px] text-slate-700">
                              {customOverrides.petunjuk_lkpd.split('\n').filter((l) => l.trim()).map((line, idx) => (
                                <li key={idx}>{line.replace(/^\d+[\.\)]\s*/, '')}</li>
                              ))}
                            </ol>
                          ) : (
                            <ol className="list-decimal pl-4 space-y-1 text-[11px] text-slate-700">
                              <li>Berdoalah sebelum memulai kegiatan bersama anggota kelompok Anda.</li>
                              <li>Bacalah dengan cermat setiap instruksi pemecahan masalah dan bahan ajar yang diberikan.</li>
                              <li>Bekerjasamalah secara aktif dan selesaikan tugas-tugas di bawah ini dengan tepat waktu.</li>
                            </ol>
                          )}
                        </div>

                        {/* Tabel Aktivitas LKPD 3M */}
                        <div className="paper-table-container mt-3">
                          <table className="paper-table">
                            <thead>
                              <tr>
                                <th className="w-12 text-center">No</th>
                                <th className="w-1/3">Tahap Aktivitas (3M)</th>
                                <th>Instruksi Tugas &amp; Lembar Kerja Siswa</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr>
                                <td className="text-center font-bold">1</td>
                                <td className="font-bold">
                                  Memahami<br />
                                  <span className="text-[10px] font-normal text-slate-500">(Eksplorasi Konsep)</span>
                                </td>
                                <td>
                                  {customOverrides.tugas_lkpd_memahami ||
                                    customOverrides.langkah_inti_memahami?.[0] ||
                                    selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.memahami ||
                                    `Pahamilah konsep dasar mengenai ${selectedChapter?.judul_bab || selectedSubject?.nama_mapel}. Tuliskan intisari pengertian dan prinsip utamanya pada lembar ini!`}
                                  <div className="mt-2 h-14 border border-dashed border-slate-300 rounded p-1.5 text-[10px] text-slate-400 italic">
                                    [Ruang Jawaban / Intisari Pemahaman Konsep Siswa]
                                  </div>
                                </td>
                              </tr>
                              <tr>
                                <td className="text-center font-bold">2</td>
                                <td className="font-bold">
                                  Mengaplikasi<br />
                                  <span className="text-[10px] font-normal text-slate-500">(Investigasi &amp; Praktik)</span>
                                </td>
                                <td>
                                  {customOverrides.tugas_lkpd_mengaplikasi ||
                                    customOverrides.langkah_inti_mengaplikasi?.[0] ||
                                    selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.mengaplikasi ||
                                    `Diskusikan bersama kelompok studi kasus kontekstual penerapan ${selectedChapter?.judul_bab}. Temukan solusi dan langkah-langkah pemecahannya secara logis!`}
                                  <div className="mt-2 h-16 border border-dashed border-slate-300 rounded p-1.5 text-[10px] text-slate-400 italic">
                                    [Ruang Analisis &amp; Sketsa Solusi Pemecahan Masalah]
                                  </div>
                                </td>
                              </tr>
                              <tr>
                                <td className="text-center font-bold">3</td>
                                <td className="font-bold">
                                  Merefleksi<br />
                                  <span className="text-[10px] font-normal text-slate-500">(Kesimpulan &amp; Evaluasi)</span>
                                </td>
                                <td>
                                  {customOverrides.tugas_lkpd_merefleksi ||
                                    customOverrides.langkah_inti_merefleksi?.[0] ||
                                    selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.merefleksi ||
                                    'Simpulkan manfaat pembelajaran hari ini dan hal apa yang masih perlu diperdalam pada pertemuan selanjutnya!'}
                                  <div className="mt-2 h-12 border border-dashed border-slate-300 rounded p-1.5 text-[10px] text-slate-400 italic">
                                    [Ruang Refleksi Diri &amp; Kesimpulan Bersama]
                                  </div>
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* I. Lampiran 2: Rubrik Asesmen 8 Dimensi Profil Lulusan (Permendikdasmen No. 10/2025) */}
                    {includeRubrik && (
                      <div className="mt-6 border-t-2 border-dashed border-slate-300 pt-5">
                        <div className="text-center mb-3">
                          <h4 className="text-sm font-extrabold uppercase text-slate-900">
                            LAMPIRAN 2: RUBRIK PENILAIAN 8 DIMENSI PROFIL LULUSAN
                          </h4>
                          <p className="text-xs font-bold text-slate-700">
                            Standar Kompetensi Lulusan sesuai Permendikdasmen No. 10 Tahun 2025
                          </p>
                        </div>

                        <div className="paper-table-container">
                          <table className="paper-table text-[10.5px]">
                            <thead>
                              <tr>
                                <th className="w-8 text-center">No</th>
                                <th className="w-1/4">Dimensi Profil Lulusan</th>
                                <th>Indikator Perilaku Amatan di Kelas</th>
                                <th className="w-12 text-center">MB</th>
                                <th className="w-12 text-center">B</th>
                                <th className="w-12 text-center">BSH</th>
                                <th className="w-12 text-center">SB</th>
                              </tr>
                            </thead>
                            <tbody>
                              {activeDplList.map((dpl, idx) => (
                                <tr key={dpl.no || idx}>
                                  <td className="text-center font-bold">{idx + 1}</td>
                                  <td>
                                    <p className="font-bold text-slate-900">{dpl.nama_dimensi}</p>
                                  </td>
                                  <td>{dpl.indikator}</td>
                                  <td className="text-center font-mono text-[11px] text-slate-400">[ &nbsp; ]</td>
                                  <td className="text-center font-mono text-[11px] text-slate-400">[ &nbsp; ]</td>
                                  <td className="text-center font-mono text-[11px] text-slate-400">[ &nbsp; ]</td>
                                  <td className="text-center font-mono text-[11px] text-slate-400">[ &nbsp; ]</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        <div className="mt-2 space-y-1 text-[10px] text-slate-500 italic">
                          <p>
                            * Keterangan Skala: MB = Mulai Berkembang (Skor 1), B = Berkembang (Skor 2), BSH = Berkembang Sesuai Harapan (Skor 3), SB = Sangat Berkembang (Skor 4).
                          </p>
                          <p className="text-slate-600 font-medium">
                            Catatan / Rekomendasi Guru: ........................................................................................................................................
                          </p>
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
                          {activeCpElements.map((el, i) => (
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
                          {activeCpElements.map((el, i) => (
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

              {/* Service 13: Live Preview Presensi Siswa Bulanan */}
              {activeService.id === '13_presensi' && (
                <div className="mt-5 space-y-5 text-xs leading-relaxed">
                  <div className="text-center">
                    <h2 className="text-base font-extrabold uppercase text-slate-900">
                      PRESENSI DAN KEHADIRAN PESERTA DIDIK
                    </h2>
                    <p className="font-bold uppercase text-slate-700">
                      TAHUN AJARAN 2026/2027 — SEMESTER {semester}
                    </p>
                  </div>

                  {/* Identitas Metadata */}
                  <div className="paper-table-container">
                    <table className="paper-table">
                      <tbody>
                        <tr>
                          <th className="w-1/4 text-left">Mata Pelajaran</th>
                          <td className="w-1/4 font-semibold">{selectedSubject?.nama_mapel}</td>
                          <th className="w-1/4 text-left">Guru Pengampu</th>
                          <td className="w-1/4 font-semibold">{teacher.nama_guru || '-'}</td>
                        </tr>
                        <tr>
                          <th className="text-left">Kelas / Rombel</th>
                          <td className="font-semibold">{customOverrides.nama_rombel || activeClassroom?.nama_rombel || `Kelas ${kelas}`}</td>
                          <th className="text-left">Bulan Presensi</th>
                          <td className="font-semibold text-blue-700">{customOverrides.bulan_presensi || 'Agustus'}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  {/* Tabel Presensi Siswa */}
                  <div className="paper-table-container">
                    <table className="paper-table text-[11px]">
                      <thead>
                        <tr>
                          <th rowSpan={2} className="w-8 text-center">No</th>
                          <th rowSpan={2} className="w-20 text-center">NISN</th>
                          <th rowSpan={2} className="text-left min-w-[140px]">Nama Lengkap Siswa</th>
                          <th rowSpan={2} className="w-8 text-center">L/P</th>
                          <th colSpan={15} className="text-center bg-teal-700 text-white">
                            Tanggal Presensi Bulan {customOverrides.bulan_presensi || 'Agustus'} (Sampel Tgl 1 - 15)
                          </th>
                          <th colSpan={5} className="text-center bg-teal-800 text-white">
                            Rekapitulasi Kehadiran
                          </th>
                        </tr>
                        <tr>
                          {Array.from({ length: 15 }, (_, i) => (
                            <th key={i + 1} className="w-5 text-center font-mono text-[10px] bg-teal-600 text-white">
                              {i + 1}
                            </th>
                          ))}
                          <th className="w-7 text-center font-bold bg-teal-700 text-white" title="Hadir (Formula =COUNTIF)">H</th>
                          <th className="w-7 text-center font-bold bg-teal-700 text-white" title="Sakit (Formula =COUNTIF)">S</th>
                          <th className="w-7 text-center font-bold bg-teal-700 text-white" title="Izin (Formula =COUNTIF)">I</th>
                          <th className="w-7 text-center font-bold bg-teal-700 text-white" title="Alpa (Formula =COUNTIF)">A</th>
                          <th className="w-10 text-center font-bold bg-teal-800 text-white" title="Persentase Kehadiran">%</th>
                        </tr>
                      </thead>
                      <tbody>
                        {effectiveStudents.slice(0, 15).map((s: StudentOverrideItem, idx: number) => (
                          <tr key={idx}>
                            <td className="text-center font-bold">{s.nomor_absen || idx + 1}</td>
                            <td className="text-center font-mono text-[10px] text-slate-500">{s.nisn || '-'}</td>
                            <td className="font-semibold text-slate-900">{s.nama_lengkap}</td>
                            <td className="text-center font-bold">{s.jenis_kelamin || 'L'}</td>
                            {Array.from({ length: 15 }, (_, dayIdx) => (
                              <td key={dayIdx} className="text-center font-mono text-[10px] text-teal-800">
                                {dayIdx % 7 === 5 || dayIdx % 7 === 6 ? '•' : 'H'}
                              </td>
                            ))}
                            <td className="text-center font-mono font-bold text-teal-700">11</td>
                            <td className="text-center font-mono text-slate-500">0</td>
                            <td className="text-center font-mono text-slate-500">0</td>
                            <td className="text-center font-mono text-slate-500">0</td>
                            <td className="text-center font-mono font-bold text-teal-900 bg-teal-50">100%</td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot>
                        <tr className="bg-slate-100 font-bold border-t-2 border-slate-400">
                          <td colSpan={4} className="text-right pr-2 uppercase text-[10px]">Total Rekapitulasi Kelas (Formula Excel)</td>
                          <td colSpan={15} className="text-center text-[10px] text-slate-500 italic">Formula Aktif =COUNTIF(E10:AI10, "H") per baris</td>
                          <td className="text-center font-mono font-extrabold text-teal-800">=SUM</td>
                          <td className="text-center font-mono font-extrabold text-teal-800">=SUM</td>
                          <td className="text-center font-mono font-extrabold text-teal-800">=SUM</td>
                          <td className="text-center font-mono font-extrabold text-teal-800">=SUM</td>
                          <td className="text-center font-mono font-extrabold text-teal-900 bg-teal-100">=AVERAGE</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                  <p className="text-[11px] text-slate-500 italic">
                    * Dokumen unduhan (.xlsx) mencakup seluruh 31 hari penuh dengan formula aktif live, dapat dibuka dan dihitung otomatis di Microsoft Excel maupun Google Sheets.
                  </p>
                </div>
              )}

              {/* Service 15: Live Preview Buku Pengolahan Daftar Nilai */}
              {activeService.id === '15_daftar_nilai' && (
                <div className="mt-5 space-y-5 text-xs leading-relaxed">
                  <div className="text-center">
                    <h2 className="text-base font-extrabold uppercase text-slate-900">
                      BUKU DAFTAR NILAI PESERTA DIDIK
                    </h2>
                    <p className="font-bold uppercase text-slate-700">
                      KURIKULUM MERDEKA — TAHUN AJARAN 2026/2027 (SEMESTER {semester})
                    </p>
                  </div>

                  {/* Identitas Metadata */}
                  <div className="paper-table-container">
                    <table className="paper-table">
                      <tbody>
                        <tr>
                          <th className="w-1/4 text-left">Mata Pelajaran</th>
                          <td className="w-1/4 font-semibold">{selectedSubject?.nama_mapel}</td>
                          <th className="w-1/4 text-left">Guru Pengampu</th>
                          <td className="w-1/4 font-semibold">{teacher.nama_guru || '-'}</td>
                        </tr>
                        <tr>
                          <th className="text-left">Kelas / Rombel</th>
                          <td className="font-semibold">{customOverrides.nama_rombel || activeClassroom?.nama_rombel || `Kelas ${kelas}`}</td>
                          <th className="text-left">KKTP Minimum</th>
                          <td className="font-semibold text-blue-700">{customOverrides.kktp_nilai || 75} (Tuntas &ge; {customOverrides.kktp_nilai || 75})</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  {/* Tabel Daftar Nilai */}
                  <div className="paper-table-container">
                    <table className="paper-table text-[11px]">
                      <thead>
                        <tr>
                          <th rowSpan={2} className="w-8 text-center">No</th>
                          <th rowSpan={2} className="w-20 text-center">NISN</th>
                          <th rowSpan={2} className="text-left min-w-[140px]">Nama Lengkap Siswa</th>
                          <th rowSpan={2} className="w-8 text-center">L/P</th>
                          <th colSpan={5} className="text-center bg-blue-900 text-white">
                            Asesmen Formatif (Lingkup TP)
                          </th>
                          <th colSpan={3} className="text-center bg-blue-800 text-white">
                            Asesmen Sumatif
                          </th>
                          <th colSpan={3} className="text-center bg-teal-800 text-white">
                            Hasil Akhir &amp; Keterangan
                          </th>
                        </tr>
                        <tr>
                          <th className="w-10 text-center font-mono text-[10px] bg-blue-800 text-white">TP 1</th>
                          <th className="w-10 text-center font-mono text-[10px] bg-blue-800 text-white">TP 2</th>
                          <th className="w-10 text-center font-mono text-[10px] bg-blue-800 text-white">TP 3</th>
                          <th className="w-10 text-center font-mono text-[10px] bg-blue-800 text-white">TP 4</th>
                          <th className="w-12 text-center font-bold font-mono text-[10px] bg-blue-700 text-white" title="=AVERAGE">Rata F</th>
                          <th className="w-10 text-center font-mono text-[10px] bg-blue-700 text-white">STS</th>
                          <th className="w-10 text-center font-mono text-[10px] bg-blue-700 text-white">SAS</th>
                          <th className="w-12 text-center font-bold font-mono text-[10px] bg-blue-600 text-white" title="=AVERAGE">Rata S</th>
                          <th className="w-12 text-center font-bold font-mono text-[10px] bg-teal-700 text-white" title="=ROUND((RataF*50% + RataS*50%),0)">NA</th>
                          <th className="w-16 text-center font-bold bg-teal-800 text-white" title="=IF(NA>=KKTP)">Status</th>
                          <th className="min-w-[100px] text-left text-[10px] bg-teal-900 text-white">Capaian Kompetensi</th>
                        </tr>
                      </thead>
                      <tbody>
                        {effectiveStudents.slice(0, 15).map((s: StudentOverrideItem, idx: number) => (
                          <tr key={idx}>
                            <td className="text-center font-bold">{s.nomor_absen || idx + 1}</td>
                            <td className="text-center font-mono text-[10px] text-slate-500">{s.nisn || '-'}</td>
                            <td className="font-semibold text-slate-900">{s.nama_lengkap}</td>
                            <td className="text-center font-bold">{s.jenis_kelamin || 'L'}</td>
                            <td className="text-center font-mono text-slate-700">85</td>
                            <td className="text-center font-mono text-slate-700">80</td>
                            <td className="text-center font-mono text-slate-700">88</td>
                            <td className="text-center font-mono text-slate-700">82</td>
                            <td className="text-center font-mono font-bold text-blue-800 bg-blue-50">83.8</td>
                            <td className="text-center font-mono text-slate-700">80</td>
                            <td className="text-center font-mono text-slate-700">85</td>
                            <td className="text-center font-mono font-bold text-blue-800 bg-blue-50">82.5</td>
                            <td className="text-center font-mono font-extrabold text-teal-800 bg-teal-50">83</td>
                            <td className="text-center font-bold text-[10px] text-emerald-700 bg-emerald-50">TUNTAS</td>
                            <td className="text-[10px] text-slate-600">Menunjukkan penguasaan optimal</td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot>
                        <tr className="bg-slate-100 font-bold border-t border-slate-300">
                          <td colSpan={4} className="text-right pr-2 uppercase text-[10px]">Nilai Tertinggi Kelas</td>
                          <td colSpan={8} className="text-center text-[10px] text-slate-400 italic">Formula Excel Otomatis</td>
                          <td className="text-center font-mono text-teal-800">=MAX</td>
                          <td colSpan={2} className="text-[10px] text-slate-500">Capaian tertinggi rombel</td>
                        </tr>
                        <tr className="bg-slate-100 font-bold">
                          <td colSpan={4} className="text-right pr-2 uppercase text-[10px]">Nilai Terendah Kelas</td>
                          <td colSpan={8} className="text-center text-[10px] text-slate-400 italic">Formula Excel Otomatis</td>
                          <td className="text-center font-mono text-teal-800">=MIN</td>
                          <td colSpan={2} className="text-[10px] text-slate-500">Batas bawah evaluasi</td>
                        </tr>
                        <tr className="bg-slate-100 font-bold">
                          <td colSpan={4} className="text-right pr-2 uppercase text-[10px]">Rata-rata Kelas</td>
                          <td colSpan={8} className="text-center text-[10px] text-slate-400 italic">Formula Excel Otomatis</td>
                          <td className="text-center font-mono text-teal-800">=AVERAGE</td>
                          <td colSpan={2} className="text-[10px] text-slate-500">Mean nilai akhir</td>
                        </tr>
                        <tr className="bg-teal-50 font-bold border-t-2 border-teal-600 text-teal-900">
                          <td colSpan={4} className="text-right pr-2 uppercase text-[10px]">Ketuntasan Klasikal (%)</td>
                          <td colSpan={8} className="text-center text-[10px] text-teal-700 italic">Formula =COUNTIF(Status, "TUNTAS")/Total</td>
                          <td colSpan={3} className="text-center font-mono font-extrabold text-teal-900">=ROUND((COUNTIF/COUNT)*100, 1)%</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                  <p className="text-[11px] text-slate-500 italic">
                    * Dokumen unduhan (.xlsx) mencakup formula aktif live: rata-rata formatif, pembobotan sumatif (STS/SAS), Nilai Akhir (NA), status KKTP, dan statistik kelas.
                  </p>
                </div>
              )}

              {/* 3. LEMBAR PENGESAHAN RESMI */}
              {renderOfficialPengesahan()}
            </div>
            {renderPaperFooter(`Kertas ${paperSize} • Halaman 1`)}
          </div>
        )}
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
