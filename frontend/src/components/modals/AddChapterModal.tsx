import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2, Loader2, BookPlus, AlertCircle } from 'lucide-react';
import { ChapterCreateRequest, ChapterTopic, CurriculumSubject, CustomTpItem } from '../../types';
import { PEDAGOGICAL_MODELS } from '../../constants/services';
import { apiClient } from '../../services/api';

interface AddChapterModalProps {
  isOpen: boolean;
  subject: CurriculumSubject | null;
  existingChapters: ChapterTopic[];
  activeSemester: number;
  onClose: () => void;
  onSuccess: (newChapter: ChapterTopic) => void;
}

export const AddChapterModal: React.FC<AddChapterModalProps> = ({
  isOpen,
  subject,
  existingChapters,
  activeSemester,
  onClose,
  onSuccess,
}) => {
  const [nomorBab, setNomorBab] = useState<number>(1);
  const [semester, setSemester] = useState<number>(activeSemester);
  const [judulBab, setJudulBab] = useState<string>('');
  const [elemenCp, setElemenCp] = useState<string>('');
  const [alokasiJp, setAlokasiJp] = useState<number>(12);
  const [modelPembelajaran, setModelPembelajaran] = useState<string>(PEDAGOGICAL_MODELS[0]);
  const [tps, setTps] = useState<CustomTpItem[]>([]);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Initialize or reset form whenever modal opens or subject changes
  useEffect(() => {
    if (isOpen && subject) {
      const nextNum =
        existingChapters.length > 0
          ? Math.max(...existingChapters.map((c) => c.nomor_bab)) + 1
          : 1;
      setNomorBab(nextNum);
      setSemester(activeSemester || 1);
      setJudulBab('');
      setErrorMsg(null);

      const defaultJp = subject.alokasi_jp_mingguan ? subject.alokasi_jp_mingguan * 3 : 12;
      setAlokasiJp(defaultJp);

      const officialElems = subject.elemen_cp_resmi || [];
      if (officialElems.length > 0) {
        setElemenCp(officialElems[0].nama_elemen);
      } else {
        setElemenCp('Pemahaman Konsep');
      }

      setTps([
        {
          code: `TP.${subject.kelas}.${nextNum}.1`,
          deskripsi: '',
          alokasi_jp: Math.max(2, Math.floor(defaultJp / 2)),
        },
        {
          code: `TP.${subject.kelas}.${nextNum}.2`,
          deskripsi: '',
          alokasi_jp: Math.max(2, defaultJp - Math.floor(defaultJp / 2)),
        },
      ]);
    }
  }, [isOpen, subject, existingChapters, activeSemester]);

  if (!isOpen || !subject) return null;

  const officialElems = subject.elemen_cp_resmi || [];

  const handleUpdateTp = (idx: number, field: keyof CustomTpItem, value: string | number) => {
    const nextList = tps.map((item, i) => (i === idx ? { ...item, [field]: value } : item));
    setTps(nextList);
  };

  const handleAddTp = () => {
    const nextIdx = tps.length + 1;
    setTps([
      ...tps,
      {
        code: `TP.${subject.kelas}.${nomorBab}.${nextIdx}`,
        deskripsi: '',
        alokasi_jp: 4,
      },
    ]);
  };

  const handleRemoveTp = (idx: number) => {
    if (tps.length <= 1) return;
    setTps(tps.filter((_, i) => i !== idx));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!judulBab.trim()) {
      setErrorMsg('Judul Bab / Materi Pokok wajib diisi.');
      return;
    }

    if (!elemenCp.trim()) {
      setErrorMsg('Elemen Capaian Pembelajaran wajib diisi.');
      return;
    }

    // Auto-fill empty TP descriptions if teacher didn't type them
    const sanitizedTps = tps.map((tp, idx) => ({
      code: tp.code.trim() || `TP.${subject.kelas}.${nomorBab}.${idx + 1}`,
      deskripsi:
        tp.deskripsi.trim() ||
        (idx === 0
          ? `Memahami dan menganalisis konsep ${judulBab.trim()}.`
          : `Menerapkan dan menyajikan penyelesaian masalah kontekstual terkait ${judulBab.trim()}.`),
      alokasi_jp: Number(tp.alokasi_jp) || 4,
    }));

    const payload: ChapterCreateRequest = {
      nomor_bab: Number(nomorBab),
      semester: Number(semester),
      judul_bab: judulBab.trim(),
      elemen_cp: elemenCp.trim(),
      alokasi_jp: Number(alokasiJp),
      model_pembelajaran: modelPembelajaran,
      daftar_tp: sanitizedTps,
    };

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const created = await apiClient.createChapter(subject.id, payload);
      onSuccess(created);
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Gagal menyimpan bab baru.';
      setErrorMsg(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
      <div className="clay-card relative max-h-[90vh] w-full max-w-2xl overflow-y-auto p-6 sm:p-8">
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className="clay-btn-white absolute right-5 top-5 flex h-8 w-8 items-center justify-center rounded-lg"
        >
          <X className="h-4 w-4 text-slate-600" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3 border-b border-slate-200 pb-4">
          <div className="clay-icon-blue flex h-10 w-10 shrink-0 items-center justify-center rounded-xl">
            <BookPlus className="h-5 w-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-extrabold text-slate-900 sm:text-xl">
              Tambah Bab Baru — {subject.nama_mapel}
            </h2>
            <p className="text-xs font-medium text-slate-500">
              {subject.jenjang} Kelas {subject.kelas} ({subject.fase}) • Disimpan ke database GuruDocDB
            </p>
          </div>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="mt-4 flex items-center gap-2.5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-xs font-bold text-red-700">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          {/* Row 1: Nomor Bab & Semester */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">
                Nomor Bab <span className="text-blue-600">*</span>
              </label>
              <input
                type="number"
                min={1}
                max={50}
                value={nomorBab}
                onChange={(e) => setNomorBab(Number(e.target.value))}
                required
                className="clay-input w-full px-3.5 py-2.5 text-xs font-bold text-slate-800 sm:text-sm"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">
                Semester <span className="text-blue-600">*</span>
              </label>
              <select
                value={semester}
                onChange={(e) => setSemester(Number(e.target.value))}
                className="clay-input w-full px-3.5 py-2.5 text-xs font-bold text-slate-800 sm:text-sm"
              >
                <option value={1}>Semester 1 (Ganjil)</option>
                <option value={2}>Semester 2 (Genap)</option>
              </select>
            </div>
          </div>

          {/* Row 2: Judul Bab / Materi Pokok */}
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">
              Judul Bab / Lingkup Materi Pokok <span className="text-blue-600">*</span>
            </label>
            <input
              type="text"
              value={judulBab}
              onChange={(e) => setJudulBab(e.target.value)}
              placeholder="Contoh: Kecerdasan Buatan dan Etika Digital"
              required
              className="clay-input w-full px-3.5 py-2.5 text-xs font-semibold text-slate-800 sm:text-sm placeholder:text-slate-400"
            />
          </div>

          {/* Row 3: Elemen CP */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-bold text-slate-700">
                Elemen Capaian Pembelajaran (CP) <span className="text-blue-600">*</span>
              </label>
              <span className="text-[11px] text-slate-500">
                Ketik langsung atau klik saran di bawah
              </span>
            </div>
            <input
              type="text"
              value={elemenCp}
              onChange={(e) => setElemenCp(e.target.value)}
              placeholder="Contoh: Pemahaman Konsep, Keterampilan Proses, dsb."
              required
              className="clay-input w-full px-3.5 py-2.5 text-xs font-semibold text-slate-800 sm:text-sm placeholder:text-slate-400"
            />
            {officialElems.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5 items-center">
                <span className="text-[11px] font-semibold text-slate-500 mr-1">Pilih Cepat:</span>
                {officialElems.map((el) => (
                  <button
                    key={el.kode_elemen}
                    type="button"
                    onClick={() => setElemenCp(el.nama_elemen)}
                    className={`px-2.5 py-1 text-xs rounded-lg font-medium transition-all ${
                      elemenCp === el.nama_elemen
                        ? 'bg-blue-600 text-white shadow-sm ring-1 ring-blue-600'
                        : 'bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200'
                    }`}
                  >
                    {el.nama_elemen}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Row 4: Alokasi JP Bab & Model Pedagogis */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">
                Alokasi Jam Pelajaran (JP) <span className="text-blue-600">*</span>
              </label>
              <input
                type="number"
                min={1}
                max={120}
                value={alokasiJp}
                onChange={(e) => setAlokasiJp(Number(e.target.value))}
                required
                className="clay-input w-full px-3.5 py-2.5 text-xs font-bold text-slate-800 sm:text-sm"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">
                Model Pembelajaran Pedagogis
              </label>
              <select
                value={modelPembelajaran}
                onChange={(e) => setModelPembelajaran(e.target.value)}
                className="clay-input w-full px-3.5 py-2.5 text-xs font-bold text-slate-800 sm:text-sm"
              >
                {PEDAGOGICAL_MODELS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Row 5: Tujuan Pembelajaran (TP) Awal */}
          <div className="border-t border-slate-200 pt-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-700">
                Tujuan Pembelajaran (TP) Awal untuk Bab Ini
              </label>
              <button
                type="button"
                onClick={handleAddTp}
                className="inline-flex items-center gap-1 text-xs font-bold text-blue-700 hover:text-blue-800"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Tambah Butir TP</span>
              </button>
            </div>

            <div className="mt-2.5 space-y-2.5">
              {tps.map((tp, idx) => (
                <div key={idx} className="clay-subcard flex items-start gap-2 p-2.5">
                  <div className="w-24 shrink-0">
                    <input
                      type="text"
                      value={tp.code}
                      onChange={(e) => handleUpdateTp(idx, 'code', e.target.value)}
                      className="clay-input w-full px-2 py-1 text-xs font-bold text-blue-800"
                    />
                  </div>

                  <div className="flex-1">
                    <input
                      type="text"
                      value={tp.deskripsi}
                      onChange={(e) => handleUpdateTp(idx, 'deskripsi', e.target.value)}
                      placeholder={`Deskripsi TP ${idx + 1}...`}
                      className="clay-input w-full px-2.5 py-1 text-xs font-medium text-slate-800 placeholder:text-slate-400"
                    />
                  </div>

                  <div className="flex w-16 shrink-0 items-center gap-1">
                    <input
                      type="number"
                      min={1}
                      max={40}
                      value={tp.alokasi_jp}
                      onChange={(e) =>
                        handleUpdateTp(idx, 'alokasi_jp', Math.max(1, Number(e.target.value) || 2))
                      }
                      className="clay-input w-full px-1.5 py-1 text-center text-xs font-bold text-slate-800"
                    />
                    <span className="text-[11px] font-bold text-slate-500">JP</span>
                  </div>

                  {tps.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveTp(idx)}
                      className="p-1 text-slate-400 hover:text-red-600"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2.5 border-t border-slate-200 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="clay-btn-white px-4 py-2.5 text-xs font-bold text-slate-700"
            >
              Batal
            </button>

            <button
              type="submit"
              disabled={isSubmitting}
              className="clay-btn-primary inline-flex items-center gap-2 px-5 py-2.5 text-xs font-bold disabled:opacity-60"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Menyimpan ke Database...</span>
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4" />
                  <span>Simpan &amp; Pilih Bab Ini</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
