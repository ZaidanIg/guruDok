import React, { useState, useEffect, useCallback } from 'react';
import {
  AuthUser,
  ChapterTopic,
  CurriculumSubject,
  CustomDocumentOverrides,
  DocumentGenerateResponse,
  GenerationMode,
  HistoryDocumentItem,
  Jenjang,
  OutputFormat,
  PaperSize,
  ServiceId,
  TeacherProfile,
} from './types';
import {
  CORE_SERVICES,
  DEFAULT_TEACHER_PROFILE,
  GRADES_BY_JENJANG,
  PEDAGOGICAL_MODELS,
} from './constants/services';
import { apiClient } from './services/api';
import { Navbar } from './components/layout/Navbar';
import { BottomNav } from './components/layout/BottomNav';
import { Footer } from './components/layout/Footer';
import { HeroSection } from './components/sections/HeroSection';
import { ServiceCatalog } from './components/sections/ServiceCatalog';
import { DocumentGenerator } from './components/sections/DocumentGenerator';
import { DocumentHistory } from './components/sections/DocumentHistory';
import { SchoolProfileModal } from './components/modals/SchoolProfileModal';
import { SuccessDownloadModal } from './components/modals/SuccessDownloadModal';
import { GoogleLoginModal } from './components/modals/GoogleLoginModal';
import { ClassroomManagementModal } from './components/modals/ClassroomManagementModal';
import { CacheConsentBadge } from './components/modals/CacheConsentBadge';
import { getClassrooms, getActiveClassroom, StudentItem } from './services/classroomStorage';
import {
  dismissSessionCachePrompt,
  enableAndWarmAssetCache,
  isLocalCacheAllowed,
  isSessionCachePromptDismissed,
} from './services/cacheConsent';

const STORAGE_KEY_TEACHER = 'gurudok_teacher_profile_v2';

