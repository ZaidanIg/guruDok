/**
 * Classroom and Student Data Service (Browser localStorage only)
 * Follows UU PDP No. 27/2022 - Student data is strictly stored on the client side.
 */

export interface StudentItem {
  id: string;
  nomor_absen: number;
  nisn: string;
  nama_lengkap: string;
  jenis_kelamin: 'L' | 'P';
}

export interface ClassroomRombel {
  id: string;
  jenjang: 'SD' | 'SMP' | 'SMA';
  tingkat_kelas: number;
  nama_rombel: string; // misal "Kelas 4-A"
  tahun_ajaran: string; // misal "2026/2027"
  wali_kelas: string;
  students: StudentItem[];
  created_at: string;
  updated_at: string;
}

const STORAGE_KEY = 'gurudok_classrooms_v1';
const ACTIVE_CLASSROOM_KEY = 'gurudok_active_classroom_id_v1';

const DEFAULT_SAMPLE_CLASSROOMS: ClassroomRombel[] = [
  {
    id: 'sample-rombel-4a',
    jenjang: 'SD',
    tingkat_kelas: 4,
    nama_rombel: 'Kelas 4-A',
    tahun_ajaran: '2026/2027',
    wali_kelas: 'Budi Santoso, S.Pd.',
    students: [
      { id: 'std-1', nomor_absen: 1, nisn: '0081234561', nama_lengkap: 'Ahmad Fauzi', jenis_kelamin: 'L' },
      { id: 'std-2', nomor_absen: 2, nisn: '0081234562', nama_lengkap: 'Budi Santoso', jenis_kelamin: 'L' },
      { id: 'std-3', nomor_absen: 3, nisn: '0081234563', nama_lengkap: 'Citra Dewi Lestari', jenis_kelamin: 'P' },
      { id: 'std-4', nomor_absen: 4, nisn: '0081234564', nama_lengkap: 'Dewi Sartika', jenis_kelamin: 'P' },
      { id: 'std-5', nomor_absen: 5, nisn: '0081234565', nama_lengkap: 'Eko Prasetyo', jenis_kelamin: 'L' },
    ],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const getClassrooms = (): ClassroomRombel[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      // Seed initial sample classroom
      localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_SAMPLE_CLASSROOMS));
      localStorage.setItem(ACTIVE_CLASSROOM_KEY, DEFAULT_SAMPLE_CLASSROOMS[0].id);
      return DEFAULT_SAMPLE_CLASSROOMS;
    }
    return JSON.parse(raw);
  } catch (err) {
    console.error('Failed to read classrooms from localStorage:', err);
    return [];
  }
};

export const saveClassroom = (classroom: ClassroomRombel): void => {
  try {
    const current = getClassrooms();
    const idx = current.findIndex((c) => c.id === classroom.id);
    const updated = {
      ...classroom,
      updated_at: new Date().toISOString(),
    };

    let nextList: ClassroomRombel[];
    if (idx >= 0) {
      nextList = [...current];
      nextList[idx] = updated;
    } else {
      nextList = [...current, updated];
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(nextList));
  } catch (err) {
    console.error('Failed to save classroom to localStorage:', err);
  }
};

export const deleteClassroom = (id: string): void => {
  try {
    const current = getClassrooms();
    const filtered = current.filter((c) => c.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));

    if (getActiveClassroomId() === id) {
      const nextActive = filtered.length > 0 ? filtered[0].id : '';
      localStorage.setItem(ACTIVE_CLASSROOM_KEY, nextActive);
    }
  } catch (err) {
    console.error('Failed to delete classroom from localStorage:', err);
  }
};

export const clearAllClassrooms = (): void => {
  try {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(ACTIVE_CLASSROOM_KEY);
  } catch (err) {
    console.error('Failed to clear classrooms from localStorage:', err);
  }
};

export const getActiveClassroomId = (): string => {
  try {
    const active = localStorage.getItem(ACTIVE_CLASSROOM_KEY);
    if (active) return active;
    const list = getClassrooms();
    return list.length > 0 ? list[0].id : '';
  } catch {
    return '';
  }
};

export const getActiveClassroom = (): ClassroomRombel | null => {
  try {
    const current = getClassrooms();
    const activeId = getActiveClassroomId();
    return current.find((c) => c.id === activeId) || current[0] || null;
  } catch {
    return null;
  }
};

export const setActiveClassroomId = (id: string): void => {
  try {
    localStorage.setItem(ACTIVE_CLASSROOM_KEY, id);
  } catch (err) {
    console.error('Failed to set active classroom ID:', err);
  }
};

export const addStudentsToClassroom = (
  classroomId: string,
  newStudents: Array<Omit<StudentItem, 'id'>>,
  replaceExisting: boolean = false
): void => {
  const current = getClassrooms();
  const target = current.find((c) => c.id === classroomId);
  if (!target) return;

  const formattedNew: StudentItem[] = newStudents.map((s, idx) => ({
    ...s,
    id: `std-${Date.now()}-${idx}-${Math.random().toString(36).substring(2, 7)}`,
  }));

  const mergedStudents = replaceExisting
    ? formattedNew
    : [...target.students, ...formattedNew];

  // Re-number sequentially if needed
  mergedStudents.forEach((s, idx) => {
    s.nomor_absen = idx + 1;
  });

  saveClassroom({
    ...target,
    students: mergedStudents,
  });
};

export const sortStudents = (classroomId: string, sortBy: 'absen' | 'nama'): void => {
  const current = getClassrooms();
  const target = current.find((c) => c.id === classroomId);
  if (!target) return;

  const sorted = [...target.students].sort((a, b) => {
    if (sortBy === 'nama') {
      return a.nama_lengkap.localeCompare(b.nama_lengkap);
    }
    return a.nomor_absen - b.nomor_absen;
  });

  saveClassroom({
    ...target,
    students: sorted,
  });
};
