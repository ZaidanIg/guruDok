import {
  ApiEnvelope,
  AuthLoginResponse,
  AuthUser,
  ChapterCreateRequest,
  ChapterTopic,
  CurriculumSubject,
  DocumentGenerateRequest,
  DocumentGenerateResponse,
  HistoryDocumentItem,
  Jenjang,
  TeacherProfile,
} from '../types';
import { FALLBACK_SUBJECTS, INITIAL_HISTORY_ITEMS } from './fallbackData';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const AUTH_TOKEN_KEY = 'gurudok_auth_token_v1';

export class GuruDokApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  /**
   * Checks if the FastAPI backend is reachable.
   */
  async checkHealth(): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/health`);
      return res.ok;
    } catch {
      return false;
    }
  }

  /**
   * Fetches curriculum subjects filtered by Jenjang and Grade.
   */
  async getSubjects(jenjang?: Jenjang, kelas?: number): Promise<CurriculumSubject[]> {
    try {
      const params = new URLSearchParams();
      if (jenjang) params.set('jenjang', jenjang);
      if (kelas) params.set('kelas', String(kelas));

      const res = await fetch(`${this.baseUrl}/curriculum/subjects?${params.toString()}`);
      if (!res.ok) throw new Error('Failed to fetch subjects');
      const json: ApiEnvelope<CurriculumSubject[]> = await res.json();
      if (json.data && json.data.length > 0) {
        return json.data;
      }
    } catch {
      // Fallback to local indexed dataset if backend is offline
    }

    return FALLBACK_SUBJECTS.filter((s) => {
      if (jenjang && s.jenjang !== jenjang) return false;
      if (kelas && s.kelas !== kelas) return false;
      return true;
    });
  }

  /**
   * Fetches full detail for a specific subject ID (including rasional, tujuan, karakteristik, elemen_cp, and bab_list).
   */
  async getSubjectDetail(subjectId: string): Promise<CurriculumSubject | null> {
    try {
      const res = await fetch(`${this.baseUrl}/curriculum/subjects/${encodeURIComponent(subjectId)}`);
      if (!res.ok) throw new Error('Failed to fetch subject detail');
      const json: ApiEnvelope<CurriculumSubject> = await res.json();
      if (json.data) {
        return json.data;
      }
    } catch {
      // Fallback
    }
    return FALLBACK_SUBJECTS.find((s) => s.id === subjectId) || null;
  }

  /**
   * Fetches chapters for a given subject ID and optional semester.
   */
  async getChapters(subjectId: string, semester?: number): Promise<ChapterTopic[]> {
    try {
      const params = new URLSearchParams();
      if (semester) params.set('semester', String(semester));
      const res = await fetch(
        `${this.baseUrl}/curriculum/subjects/${encodeURIComponent(subjectId)}/chapters?${params.toString()}`
      );
      if (!res.ok) throw new Error('Failed to fetch chapters');
      const json: ApiEnvelope<ChapterTopic[]> = await res.json();
      if (json.data && json.data.length > 0) {
        return json.data;
      }
    } catch {
      // Fallback to local chapter list
    }

    const found = FALLBACK_SUBJECTS.find((s) => s.id === subjectId);
    if (!found || !found.bab_list) return [];
    const filtered = semester
      ? found.bab_list.filter((b) => b.semester === semester)
      : found.bab_list;
    return filtered.length > 0 ? filtered : found.bab_list;
  }

  /**
   * Adds a user-defined custom chapter to a subject.
   */
  async createChapter(subjectId: string, payload: ChapterCreateRequest): Promise<ChapterTopic> {
    const res = await fetch(`${this.baseUrl}/curriculum/subjects/${encodeURIComponent(subjectId)}/chapters`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const json: ApiEnvelope<ChapterTopic> = await res.json();
    if (!res.ok) {
      throw new Error(json.message || 'Gagal menambahkan bab baru.');
    }
    return json.data;
  }

  /**
   * Saves teacher and school profile (Lead Capture).
   */
  async saveTeacherProfile(profile: TeacherProfile): Promise<TeacherProfile> {
    const res = await fetch(`${this.baseUrl}/teachers/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    });

    const json = await res.json();
    if (!res.ok) {
      throw new Error(json.message || 'Gagal menyimpan profil sekolah. Periksa kembali format isian.');
    }
    return json.data;
  }

  getAuthToken(): string | null {
    try {
      return localStorage.getItem(AUTH_TOKEN_KEY);
    } catch {
      return null;
    }
  }

  setAuthToken(token: string): void {
    try {
      localStorage.setItem(AUTH_TOKEN_KEY, token);
    } catch {
      // ignore storage errors
    }
  }

  clearAuthToken(): void {
    try {
      localStorage.removeItem(AUTH_TOKEN_KEY);
    } catch {
      // ignore storage errors
    }
  }

  private getAuthHeaders(): Record<string, string> {
    const token = this.getAuthToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  async loginWithGoogle(credential: string): Promise<AuthLoginResponse> {
    const res = await fetch(`${this.baseUrl}/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential }),
    });
    const json = await res.json();
    if (!res.ok) {
      throw new Error(json.detail || json.message || 'Gagal login dengan Google.');
    }
    this.setAuthToken(json.data.access_token);
    return json.data;
  }

  async getCurrentUser(): Promise<AuthUser | null> {
    const token = this.getAuthToken();
    if (!token) return null;
    try {
      const res = await fetch(`${this.baseUrl}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        this.clearAuthToken();
        return null;
      }
      const json: ApiEnvelope<AuthUser> = await res.json();
      return json.data;
    } catch {
      return null;
    }
  }

  /**
   * Requests deterministic Word (.docx), Excel (.xlsx), or PDF (.pdf) document generation.
   */
  async generateDocument(payload: DocumentGenerateRequest): Promise<DocumentGenerateResponse> {
    const res = await fetch(`${this.baseUrl}/documents/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
      },
      body: JSON.stringify(payload),
    });

    const json = await res.json();
    if (!res.ok) {
      throw new Error(json.message || 'Gagal membuat dokumen. Pastikan server backend berjalan.');
    }
    return json.data;
  }

  /**
   * Downloads generated document with Bearer JWT authentication.
   * Supports direct authenticated URL (?token=...) navigation for iOS Safari and mobile devices,
   * with safe delayed blob URL revocation for desktop browsers.
   */
  async downloadAuthenticatedFile(fileUrl: string, filename: string): Promise<void> {
    const token = this.getAuthToken();
    let targetUrl = fileUrl;
    if (token) {
      const sep = targetUrl.includes('?') ? '&' : '?';
      targetUrl = `${targetUrl}${sep}token=${encodeURIComponent(token)}`;
    }

    const isMobileOrSafari =
      typeof navigator !== 'undefined' &&
      (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent) ||
        (navigator.userAgent.includes('Safari') && !navigator.userAgent.includes('Chrome')));

    // On iOS Safari and mobile devices, trigger direct link navigation so native download manager handles attachment
    if (isMobileOrSafari && (targetUrl.startsWith('/api') || targetUrl.startsWith('http'))) {
      const link = document.createElement('a');
      link.href = targetUrl;
      link.setAttribute('download', filename);
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      link.remove();
      return;
    }

    // For desktop browsers, fetch with headers and safely delay blob revocation
    const res = await fetch(targetUrl, {
      headers: {
        ...this.getAuthHeaders(),
      },
    });
    if (res.status === 401) {
      throw new Error('UNAUTHORIZED');
    }
    if (!res.ok) {
      throw new Error('Gagal mengunduh dokumen dari server.');
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    // Delay revocation by 30 seconds to prevent WebKit / async abort
    setTimeout(() => {
      try {
        window.URL.revokeObjectURL(url);
      } catch {
        // ignore
      }
    }, 30000);
  }

  /**
   * Fetches generated document history.
   */
  async getHistory(): Promise<HistoryDocumentItem[]> {
    try {
      const res = await fetch(`${this.baseUrl}/documents/history?limit=100`, {
        headers: {
          ...this.getAuthHeaders(),
        },
      });
      if (!res.ok) throw new Error('Failed to fetch history');
      const json: ApiEnvelope<HistoryDocumentItem[]> = await res.json();
      return Array.isArray(json.data) ? json.data : [];
    } catch {
      // Return initial fallback history only when backend is offline/unreachable
      return INITIAL_HISTORY_ITEMS;
    }
  }

  /**
   * Uploads and parses teacher student roster Excel file statelessly.
   */
  async parseClassroomExcel(file: File): Promise<{
    detected_header_row: number;
    column_mappings: Record<string, number | null>;
    total_rows: number;
    students: Array<{
      nomor_absen: number;
      nisn: string;
      nama_lengkap: string;
      jenis_kelamin: 'L' | 'P';
    }>;
    warnings: string[];
  }> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${this.baseUrl}/classrooms/parse-excel`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      let errorMsg = 'Gagal memproses file Excel.';
      try {
        const errorJson = await res.json();
        if (errorJson.detail) errorMsg = errorJson.detail;
      } catch {
        // ignore
      }
      throw new Error(errorMsg);
    }

    const json = await res.json();
    return json.data;
  }

  /**
   * Downloads the official GuruDok student template .xlsx file.
   */
  async downloadStudentTemplate(): Promise<void> {
    const res = await fetch(`${this.baseUrl}/classrooms/template-excel`);
    if (!res.ok) {
      throw new Error('Gagal mengunduh format template Excel.');
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'Format_Data_Siswa_GuruDok.xlsx');
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => {
      try {
        window.URL.revokeObjectURL(url);
      } catch {
        // ignore
      }
    }, 30000);
  }
}

export const apiClient = new GuruDokApiClient();
