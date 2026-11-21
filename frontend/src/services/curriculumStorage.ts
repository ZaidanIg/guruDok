import { ChapterTopic, CustomChapterItem, CustomCpElementItem, CustomDocumentOverrides, CustomTpItem, GenerationMode } from '../types';

const STORAGE_PREFIX = 'gurudok_curriculum';
const CP_PREFIX = 'gurudok_cp';
const DRAFT_PREFIX = 'gurudok_draft';
const SESSION_KEY = 'gurudok_last_session';

/**
 * Converts domain ChapterTopic array (from backend API) into CustomChapterItem array.
 */
export function convertChapterTopicsToCustom(chapters: ChapterTopic[]): CustomChapterItem[] {
  return chapters.map((ch) => ({
    id_bab: ch.id,
    nomor_bab: ch.nomor_bab,
    semester: ch.semester,
    judul_bab: ch.judul_bab,
    elemen_cp: ch.elemen_cp || 'Pemahaman Konsep & Keterampilan Proses',
    alokasi_jp_bab: ch.alokasi_jp,
    estimasi_jumlah_pertemuan: ch.estimasi_pertemuan,
    rentang_minggu_promes: ch.rentang_minggu_promes,
    tujuan_pembelajaran: (ch.tujuan_pembelajaran || []).map((tp) => ({
      code: tp.code,
      deskripsi: tp.deskripsi,
      alokasi_jp: tp.alokasi_jp,
    })),
  }));
}

/**
 * Gets cached custom curriculum chapters for a given subject and mode.
 */
export function getCustomCurriculum(mode: GenerationMode, subjectId: string): CustomChapterItem[] | null {
  if (!subjectId) return null;
  try {
    const raw = localStorage.getItem(`${STORAGE_PREFIX}_${mode}_${subjectId}`);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : null;
  } catch (err) {
    console.warn('[CurriculumStorage] Failed to read curriculum cache:', err);
    return null;
  }
}

/**
 * Saves custom curriculum chapters for a given subject and mode.
 */
export function saveCustomCurriculum(
  mode: GenerationMode,
  subjectId: string,
  chapters: CustomChapterItem[]
): void {
  if (!subjectId) return;
  try {
    localStorage.setItem(`${STORAGE_PREFIX}_${mode}_${subjectId}`, JSON.stringify(chapters));
  } catch (err) {
    console.warn('[CurriculumStorage] Failed to save curriculum cache:', err);
  }
}

/**
 * Checks if custom curriculum cache exists for a given subject and mode.
 */
export function hasCustomCurriculum(mode: GenerationMode, subjectId: string): boolean {
  if (!subjectId) return false;
  try {
    return Boolean(localStorage.getItem(`${STORAGE_PREFIX}_${mode}_${subjectId}`));
  } catch {
    return false;
  }
}

/**
 * Resets / deletes custom curriculum cache for a given subject and mode.
 */
export function resetCustomCurriculum(mode: GenerationMode, subjectId: string): void {
  if (!subjectId) return;
  try {
    localStorage.removeItem(`${STORAGE_PREFIX}_${mode}_${subjectId}`);
  } catch (err) {
    console.warn('[CurriculumStorage] Failed to reset curriculum cache:', err);
  }
}

/**
 * Gets draft overrides for a specific service and subject.
 */
