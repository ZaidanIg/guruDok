import {
  ApiEnvelope,
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

  /**
   * Requests deterministic Word (.docx), Excel (.xlsx), or PDF (.pdf) document generation.
   */
  async generateDocument(payload: DocumentGenerateRequest): Promise<DocumentGenerateResponse> {
    const res = await fetch(`${this.baseUrl}/documents/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const json = await res.json();
    if (!res.ok) {
      throw new Error(json.message || 'Gagal membuat dokumen. Pastikan server backend berjalan.');
    }
    return json.data;
  }

  /**
   * Fetches generated document history.
   */
  async getHistory(): Promise<HistoryDocumentItem[]> {
    try {
      const res = await fetch(`${this.baseUrl}/documents/history?limit=100`);
      if (!res.ok) throw new Error('Failed to fetch history');
      const json: ApiEnvelope<HistoryDocumentItem[]> = await res.json();
      if (json.data && json.data.length > 0) {
        return json.data;
      }
    } catch {
      // Return initial fallback history when offline or empty
    }
    return INITIAL_HISTORY_ITEMS;
  }
}

export const apiClient = new GuruDokApiClient();
