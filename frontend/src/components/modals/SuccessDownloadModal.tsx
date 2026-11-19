import React, { useState } from 'react';
import {
  CheckCircle2,
  FileText,
  FileSpreadsheet,
  Download,
  MessageCircle,
  Link2,
  Share2,
  X,
  Check,
} from 'lucide-react';
import { DocumentGenerateResponse, TeacherProfile } from '../../types';

interface SuccessDownloadModalProps {
  isOpen: boolean;
  result: DocumentGenerateResponse | null;
  teacher: TeacherProfile;
  onClose: () => void;
  onDownload: (url: string, filename: string) => void;
}

export const SuccessDownloadModal: React.FC<SuccessDownloadModalProps> = ({
  isOpen,
  result,
  teacher,
  onClose,
  onDownload,
}) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !result) return null;

  const isExcel = result.file_format === 'xlsx';
  const isPdf = result.file_format === 'pdf';
  const formatLabel = isExcel ? 'EXCEL (.XLSX)' : isPdf ? 'PDF (.PDF)' : 'WORD (.DOCX)';

  const handleCopyLink = () => {
    navigator.clipboard?.writeText('https://gurudok.id');
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleSendToOwnWa = () => {
    const cleanPhone = teacher.no_whatsapp.replace(/[^0-9]/g, '');
    const waPhone = cleanPhone.startsWith('0')
      ? `62${cleanPhone.slice(1)}`
      : cleanPhone;
    const text = encodeURIComponent(
      `Halo Ibu/Bapak ${teacher.nama_guru},\nBerikut berkas administrasi mengajar Anda dari *GuruDok.id*:\n\n📄 *${result.filename}*\n🏫 ${teacher.nama_sekolah}\n🖨️ Ukuran Kertas: ${result.paper_size}\n\nUnduh di: ${window.location.origin}${result.download_url}`
    );
    window.open(`https://wa.me/${waPhone}?text=${text}`, '_blank');
  };

  const handleShareToGroup = () => {
    const text = encodeURIComponent(
      `Bapak/Ibu Guru, sekarang buat Modul Ajar/RPP Deep Learning 3M, ATP, CP-TP BSKAP 046/2025, Prota & Promes Word/Excel siap cetak F4 cuma butuh 2 menit dan *100% GRATIS* di:\n👉 https://gurudok.id`
    );
    window.open(`https://wa.me/?text=${text}`, '_blank');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-md">
      <div className="clay-card relative w-full max-w-lg p-6 text-center sm:p-8">
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Tutup Modal"
          className="clay-btn-white absolute right-5 top-5 flex h-8 w-8 items-center justify-center rounded-full"
        >
          <X className="h-4 w-4 text-slate-600" />
        </button>

        {/* Big 3D Emerald Green Checkmark */}
        <div className="clay-icon-green mx-auto flex h-16 w-16 items-center justify-center rounded-2xl shadow-lg">
          <CheckCircle2 className="h-9 w-9 text-white" />
        </div>

        {/* Title & Subtitle */}
        <h3 className="mt-4 text-xl font-extrabold text-slate-900 sm:text-2xl">
          Dokumen Berhasil Dibuat!
        </h3>
        <p className="mt-1 text-xs font-medium text-slate-500 sm:text-sm">
          Berkas administrasi Anda telah selesai disusun rapi dalam{' '}
          <span className="font-bold text-emerald-700">{result.execution_time_ms} ms</span>.
        </p>

        {/* File Info Card */}
        <div className="clay-input mt-5 flex items-center gap-3.5 p-4 text-left">
          <div
            className={`${
              isExcel ? 'clay-icon-green' : 'clay-icon-blue'
            } flex h-11 w-11 shrink-0 items-center justify-center rounded-full`}
          >
            {isExcel ? (
              <FileSpreadsheet className="h-5 w-5 text-white" />
            ) : (
              <FileText className="h-5 w-5 text-white" />
            )}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-extrabold text-slate-900 sm:text-sm">
              {result.filename}
            </p>
            <p className="mt-0.5 text-[11px] font-semibold text-slate-500">
              Ukuran: {result.file_size_human} • Tebal: ± {result.total_pages_approx} Halaman • Kertas:{' '}
              {result.paper_size}
            </p>
            <p className="text-[11px] font-bold text-slate-600">
              Kop Resmi: {teacher.nama_sekolah}
            </p>
          </div>
        </div>

        {/* Primary Download & Secondary WhatsApp CTAs */}
        <div className="mt-5 space-y-3">
          <button
            type="button"
            onClick={() => onDownload(result.download_url, result.filename)}
            className="clay-btn-primary flex w-full items-center justify-center gap-2.5 py-3.5 text-xs font-extrabold sm:text-sm"
          >
            <Download className="h-4 w-4" />
            <span>Download File {formatLabel} Siap Print &amp; Edit</span>
          </button>

          <button
            type="button"
            onClick={handleSendToOwnWa}
            className="clay-btn-success flex w-full items-center justify-center gap-2.5 py-3.5 text-xs font-extrabold sm:text-sm"
          >
            <MessageCircle className="h-4 w-4" />
            <span>Kirim Salinan File ke WhatsApp Saya</span>
          </button>
        </div>

        {/* Viral Share Row */}
        <div className="mt-6 border-t border-slate-200/70 pt-4">
          <p className="text-[11px] font-semibold text-slate-500">
            Bagikan ke sesama rekan guru di sekolah agar administrasi mereka juga beres:
          </p>

          <div className="mt-3 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
            <button
              type="button"
              onClick={handleCopyLink}
              className="clay-btn-white flex items-center justify-center gap-1.5 py-2.5 text-xs font-extrabold text-slate-700"
            >
              {copied ? (
                <>
                  <Check className="h-3.5 w-3.5 text-emerald-600" />
                  <span className="text-emerald-700">Tautan Tersalin!</span>
                </>
              ) : (
                <>
                  <Link2 className="h-3.5 w-3.5 text-slate-500" />
                  <span>Salin Tautan: gurudok.id</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handleShareToGroup}
              className="clay-btn-white flex items-center justify-center gap-1.5 py-2.5 text-xs font-extrabold text-slate-700"
            >
              <Share2 className="h-3.5 w-3.5 text-slate-500" />
              <span>Bagikan ke Grup WA Guru</span>
            </button>
          </div>
        </div>

        {/* Bottom Close Action */}
        <div className="mt-5 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="rounded-full bg-blue-50 px-4 py-1.5 text-xs font-extrabold text-blue-700 hover:bg-blue-100"
          >
            Selesai / Buat Bab Lain
          </button>
        </div>
      </div>
    </div>
  );
};
