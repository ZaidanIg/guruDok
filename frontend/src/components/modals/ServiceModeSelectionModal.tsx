import React from 'react';
import { GenerationMode, ServiceCatalogItem } from '../../types';
import { checkDraftAvailability } from '../../services/curriculumStorage';

interface ServiceModeSelectionModalProps {
  isOpen: boolean;
  service: ServiceCatalogItem | null;
  selectedSubjectId?: string;
  onSelectMode: (mode: GenerationMode) => void;
  onClose: () => void;
}

export const ServiceModeSelectionModal: React.FC<ServiceModeSelectionModalProps> = ({
  isOpen,
  service,
  selectedSubjectId,
  onSelectMode,
  onClose,
}) => {
  if (!isOpen || !service) return null;

  const { hasTemplateDraft, hasManualDraft } = checkDraftAvailability(
    service.id,
    selectedSubjectId || ''
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="w-full max-w-xl bg-white rounded-3xl p-6 sm:p-8 shadow-2xl border border-slate-100 animate-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
      >
        <div className="text-center mb-6">
          <h2 className="text-xl sm:text-2xl font-black text-slate-800 tracking-tight">
            {service.title}
          </h2>
          <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
            Pilih cara yang paling sesuai untuk menyusun administrasi kurikulum Anda.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 my-6">
          {/* Option 1: Gunakan Template */}
          <button
            type="button"
            onClick={() => onSelectMode('template')}
            className="group relative flex flex-col justify-between p-5 text-left bg-gradient-to-br from-indigo-50/50 via-white to-slate-50 rounded-2xl border-2 border-slate-200/80 hover:border-indigo-500 hover:shadow-lg transition-all duration-200"
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                  Gunakan Template
                </span>
                {hasTemplateDraft && (
                  <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                    Ada draf tersimpan
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Materi, alokasi JP, dan tujuan pembelajaran langsung terisi dari standar resmi BSKAP No. 046/2025 &amp; SIBI. Anda tetap memiliki kendali penuh untuk memodifikasi.
              </p>
            </div>
            <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-indigo-600 group-hover:translate-x-0.5 transition-transform">
              <span>Pilih Opsi Ini</span>
              <span>&rarr;</span>
            </div>
          </button>

          {/* Option 2: Buat Manual */}
          <button
            type="button"
            onClick={() => onSelectMode('manual')}
            className="group relative flex flex-col justify-between p-5 text-left bg-gradient-to-br from-slate-50/80 via-white to-slate-50 rounded-2xl border-2 border-slate-200/80 hover:border-slate-700 hover:shadow-lg transition-all duration-200"
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-base font-bold text-slate-900 group-hover:text-slate-800 transition-colors">
                  Buat Manual
                </span>
                {hasManualDraft && (
                  <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                    Ada draf tersimpan
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Mulai dari daftar kosong untuk menyusun materi, bab, alokasi JP, dan tujuan pembelajaran secara mandiri. Perubahan tersimpan otomatis di perangkat Anda.
              </p>
            </div>
            <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-slate-700 group-hover:translate-x-0.5 transition-transform">
              <span>Pilih Opsi Ini</span>
              <span>&rarr;</span>
            </div>
          </button>
        </div>

        <div className="flex justify-center mt-4">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2 text-xs font-semibold text-slate-500 hover:text-slate-700 transition-colors"
          >
            Batal
          </button>
        </div>
      </div>
    </div>
  );
};
