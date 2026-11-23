import React, { useState, useEffect } from 'react';
import { CustomChapterItem, CustomTpItem } from '../../types';
import { Plus, Trash2, X, AlertCircle } from 'lucide-react';

interface ChapterEditorModalProps {
  isOpen: boolean;
  chapterToEdit: CustomChapterItem | null;
  defaultSemester?: number;
  suggestedChapterNumber?: number;
  availableCpElements?: { kode_elemen: string; nama_elemen: string; deskripsi_cp: string }[];
  onSave: (chapter: CustomChapterItem) => void;
  onClose: () => void;
}

export const ChapterEditorModal: React.FC<ChapterEditorModalProps> = ({
  isOpen,
  chapterToEdit,
  defaultSemester = 1,
  suggestedChapterNumber = 1,
  availableCpElements = [],
  onSave,
  onClose,
}) => {
  const [nomorBab, setNomorBab] = useState<number>(suggestedChapterNumber);
  const [semester, setSemester] = useState<number>(defaultSemester);
  const [judulBab, setJudulBab] = useState<string>('');
  const [elemenCp, setElemenCp] = useState<string>('Pemahaman Konsep & Keterampilan Proses');
  const [alokasiJp, setAlokasiJp] = useState<number>(18);
  const [tps, setTps] = useState<CustomTpItem[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (chapterToEdit) {
      setNomorBab(chapterToEdit.nomor_bab);
      setSemester(chapterToEdit.semester);
      setJudulBab(chapterToEdit.judul_bab);
      setElemenCp(chapterToEdit.elemen_cp || 'Pemahaman Konsep & Keterampilan Proses');
      setAlokasiJp(chapterToEdit.alokasi_jp_bab);
      setTps(
        chapterToEdit.tujuan_pembelajaran && chapterToEdit.tujuan_pembelajaran.length > 0
          ? [...chapterToEdit.tujuan_pembelajaran]
          : [
              {
                code: `TP.${chapterToEdit.nomor_bab}.1`,
                deskripsi: `Memahami konsep pokok materi ${chapterToEdit.judul_bab || ''}`,
                alokasi_jp: Math.floor(chapterToEdit.alokasi_jp_bab / 2) || 9,
              },
              {
                code: `TP.${chapterToEdit.nomor_bab}.2`,
                deskripsi: `Menerapkan dan menyelesaikan masalah kontekstual materi ${chapterToEdit.judul_bab || ''}`,
                alokasi_jp: Math.ceil(chapterToEdit.alokasi_jp_bab / 2) || 9,
              },
            ]
      );
    } else {
      setNomorBab(suggestedChapterNumber);
      setSemester(defaultSemester);
      setJudulBab('');
      setElemenCp(availableCpElements[0]?.nama_elemen || 'Pemahaman Konsep & Keterampilan Proses');
      setAlokasiJp(18);
      setTps([
        { code: `TP.${suggestedChapterNumber}.1`, deskripsi: '', alokasi_jp: 9 },
        { code: `TP.${suggestedChapterNumber}.2`, deskripsi: '', alokasi_jp: 9 },
      ]);
    }
    setErrorMsg(null);
  }, [chapterToEdit, suggestedChapterNumber, defaultSemester, isOpen]);

  if (!isOpen) return null;

  const handleAddTp = () => {
    const nextIdx = tps.length + 1;
    setTps([
      ...tps,
      {
        code: `TP.${nomorBab}.${nextIdx}`,
        deskripsi: '',
        alokasi_jp: 6,
      },
    ]);
  };

  const handleRemoveTp = (index: number) => {
    if (tps.length <= 1) {
      setErrorMsg('Setiap bab minimal memiliki 1 butir Tujuan Pembelajaran (TP).');
      return;
    }
    setTps(tps.filter((_, idx) => idx !== index));
  };

  const handleTpChange = (index: number, field: keyof CustomTpItem, value: any) => {
    const next = [...tps];
    next[index] = { ...next[index], [field]: value };
    setTps(next);
  };

  const handleSave = () => {
    if (!judulBab.trim()) {
      setErrorMsg('Judul bab wajib diisi.');
      return;
    }
    if (alokasiJp <= 0) {
      setErrorMsg('Alokasi JP bab harus lebih besar dari 0.');
      return;
    }

    // Clean TPs
    const cleanTps = tps
      .filter((t) => t.deskripsi.trim().length > 0)
      .map((t, idx) => ({
        code: t.code || `TP.${nomorBab}.${idx + 1}`,
        deskripsi: t.deskripsi.trim(),
        alokasi_jp: Number(t.alokasi_jp) || Math.floor(alokasiJp / Math.max(1, tps.length)),
      }));

    const result: CustomChapterItem = {
      id_bab: chapterToEdit?.id_bab || `CUSTOM-B${nomorBab.toString().padStart(2, '0')}`,
      nomor_bab: Number(nomorBab),
      semester: Number(semester),
      judul_bab: judulBab.trim(),
      elemen_cp: elemenCp,
      alokasi_jp_bab: Number(alokasiJp),
      estimasi_jumlah_pertemuan: Math.max(1, Math.ceil(alokasiJp / 3)),
      rentang_minggu_promes: chapterToEdit?.rentang_minggu_promes || `Minggu Efektif Semester ${semester}`,
      tujuan_pembelajaran: cleanTps.length > 0 ? cleanTps : undefined,
    };

    onSave(result);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="w-full max-w-2xl bg-white rounded-3xl p-6 sm:p-8 shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto"
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-5">
          <h2 className="text-lg sm:text-xl font-black text-slate-800">
            {chapterToEdit ? 'Edit Bab / Lingkup Materi' : 'Tambah Bab Baru'}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Nomor Bab
              </label>
              <input
                type="number"
                min={1}
                max={50}
                value={nomorBab}
                onChange={(e) => setNomorBab(parseInt(e.target.value) || 1)}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Semester
              </label>
              <select
                value={semester}
                onChange={(e) => setSemester(parseInt(e.target.value) || 1)}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              >
                <option value={1}>Semester 1 (Ganjil)</option>
                <option value={2}>Semester 2 (Genap)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Alokasi JP Bab
              </label>
              <input
                type="number"
                min={1}
                max={200}
                value={alokasiJp}
                onChange={(e) => setAlokasiJp(parseInt(e.target.value) || 1)}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Judul Bab / Lingkup Materi Pokok
            </label>
            <input
              type="text"
              value={judulBab}
              onChange={(e) => setJudulBab(e.target.value)}
              placeholder="Contoh: Eksplorasi Keanekaragaman Hayati Pesisir"
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-bold text-slate-700">
                Elemen Capaian Pembelajaran (CP)
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
              className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
            {availableCpElements && availableCpElements.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5 items-center">
                <span className="text-[11px] font-semibold text-slate-500 mr-1">Pilih Cepat:</span>
                {availableCpElements.map((elem) => (
                  <button
                    key={elem.kode_elemen}
                    type="button"
                    onClick={() => setElemenCp(elem.nama_elemen)}
                    className={`px-2.5 py-1 text-xs rounded-lg font-medium transition-all ${
                      elemenCp === elem.nama_elemen
                        ? 'bg-indigo-600 text-white shadow-sm ring-1 ring-indigo-600'
                        : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200'
                    }`}
                  >
                    {elem.nama_elemen}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* TP Management */}
          <div className="pt-2">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-slate-700">
                Tujuan Pembelajaran (TP) pada Bab Ini
              </label>
              <button
                type="button"
                onClick={handleAddTp}
                className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Tambah Butir TP</span>
              </button>
            </div>

            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {tps.map((tp, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2 p-2.5 bg-slate-50 rounded-xl border border-slate-200"
                >
                  <div className="w-20 shrink-0">
                    <input
                      type="text"
                      value={tp.code}
                      onChange={(e) => handleTpChange(idx, 'code', e.target.value)}
                      placeholder="Kode"
                      className="w-full px-2 py-1.5 text-xs bg-white border border-slate-200 rounded-lg text-slate-700 font-mono"
                    />
                  </div>
                  <div className="flex-1">
                    <input
                      type="text"
                      value={tp.deskripsi}
                      onChange={(e) => handleTpChange(idx, 'deskripsi', e.target.value)}
                      placeholder={`Deskripsi TP ${idx + 1}...`}
                      className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-200 rounded-lg text-slate-800"
                    />
                  </div>
                  <div className="w-16 shrink-0">
                    <input
                      type="number"
                      min={1}
                      value={tp.alokasi_jp}
                      onChange={(e) =>
                        handleTpChange(idx, 'alokasi_jp', parseInt(e.target.value) || 2)
                      }
                      title="Alokasi JP TP"
                      placeholder="JP"
                      className="w-full px-2 py-1.5 text-xs bg-white border border-slate-200 rounded-lg text-slate-700 text-center"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveTp(idx)}
                    className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg transition-colors"
                    title="Hapus TP"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-slate-100">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 rounded-xl hover:bg-slate-100 transition-colors"
          >
            Batal
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="px-5 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-md hover:shadow-lg transition-all"
          >
            Simpan Bab
          </button>
        </div>
      </div>
    </div>
  );
};
