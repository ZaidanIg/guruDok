import React, { useState, useEffect } from 'react';
import { CustomCpElementItem } from '../../types';
import { X, AlertCircle, Sparkles } from 'lucide-react';

interface CpElementEditorModalProps {
  isOpen: boolean;
  elementToEdit: CustomCpElementItem | null;
  suggestedCode?: string;
  onSave: (element: CustomCpElementItem) => void;
  onClose: () => void;
}

export const CpElementEditorModal: React.FC<CpElementEditorModalProps> = ({
  isOpen,
  elementToEdit,
  suggestedCode = 'EL-01',
  onSave,
  onClose,
}) => {
  const [kodeElemen, setKodeElemen] = useState<string>(suggestedCode);
  const [namaElemen, setNamaElemen] = useState<string>('');
  const [deskripsiCp, setDeskripsiCp] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (elementToEdit) {
      setKodeElemen(elementToEdit.kode_elemen);
      setNamaElemen(elementToEdit.nama_elemen);
      setDeskripsiCp(elementToEdit.deskripsi_cp);
    } else {
      setKodeElemen(suggestedCode);
      setNamaElemen('');
      setDeskripsiCp('');
    }
    setErrorMsg(null);
  }, [elementToEdit, suggestedCode, isOpen]);

  if (!isOpen) return null;

  const handleSave = () => {
    if (!namaElemen.trim()) {
      setErrorMsg('Nama Elemen CP wajib diisi (contoh: Pemahaman Konsep, Keterampilan Proses).');
      return;
    }
    if (!deskripsiCp.trim() || deskripsiCp.trim().length < 5) {
      setErrorMsg('Rumusan Deskripsi Capaian Pembelajaran wajib diisi minimal 5 karakter.');
      return;
    }

    const cleanElement: CustomCpElementItem = {
      kode_elemen: kodeElemen.trim() || suggestedCode,
      nama_elemen: namaElemen.trim(),
      deskripsi_cp: deskripsiCp.trim(),
    };

    onSave(cleanElement);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="w-full max-w-xl bg-white rounded-3xl p-6 sm:p-8 shadow-2xl border border-slate-100 max-h-[90vh] overflow-y-auto"
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <Sparkles className="w-4 h-4" />
            </div>
            <h2 className="text-lg sm:text-xl font-black text-slate-800">
              {elementToEdit ? 'Edit Elemen Capaian Pembelajaran' : 'Tambah Elemen CP Baru'}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form Body */}
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Kode Elemen
              </label>
              <input
                type="text"
                value={kodeElemen}
                onChange={(e) => setKodeElemen(e.target.value)}
                placeholder="Contoh: EL-01"
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Nama Elemen CP <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                value={namaElemen}
                onChange={(e) => setNamaElemen(e.target.value)}
                placeholder="Contoh: Pemahaman Konsep & Keterampilan Proses"
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Rumusan Kalimat Capaian Pembelajaran (CP) <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={5}
              value={deskripsiCp}
              onChange={(e) => setDeskripsiCp(e.target.value)}
              placeholder="Tuliskan rumusan capaian kompetensi peserta didik pada fase ini (BSKAP 046/H/KR/2025 atau muatan kontekstual sekolah)..."
              className="w-full px-3 py-2.5 text-xs sm:text-sm bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none leading-relaxed"
            />
            <p className="mt-1 text-[11px] text-slate-500">
              Rumusan ini akan otomatis tercetak pada dokumen CP-TP dan terhubung sebagai opsi elemen bab di ATP, Prota, Promes, KKTP, &amp; Modul Ajar.
            </p>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 pt-5 mt-5 border-t border-slate-100">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-bold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-xl transition-all"
          >
            Batal
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="px-5 py-2 text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-md shadow-indigo-100 transition-all flex items-center gap-1.5"
          >
            {elementToEdit ? 'Simpan Perubahan' : 'Tambahkan Elemen'}
          </button>
        </div>
      </div>
    </div>
  );
};
