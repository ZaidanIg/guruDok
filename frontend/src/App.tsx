import React, { useState, useEffect, useCallback } from 'react';
import {
  AuthUser,
  ChapterTopic,
  CurriculumSubject,
  CustomDocumentOverrides,
  DocumentGenerateResponse,
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
import { QuickFilterBar } from './components/sections/QuickFilterBar';
import { ServiceCatalog } from './components/sections/ServiceCatalog';
import { DocumentGenerator } from './components/sections/DocumentGenerator';
import { DocumentHistory } from './components/sections/DocumentHistory';
import { SchoolProfileModal } from './components/modals/SchoolProfileModal';
import { SuccessDownloadModal } from './components/modals/SuccessDownloadModal';
import { GoogleLoginModal } from './components/modals/GoogleLoginModal';

const STORAGE_KEY_TEACHER = 'gurudok_teacher_profile_v2';

export const App: React.FC = () => {
  // Multi-Page Navigation State: 'home' | 'katalog' | 'generator' | 'riwayat'
  const [activeSection, setActiveSection] = useState<'home' | 'katalog' | 'generator' | 'riwayat'>('home');
  const [selectedServiceId, setSelectedServiceId] = useState<ServiceId>('08_modul_ajar');

  // Katalog Filter State
  const [quickJenjang, setQuickJenjang] = useState<Jenjang | 'ALL'>('ALL');
  const [quickKelas, setQuickKelas] = useState<number | 'ALL'>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

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

  // Google Auth Gate State
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState<boolean>(false);
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

  // Load Google Auth Session & History on mount
  useEffect(() => {
    apiClient.getCurrentUser().then((user) => {
      setAuthUser(user);
      apiClient.getHistory().then(setHistory);
    });
  }, []);

  // Multi-Page Navigation Helper
  const handleNavigate = (section: 'home' | 'katalog' | 'generator' | 'riwayat') => {
    setActiveSection(section);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Select Service from Home or Katalog -> Opens dedicated Generator Page
  const handleSelectService = (serviceId: ServiceId) => {
    setSelectedServiceId(serviceId);
    setOutputFormat(serviceId === '06_promes' ? 'xlsx' : 'docx');
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

  // Handle Quick Filter Trigger on Katalog Page
  const handleQuickFilterTrigger = () => {
    if (quickJenjang !== 'ALL') {
      setJenjang(quickJenjang);
      const nextGrade =
        quickKelas !== 'ALL' ? quickKelas : GRADES_BY_JENJANG[quickJenjang][0];
      setKelas(nextGrade);
    }
    if (activeSection !== 'katalog') {
      handleNavigate('katalog');
    }
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
      const hasCustomOverrides = Object.keys(customOverrides).length > 0;
      const hasCompleteProfile = Boolean(
        teacher.nama_guru.trim() &&
          teacher.nama_sekolah.trim() &&
          teacher.kabupaten_kota.trim() &&
          teacher.nama_kepala_sekolah.trim() &&
          teacher.no_whatsapp.trim()
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
        custom_overrides: hasCustomOverrides ? customOverrides : undefined,
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
    setAuthUser(user);
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
          onOpenLoginModal={() => setIsLoginModalOpen(true)}
          onLogout={handleLogout}
        />

        {/* Multi-Page Content Router */}
        <main>
          {activeSection === 'home' && (
            <HeroSection
              onOpenCatalog={() => handleNavigate('katalog')}
              onOpenHistory={() => handleNavigate('riwayat')}
              onSelectService={handleSelectService}
            />
          )}

          {activeSection === 'katalog' && (
            <>
              <QuickFilterBar
                selectedJenjang={quickJenjang}
                selectedKelas={quickKelas}
                searchQuery={searchQuery}
                onChangeJenjang={setQuickJenjang}
                onChangeKelas={setQuickKelas}
                onChangeSearch={setSearchQuery}
                onTriggerSearch={handleQuickFilterTrigger}
              />
              <ServiceCatalog
                selectedServiceId={selectedServiceId}
                searchQuery={searchQuery}
                onSelectService={handleSelectService}
              />
            </>
          )}

          {activeSection === 'generator' && (
            <DocumentGenerator
              activeService={activeServiceObj}
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
    </div>
  );
};

export default App;
