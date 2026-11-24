import React from 'react';
import { DatabaseZap, X } from 'lucide-react';

interface CacheConsentBadgeProps {
  isVisible: boolean;
  isSaving?: boolean;
  onAllow: () => void;
  onDismiss: () => void;
}

export const CacheConsentBadge: React.FC<CacheConsentBadgeProps> = ({
  isVisible,
  isSaving = false,
  onAllow,
  onDismiss,
}) => {
  if (!isVisible) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed bottom-20 left-4 right-4 z-40 mx-auto max-w-md sm:bottom-5 sm:left-auto sm:right-5 sm:w-[360px]"
    >
      <div className="clay-card flex items-start gap-3 border border-blue-200 bg-white/95 p-3.5 shadow-xl backdrop-blur-md">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
          <DatabaseZap className="h-5 w-5" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <p className="text-xs font-extrabold text-slate-900">
              Izinkan Cache Lokal
            </p>
            <button
              type="button"
              onClick={onDismiss}
              aria-label="Tutup"
              className="rounded p-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
          <p className="mt-0.5 text-[11px] leading-snug text-slate-600">
            Simpan aset ikon di perangkat &amp; akun Anda agar perpindahan halaman instan tanpa unduh ulang.
          </p>
          <div className="mt-2.5 flex items-center gap-2">
            <button
              type="button"
              disabled={isSaving}
              onClick={onAllow}
              className="clay-btn-primary px-3 py-1.5 text-[11px] font-bold"
            >
              {isSaving ? 'Menyimpan...' : 'Allow Cache'}
            </button>
            <button
              type="button"
              onClick={onDismiss}
              className="rounded-lg border border-slate-200 px-2.5 py-1.5 text-[11px] font-semibold text-slate-600 hover:bg-slate-50"
            >
              Nanti
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
