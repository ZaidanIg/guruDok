export type Jenjang = 'SD' | 'SMP' | 'SMA';
export type PaperSize = 'F4' | 'A4';
export type OutputFormat = 'docx' | 'xlsx' | 'pdf';
export type ServiceId = '03_cp_tp' | '04_atp' | '05_prota' | '06_promes' | '08_modul_ajar';

export interface LearningObjective {
  code: string;
  deskripsi: string;
  alokasi_jp: number;
  urutan_atp?: number;
  ringkasan_rapor?: string;
  level_kognitif_bloom?: string;
}

export interface ChapterTopic {
  id: string;
  semester: number;
  nomor_bab: number;
  judul_bab: string;
  alokasi_jp: number;
  elemen_cp?: string;
  estimasi_pertemuan?: number;
  rentang_minggu_promes?: string;
  tujuan_pembelajaran: LearningObjective[];
  dimensi_profil_lulusan: string[];
  model_pembelajaran_default: string;
  modul_ajar_template?: Record<string, any>;
}

export interface CurriculumSubject {
  id: string;
  id_mapel_bskap?: string;
  jenjang: Jenjang;
  kelas: number;
  fase: string;
  nama_mapel: string;
  alokasi_jp_mingguan: number;
  total_alokasi_jp_tahun: number;
  durasi_1_jp_menit?: number;
  buku_rujukan_sibi?: string;
  rasional_bskap?: string;
  tujuan_bskap?: string;
  karakteristik_bskap?: string;
  elemen_cp_resmi?: {
    kode_elemen: string;
    nama_elemen: string;
    deskripsi_cp: string;
  }[];
  bab_count: number;
  bab_list?: ChapterTopic[];
}

export interface TeacherProfile {
  id?: string;
  nama_guru: string;
  nip_guru: string;
  nama_sekolah: string;
  npsn?: string;
  kabupaten_kota: string;
  provinsi: string;
  nama_kepala_sekolah: string;
  nip_kepala_sekolah: string;
  no_whatsapp: string;
  email?: string;
  ukuran_kertas_default: PaperSize;
  created_at?: string;
}

export interface CustomTpItem {
  code: string;
  deskripsi: string;
  alokasi_jp: number;
}

export interface ChapterCreateRequest {
  nomor_bab: number;
  semester: number;
  judul_bab: string;
  elemen_cp: string;
  alokasi_jp: number;
  model_pembelajaran?: string;
  daftar_tp?: CustomTpItem[];
}

export interface CustomDocumentOverrides {
  alokasi_jp_bab?: number;
  tujuan_pembelajaran_custom?: CustomTpItem[];
  kesiapan_murid?: string;
  karakteristik_materi?: string;
  lintas_disiplin_ilmu?: string;
  topik_kontekstual?: string;
  pertanyaan_pemantik?: string[];
  sarana_prasarana?: string[];
  langkah_pendahuluan?: string[];
  langkah_inti_memahami?: string[];
  langkah_inti_mengaplikasi?: string[];
  langkah_inti_merefleksi?: string[];
  langkah_penutup?: string[];
  soal_asesmen_awal?: string[];
  soal_asesmen_proses?: string[];
  soal_asesmen_akhir?: string[];
  catatan_khusus?: string;
  cadangan_jp?: number;
}

export interface DocumentGenerateRequest {
  service_id: ServiceId;
  jenjang: Jenjang;
  kelas: number;
  subject_id: string;
  semester: number;
  chapter_id?: string;
  model_pembelajaran?: string;
  paper_size: PaperSize;
  output_format?: OutputFormat;
  teacher_profile?: TeacherProfile;
  include_lkpd: boolean;
  include_asesmen: boolean;
  include_rubrik: boolean;
  custom_overrides?: CustomDocumentOverrides;
}

export interface DocumentGenerateResponse {
  job_id: string;
  service_id: ServiceId;
  service_name: string;
  filename: string;
  file_format: OutputFormat;
  paper_size: PaperSize;
  download_url: string;
  file_size_bytes: number;
  file_size_human: string;
  total_pages_approx: number;
  execution_time_ms: number;
  created_at: string;
}

export interface HistoryDocumentItem {
  id: string;
  service_id: string;
  service_name: string;
  filename: string;
  file_format: OutputFormat;
  paper_size: PaperSize;
  file_url: string;
  file_size_human: string;
  created_at: string;
  parameters?: {
    jenjang?: Jenjang;
    kelas?: number;
    subject_id?: string;
    chapter_id?: string;
    semester?: number;
  };
}

export interface ServiceCatalogItem {
  id: ServiceId | 'coming_soon';
  codeLabel: string;
  title: string;
  shortTitle: string;
  description: string;
  formats: ('DOCX' | 'XLSX' | 'PDF')[];
  isFree: boolean;
  isPopular?: boolean;
  isComingSoon?: boolean;
  iconColor: 'blue' | 'green' | 'amber';
  requiresChapter: boolean;
}

export interface ApiEnvelope<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string | null;
  role: string;
}

export interface AuthLoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}