export const App: React.FC = () => {
  // Multi-Page Navigation State: 'home' | 'katalog' | 'generator' | 'riwayat'
  const [activeSection, setActiveSection] = useState<'home' | 'katalog' | 'generator' | 'riwayat'>('home');
  const [selectedServiceId, setSelectedServiceId] = useState<ServiceId>('08_modul_ajar');

  // Generator Mode State ('template' default for curriculum, 'manual' for exams/tracking)
  const [generationMode, setGenerationMode] = useState<GenerationMode>('template');

  // Classroom Management Modal State
  const [isClassroomModalOpen, setIsClassroomModalOpen] = useState<boolean>(false);

  // Studio Generator Cascading Form State
  const [jenjang, setJenjang] = useState<Jenjang>('SMA');
  const [kelas, setKelas] = useState<number>(11);
  const [subjects, setSubjects] = useState<CurriculumSubject[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<CurriculumSubject | null>(null);
  const [semester, setSemester] = useState<number>(1);
  const [chapters, setChapters] = useState<ChapterTopic[]>([]);
  const [selectedChapter, setSelectedChapter] = useState<ChapterTopic | null>(null);
  const [modelPembelajaran, setModelPembelajaran] = useState<string>(PEDAGOGICAL_MODELS[0]);
  const [paperSize, setPaperSize] = useState<PaperSize>('F4');
  const [outputFormat, setOutputFormat] = useState<OutputFormat>('docx');
  const [includeLkpd, setIncludeLkpd] = useState<boolean>(true);
  const [includeAsesmen, setIncludeAsesmen] = useState<boolean>(true);
  const [includeRubrik, setIncludeRubrik] = useState<boolean>(true);
  const [customOverrides, setCustomOverrides] = useState<CustomDocumentOverrides>({});

  // Teacher Profile State (persisted in localStorage)
  const [teacher, setTeacher] = useState<TeacherProfile>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_TEACHER);
      if (saved) return JSON.parse(saved);
    } catch {
      // ignore storage errors
    }
    return DEFAULT_TEACHER_PROFILE;
  });

  // Modals & Generation State
  const [isProfileModalOpen, setIsProfileModalOpen] = useState<boolean>(false);
  const [isSuccessModalOpen, setIsSuccessModalOpen] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<DocumentGenerateResponse | null>(null);
  const [history, setHistory] = useState<HistoryDocumentItem[]>([]);

  // Google Auth Gate & Cache Consent State
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState<boolean>(false);
  const [isCacheBadgeVisible, setIsCacheBadgeVisible] = useState<boolean>(false);
  const [isSavingCacheConsent, setIsSavingCacheConsent] = useState<boolean>(false);
  const [pendingAction, setPendingAction] = useState<
    | { type: 'generate' }
    | { type: 'download'; fileUrl: string; filename: string }
    | null
  >(null);

  // Load Generator Subjects whenever Jenjang or Kelas changes
  const loadSubjects = useCallback(
    async (targetJenjang: Jenjang, targetKelas: number, preferredSubjectId?: string) => {
      const list = await apiClient.getSubjects(targetJenjang, targetKelas);
      const effectiveList =
        list.length > 0 ? list : await apiClient.getSubjects(targetJenjang);
      setSubjects(effectiveList);

      const targetSubj =
        (preferredSubjectId && effectiveList.find((s) => s.id === preferredSubjectId)) ||
        effectiveList.find((s) => s.id === 'SMA-K11-INF') ||
        effectiveList[0] ||
        null;

      if (targetSubj) {
        const detailed = await apiClient.getSubjectDetail(targetSubj.id);
        setSelectedSubject(detailed || targetSubj);
      } else {
        setSelectedSubject(null);
      }
    },
    []
  );

  useEffect(() => {
    loadSubjects(jenjang, kelas);
  }, [jenjang, kelas, loadSubjects]);

  // Load Chapters whenever Selected Subject or Semester changes
  useEffect(() => {
    let active = true;
    const fetchChapters = async () => {
      if (!selectedSubject) {
        setChapters([]);
        setSelectedChapter(null);
        return;
      }
      const chList = await apiClient.getChapters(selectedSubject.id, semester);
      if (!active) return;
      const effectiveChapters =
        chList.length > 0
          ? chList
          : await apiClient.getChapters(selectedSubject.id);
      setChapters(effectiveChapters);
      const firstCh = effectiveChapters[0] || null;
      setSelectedChapter(firstCh);
      setCustomOverrides({});
      if (firstCh?.model_pembelajaran_default) {
        setModelPembelajaran(firstCh.model_pembelajaran_default);
      }
    };
    fetchChapters();
    return () => {
      active = false;
    };
  }, [selectedSubject?.id, semester]);

  // Load Google Auth Session & History on mount, sync cache consent, and enforce session protection on shared file links
  useEffect(() => {
    const localAllowed = isLocalCacheAllowed();
    if (localAllowed) {
      enableAndWarmAssetCache();
    }

    apiClient.getCurrentUser().then(async (user) => {
      if (user?.cache_allowed) {
        setAuthUser(user);
        setIsCacheBadgeVisible(false);
        enableAndWarmAssetCache();
      } else if (user && localAllowed) {
        const synced = await apiClient.saveCacheConsent(true);
        setAuthUser(synced || { ...user, cache_allowed: true });
        setIsCacheBadgeVisible(false);
      } else {
        setAuthUser(user);
        if (!localAllowed && !isSessionCachePromptDismissed()) {
          setIsCacheBadgeVisible(true);
        }
      }

      apiClient.getHistory().then(setHistory);

      // Check URL query parameters for shared file download: ?download_file=... or ?download=...
      const urlParams = new URLSearchParams(window.location.search);
      const targetFile = urlParams.get('download_file') || urlParams.get('download');
      if (targetFile) {
        // Clean URL parameter from address bar
        window.history.replaceState({}, document.title, window.location.pathname);

        const fileUrl = `/api/v1/documents/${encodeURIComponent(targetFile)}/download`;
        if (user) {
          // User has active session -> initiate authenticated download
          apiClient.downloadAuthenticatedFile(fileUrl, targetFile).catch(() => {
            setErrorMsg('Gagal mengunduh berkas tautan. Berkas mungkin tidak ditemukan di server.');
          });
        } else {
          // User has NO SESSION -> BLOCK DOWNLOAD & REQUIRE GOOGLE LOGIN
          setPendingAction({ type: 'download', fileUrl, filename: targetFile });
          setIsLoginModalOpen(true);
        }
      }
    });
  }, []);

  // Multi-Page Navigation Helper
  const handleNavigate = (section: 'home' | 'katalog' | 'generator' | 'riwayat') => {
    setActiveSection(section);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Select Service from Home or Katalog -> Opens Studio Generator immediately (no blocking pop-up)
  const handleSelectService = (serviceId: ServiceId) => {
    const isCurriculum =
      serviceId === '03_cp_tp' ||
      serviceId === '04_atp' ||
      serviceId === '05_prota' ||
      serviceId === '06_promes' ||
      serviceId === '07_kktp' ||
      serviceId === '08_modul_ajar' ||
      serviceId === '09_lkpd';
    const nextMode: GenerationMode = !isCurriculum
      ? 'manual'
      : activeSection === 'generator'
      ? generationMode
      : 'template';
    applyServiceSelection(serviceId, nextMode);
  };

  const applyServiceSelection = (serviceId: ServiceId, mode: GenerationMode) => {
    setSelectedServiceId(serviceId);
    setGenerationMode(mode);
    const targetService = CORE_SERVICES.find((s) => s.id === serviceId);
    const allowed = (targetService?.formats || ['DOCX', 'PDF']).map((f) => f.toLowerCase() as OutputFormat);
    setOutputFormat((prev) => {
      if (serviceId === '06_promes' || serviceId === '13_presensi' || serviceId === '15_daftar_nilai') {
        return 'xlsx';
      }
      if (allowed.includes(prev)) return prev;
      return allowed[0] || 'docx';
    });
    setErrorMsg(null);
    handleNavigate('generator');
  };

  // Handle Jenjang Change in Generator
  const handleGeneratorJenjangChange = (nextJenjang: Jenjang) => {
    setJenjang(nextJenjang);
    const defaultGrade = GRADES_BY_JENJANG[nextJenjang][0];
    setKelas(defaultGrade);
  };

  // Handle Subject Change in Generator
  const handleGeneratorSubjectChange = async (subjectId: string) => {
    const found = subjects.find((s) => s.id === subjectId) || null;
    if (found) {
      const detailed = await apiClient.getSubjectDetail(found.id);
      setSelectedSubject(detailed || found);
      setCustomOverrides({});
    }
  };

  // Handle Chapter Change in Generator
  const handleGeneratorChapterChange = (chapterId: string) => {
    const found = chapters.find((c) => c.id === chapterId) || null;
    setSelectedChapter(found);
    setCustomOverrides({});
  };

  // Handle Chapter Created in Generator
  const handleChapterCreated = async (newChapter: ChapterTopic) => {
    if (!selectedSubject) return;
    const updatedSubj = await apiClient.getSubjectDetail(selectedSubject.id);
    if (updatedSubj) {
      setSelectedSubject(updatedSubj);
    }
    const chList = await apiClient.getChapters(selectedSubject.id, semester);
    setChapters(chList);
    setSelectedChapter(newChapter);
    setCustomOverrides({});
  };

  // Save Teacher Profile (Disimpan di browser saja, bersifat opsional)
  const handleSaveTeacherProfile = async (updated: TeacherProfile) => {
    setTeacher(updated);
    setPaperSize(updated.ukuran_kertas_default);
    try {
      localStorage.setItem(STORAGE_KEY_TEACHER, JSON.stringify(updated));
    } catch {
      // ignore storage errors
    }
  };

  const executeGenerateDocument = async () => {
    if (!selectedSubject) {
      setErrorMsg('Silakan pilih Mata Pelajaran terlebih dahulu.');
      return;
    }

    setIsGenerating(true);
    setErrorMsg(null);

    try {
      let finalOverrides: CustomDocumentOverrides = { ...customOverrides };

      // Automatic Student and Rombel injection for Classroom & Jurnal Services
      if (selectedServiceId === '13_presensi' || selectedServiceId === '14_jurnal_mengajar' || selectedServiceId === '15_daftar_nilai') {
        const activeRombel = getActiveClassroom() || getClassrooms()[0];
        if (activeRombel) {
          if (!finalOverrides.students || finalOverrides.students.length === 0) {
            finalOverrides.students = (activeRombel.students || []).map((s: StudentItem) => ({
              nomor_absen: s.nomor_absen,
              nisn: s.nisn,
              nama_lengkap: s.nama_lengkap,
              jenis_kelamin: s.jenis_kelamin,
            }));
          }
          if (!finalOverrides.nama_rombel) {
            finalOverrides.nama_rombel = activeRombel.nama_rombel;
          }
          if (!finalOverrides.wali_kelas) {
            finalOverrides.wali_kelas = activeRombel.wali_kelas;
          }
        }
        if (selectedServiceId === '13_presensi' && !finalOverrides.bulan_presensi) {
          finalOverrides.bulan_presensi = 'Agustus';
        }
        if (selectedServiceId === '15_daftar_nilai' && !finalOverrides.kktp_nilai) {
          finalOverrides.kktp_nilai = 75;
        }
      }

      if (finalOverrides.butir_soal_kustom && finalOverrides.butir_soal_kustom.length > 0) {
        finalOverrides.butir_soal_kustom = finalOverrides.butir_soal_kustom.map((q) => ({
          ...q,
          pertanyaan:
            q.pertanyaan && q.pertanyaan.trim().length >= 2
              ? q.pertanyaan
              : '(Belum ada teks pertanyaan)',
        }));
      }

      if (finalOverrides.custom_jurnal_rows && finalOverrides.custom_jurnal_rows.length > 0) {
        finalOverrides.custom_jurnal_rows = finalOverrides.custom_jurnal_rows.map((row, idx) => ({
          ...row,
          no: idx + 1,
          hari_tanggal: row.hari_tanggal?.trim() || `Pertemuan Ke-${idx + 1}`,
        }));
      }

      const hasCustomOverrides = Object.keys(finalOverrides).length > 0;
      const hasCompleteProfile = Boolean(
        teacher.nama_guru.trim().length >= 2 &&
          teacher.nama_sekolah.trim().length >= 3 &&
          teacher.kabupaten_kota.trim().length >= 3 &&
          teacher.provinsi.trim().length >= 3 &&
          teacher.nama_kepala_sekolah.trim().length >= 2 &&
          teacher.no_whatsapp.replace(/\D/g, '').length >= 9
      );

      const response = await apiClient.generateDocument({
        service_id: selectedServiceId,
        jenjang,
        kelas: selectedSubject.kelas,
        subject_id: selectedSubject.id,
        semester,
        chapter_id: selectedChapter?.id,
        model_pembelajaran: modelPembelajaran,
        paper_size: paperSize,
        output_format: outputFormat,
        teacher_profile: hasCompleteProfile ? teacher : undefined,
        include_lkpd: includeLkpd,
        include_asesmen: includeAsesmen,
        include_rubrik: includeRubrik,
        custom_overrides: hasCustomOverrides ? finalOverrides : undefined,
      });

      setLastResult(response);
      setIsSuccessModalOpen(true);

      const updatedHistory = await apiClient.getHistory();
      setHistory(updatedHistory);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Gagal terhubung ke server generator. Pastikan backend FastAPI berjalan di port 8000.';
      setErrorMsg(msg);
    } finally {
      setIsGenerating(false);
    }
  };

  // Trigger Document Generation (Wajib Google Login sebelum generate/download)
  const handleGenerateDocument = async () => {
    if (!selectedSubject) {
      setErrorMsg('Silakan pilih Mata Pelajaran terlebih dahulu.');
      return;
    }
    if (!authUser) {
      setPendingAction({ type: 'generate' });
      setIsLoginModalOpen(true);
      return;
    }
    await executeGenerateDocument();
  };

  // Trigger File Download (Wajib Google Login)
  const handleDownloadFile = async (url: string, filename: string) => {
    if (!url || url === '#') {
      handleNavigate('generator');
      return;
    }
    if (!authUser) {
      setPendingAction({ type: 'download', fileUrl: url, filename });
      setIsLoginModalOpen(true);
      return;
    }
    try {
      await apiClient.downloadAuthenticatedFile(url, filename);
    } catch (err: unknown) {
      if (err instanceof Error && err.message === 'UNAUTHORIZED') {
        apiClient.clearAuthToken();
        setAuthUser(null);
        setPendingAction({ type: 'download', fileUrl: url, filename });
        setIsLoginModalOpen(true);
      } else {
        setErrorMsg('Gagal mengunduh berkas dari server.');
      }
    }
  };

  const handleGoogleLoginSuccess = async (user: AuthUser) => {
    let resolvedUser = user;
    if (user.cache_allowed) {
      setIsCacheBadgeVisible(false);
      enableAndWarmAssetCache();
    } else if (isLocalCacheAllowed()) {
      const synced = await apiClient.saveCacheConsent(true);
      if (synced) resolvedUser = synced;
      setIsCacheBadgeVisible(false);
    }

    setAuthUser(resolvedUser);
    setIsLoginModalOpen(false);
    const updatedHistory = await apiClient.getHistory();
    setHistory(updatedHistory);

    const action = pendingAction;
    setPendingAction(null);
    if (action?.type === 'generate') {
      await executeGenerateDocument();
    } else if (action?.type === 'download') {
      try {
        await apiClient.downloadAuthenticatedFile(action.fileUrl, action.filename);
      } catch {
        setErrorMsg('Gagal mengunduh berkas setelah login.');
      }
    }
  };

  const handleAllowCacheConsent = async () => {
    setIsSavingCacheConsent(true);
    try {
      await enableAndWarmAssetCache();
      if (authUser) {
        const updatedUser = await apiClient.saveCacheConsent(true);
        if (updatedUser) {
          setAuthUser(updatedUser);
        } else {
          setAuthUser((prev) => (prev ? { ...prev, cache_allowed: true } : prev));
        }
      }
      setIsCacheBadgeVisible(false);
    } finally {
      setIsSavingCacheConsent(false);
    }
  };

  const handleDismissCacheConsent = () => {
    dismissSessionCachePrompt();
    setIsCacheBadgeVisible(false);
  };

  const handleLogout = () => {
    apiClient.clearAuthToken();
    setAuthUser(null);
    setHistory([]);
  };

  const activeServiceObj =
    CORE_SERVICES.find((s) => s.id === selectedServiceId) || CORE_SERVICES[2];

  return (
    <div className="flex min-h-screen flex-col justify-between">
      <div>
        {/* Top Clean Navbar (3 Pages: Home, Katalog Layanan, Riwayat Dokumen) */}
        <Navbar
          teacher={teacher}
          authUser={authUser}
          activeSection={activeSection}
          onNavigate={handleNavigate}
          onOpenProfileModal={() => setIsProfileModalOpen(true)}
          onOpenClassroomModal={() => setIsClassroomModalOpen(true)}
          onOpenLoginModal={() => setIsLoginModalOpen(true)}
          onLogout={handleLogout}
        />

        {/* Multi-Page Content Router (Keep-Alive on Home & Catalog to prevent icon re-requests) */}
        <main>
          <div className={activeSection === 'home' ? 'block' : 'hidden'}>
            <HeroSection
              onOpenCatalog={() => handleNavigate('katalog')}
              onOpenHistory={() => handleNavigate('riwayat')}
              onSelectService={handleSelectService}
            />
          </div>

          <div className={activeSection === 'katalog' ? 'block' : 'hidden'}>
            <ServiceCatalog
              selectedServiceId={selectedServiceId}
              onSelectService={handleSelectService}
              onOpenClassroomModal={() => setIsClassroomModalOpen(true)}
            />
          </div>

          {activeSection === 'generator' && (
            <DocumentGenerator
              activeService={activeServiceObj}
              generationMode={generationMode}
              onChangeGenerationMode={setGenerationMode}
              jenjang={jenjang}
              kelas={kelas}
              subjects={subjects}
              selectedSubject={selectedSubject}
              semester={semester}
              chapters={chapters}
              selectedChapter={selectedChapter}
              modelPembelajaran={modelPembelajaran}
              paperSize={paperSize}
              outputFormat={outputFormat}
              includeLkpd={includeLkpd}
              includeAsesmen={includeAsesmen}
              includeRubrik={includeRubrik}
              teacher={teacher}
              customOverrides={customOverrides}
              isGenerating={isGenerating}
              errorMsg={errorMsg}
              onSelectService={handleSelectService}
              onChangeJenjang={handleGeneratorJenjangChange}
              onChangeKelas={setKelas}
              onChangeSubject={handleGeneratorSubjectChange}
              onChangeSemester={setSemester}
              onChangeChapter={handleGeneratorChapterChange}
              onChangeModelPembelajaran={setModelPembelajaran}
              onChangePaperSize={setPaperSize}
              onChangeOutputFormat={setOutputFormat}
              onToggleLkpd={() => setIncludeLkpd((v) => !v)}
              onToggleAsesmen={() => setIncludeAsesmen((v) => !v)}
              onToggleRubrik={() => setIncludeRubrik((v) => !v)}
              onChangeCustomOverrides={setCustomOverrides}
              onResetCustomOverrides={() => setCustomOverrides({})}
              onOpenProfileModal={() => setIsProfileModalOpen(true)}
              onOpenClassroomModal={() => setIsClassroomModalOpen(true)}
              onBackToCatalog={() => handleNavigate('katalog')}
              onGenerate={handleGenerateDocument}
              onChapterCreated={handleChapterCreated}
            />
          )}

          {activeSection === 'riwayat' && (
            <DocumentHistory
              history={history}
              onRedownload={(item) => handleDownloadFile(item.file_url, item.filename)}
              onOpenCatalog={() => handleNavigate('katalog')}
            />
          )}
        </main>
      </div>

      {/* Clean Footer */}
      <Footer />

      {/* Mobile Fixed Bottom Navigation */}
      <BottomNav activeSection={activeSection} onNavigate={handleNavigate} />

      {/* First-Visit Cache Allow Consent Badge (Synced with User Account) */}
      <CacheConsentBadge
        isVisible={isCacheBadgeVisible}
        isSaving={isSavingCacheConsent}
        onAllow={handleAllowCacheConsent}
        onDismiss={handleDismissCacheConsent}
      />

      {/* Modal 1: Lengkapi Profil Sekolah Anda */}
      <SchoolProfileModal
        isOpen={isProfileModalOpen}
        initialProfile={teacher}
        onClose={() => setIsProfileModalOpen(false)}
        onSave={handleSaveTeacherProfile}
      />

      {/* Modal 2: Dokumen Berhasil Dibuat & Download */}
      <SuccessDownloadModal
        isOpen={isSuccessModalOpen}
        result={lastResult}
        teacher={teacher}
        onClose={() => setIsSuccessModalOpen(false)}
        onDownload={handleDownloadFile}
      />

      {/* Modal 3: Google Sign-In Gate (Wajib saat Download) */}
      <GoogleLoginModal
        isOpen={isLoginModalOpen}
        onClose={() => {
          setIsLoginModalOpen(false);
          setPendingAction(null);
        }}
        onSuccess={handleGoogleLoginSuccess}
      />

      {/* Modal 4: Kelola Data Kelas & Rombel Siswa (Client-Side Storage) */}
      <ClassroomManagementModal
        isOpen={isClassroomModalOpen}
        onClose={() => setIsClassroomModalOpen(false)}
      />
    </div>
  );
};

export default App;
