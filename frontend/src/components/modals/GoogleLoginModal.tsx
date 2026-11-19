import React, { useEffect, useRef, useState } from 'react';
import { ShieldCheck, Lock, X, AlertCircle } from 'lucide-react';
import { apiClient } from '../../services/api';
import { AuthUser } from '../../types';

interface GoogleLoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: AuthUser) => void;
}

declare global {
  interface Window {
    google?: {
      accounts?: {
        id?: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string }) => void;
          }) => void;
          renderButton: (
            parent: HTMLElement,
            options: Record<string, string | number>
          ) => void;
        };
      };
    };
  }
}

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

export const GoogleLoginModal: React.FC<GoogleLoginModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const buttonContainerRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen || !GOOGLE_CLIENT_ID) return;
    setError(null);

    let timer: number | undefined;
    const initGoogleButton = () => {
      const gId = window.google?.accounts?.id;
      if (!gId || !buttonContainerRef.current) {
        timer = window.setTimeout(initGoogleButton, 250);
        return;
      }

      buttonContainerRef.current.innerHTML = '';
      gId.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: async (response: { credential: string }) => {
          setIsLoading(true);
          setError(null);
          try {
            const res = await apiClient.loginWithGoogle(response.credential);
            onSuccess(res.user);
          } catch (err: unknown) {
            const msg =
              err instanceof Error
                ? err.message
                : 'Gagal memverifikasi akun Google. Silakan coba lagi.';
            setError(msg);
          } finally {
            setIsLoading(false);
          }
        },
      });

      gId.renderButton(buttonContainerRef.current, {
        theme: 'outline',
        size: 'large',
        shape: 'pill',
        text: 'signin_with',
        width: 300,
      });
    };

    initGoogleButton();
    return () => {
      if (timer) window.clearTimeout(timer);
    };
  }, [isOpen, onSuccess]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
      <div className="clay-card relative w-full max-w-md p-6 sm:p-7">
        <button
          type="button"
          onClick={onClose}
          className="clay-btn-white absolute right-5 top-5 flex h-8 w-8 items-center justify-center rounded-lg"
          aria-label="Tutup modal login"
        >
          <X className="h-4 w-4 text-slate-600" />
        </button>

        <div className="flex flex-col items-center text-center">
          <div className="clay-icon-blue flex h-12 w-12 items-center justify-center rounded-2xl shadow-md">
            <Lock className="h-6 w-6 text-white" />
          </div>

          <h2 className="mt-4 text-xl font-extrabold text-slate-900">
            Masuk dengan Google untuk Mengunduh
          </h2>
          <p className="mt-2 text-xs font-medium leading-relaxed text-slate-600 sm:text-sm">
            Anda bebas menyusun dan melihat pratinjau dokumen tanpa batas. Masuk 1-klik dengan akun
            Google untuk mengunduh berkas <strong>Word / Excel / PDF</strong> dan menyimpan riwayat
            pribadi Anda.
          </p>
        </div>

        {error && (
          <div className="mt-4 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-3.5 py-2.5 text-xs font-semibold text-red-700">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="mt-6 flex flex-col items-center justify-center">
          {!GOOGLE_CLIENT_ID ? (
            <div className="w-full rounded-xl border border-amber-200 bg-amber-50 p-3.5 text-left text-xs text-amber-900">
              <p className="font-bold">Konfigurasi Google Client ID Diperlukan</p>
              <p className="mt-1">
                Variabel <code className="font-mono font-bold">VITE_GOOGLE_CLIENT_ID</code> belum
                diatur pada build frontend. Tambahkan OAuth Client ID di environment Coolify lalu
                redeploy.
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <div ref={buttonContainerRef} className="min-h-[44px]" />
              {isLoading && (
                <p className="text-xs font-bold text-blue-700">
                  Memverifikasi akun Google...
                </p>
              )}
            </div>
          )}
        </div>

        <div className="mt-5 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3.5 py-2.5 text-[11px] font-semibold text-emerald-800">
          <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-600" />
          <span>
            100% Gratis. Data profil KOP Sekolah tetap tersimpan aman hanya di browser Anda.
          </span>
        </div>
      </div>
    </div>
  );
};