export function getManualDraft(
  mode: GenerationMode,
  serviceId: string,
  subjectId: string
): Partial<CustomDocumentOverrides> | null {
  if (!serviceId || !subjectId) return null;
  try {
    const raw = localStorage.getItem(`${DRAFT_PREFIX}_${mode}_${serviceId}_${subjectId}`);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (err) {
    console.warn('[CurriculumStorage] Failed to read manual draft:', err);
    return null;
  }
}

/**
 * Saves draft overrides real-time to localStorage cache.
 */
export function saveManualDraft(
  mode: GenerationMode,
  serviceId: string,
  subjectId: string,
  data: Partial<CustomDocumentOverrides>
): void {
  if (!serviceId || !subjectId) return;
  try {
    localStorage.setItem(
      `${DRAFT_PREFIX}_${mode}_${serviceId}_${subjectId}`,
      JSON.stringify(data)
    );
  } catch (err) {
    console.warn('[CurriculumStorage] Failed to save manual draft:', err);
  }
}

/**
 * Clears draft overrides for a specific service and subject.
 */
export function clearManualDraft(
  mode: GenerationMode,
  serviceId: string,
  subjectId: string
): void {
  if (!serviceId || !subjectId) return;
  try {
    localStorage.removeItem(`${DRAFT_PREFIX}_${mode}_${serviceId}_${subjectId}`);
  } catch (err) {
    console.warn('[CurriculumStorage] Failed to clear manual draft:', err);
  }
}

/**
 * Checks whether any draft exists for a service and subject (used by the selection modal badge).
 */
export function checkDraftAvailability(
  serviceId: string,
  subjectId: string
): { hasTemplateDraft: boolean; hasManualDraft: boolean } {
  if (!serviceId || !subjectId) {
    return { hasTemplateDraft: false, hasManualDraft: false };
  }
  const hasTemplateDraft = Boolean(
    localStorage.getItem(`${STORAGE_PREFIX}_template_${subjectId}`) ||
    localStorage.getItem(`${DRAFT_PREFIX}_template_${serviceId}_${subjectId}`)
  );
  const hasManualDraft = Boolean(
    localStorage.getItem(`${STORAGE_PREFIX}_manual_${subjectId}`) ||
    localStorage.getItem(`${DRAFT_PREFIX}_manual_${serviceId}_${subjectId}`)
  );
  return { hasTemplateDraft, hasManualDraft };
}

/**
 * Checks whether any manual draft exists across all subjects for a given service.
 */
export function checkAnyDraftForService(serviceId: string): boolean {
  if (!serviceId) return false;
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && (key.startsWith(`${STORAGE_PREFIX}_manual_`) || key.includes(`_${serviceId}_`))) {
        return true;
      }
    }
  } catch {
    return false;
  }
  return false;
}

/**
 * Saves the last active session to allow crash recovery on browser reload.
 */
export function saveLastSession(session: {
  mode: GenerationMode;
  serviceId: string;
  subjectId?: string;
}): void {
  try {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  } catch (err) {
    console.warn('[CurriculumStorage] Failed to save last session:', err);
  }
}

/**
 * Retrieves the last active session.
 */
export function getLastSession(): {
  mode?: GenerationMode;
  serviceId?: string;
  subjectId?: string;
} | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

/**
 * Gets cached custom CP elements for a given subject and mode.
 */
export function getCustomCpElements(mode: GenerationMode, subjectId: string): CustomCpElementItem[] | null {
  if (!subjectId) return null;
  try {
    const raw = localStorage.getItem(`${CP_PREFIX}_${mode}_${subjectId}`);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : null;
  } catch (err) {
    console.warn('[CurriculumStorage] Failed to read CP cache:', err);
    return null;
  }
}

/**
 * Saves custom CP elements for a given subject and mode.
 */
export function saveCustomCpElements(
  mode: GenerationMode,
  subjectId: string,
  elements: CustomCpElementItem[]
): void {
  if (!subjectId) return;
  try {
    localStorage.setItem(`${CP_PREFIX}_${mode}_${subjectId}`, JSON.stringify(elements));
  } catch (err) {
    console.warn('[CurriculumStorage] Failed to save CP cache:', err);
  }
}

/**
 * Resets / deletes custom CP elements cache for a given subject and mode.
 */
export function resetCustomCpElements(mode: GenerationMode, subjectId: string): void {
  if (!subjectId) return;
  try {
    localStorage.removeItem(`${CP_PREFIX}_${mode}_${subjectId}`);
  } catch (err) {
    console.warn('[CurriculumStorage] Failed to reset CP cache:', err);
  }
}

/**
 * Checks if custom CP elements cache exists for a given subject and mode.
 */
export function hasCustomCpElements(mode: GenerationMode, subjectId: string): boolean {
  if (!subjectId) return false;
  try {
    return Boolean(localStorage.getItem(`${CP_PREFIX}_${mode}_${subjectId}`));
  } catch {
    return false;
  }
}
