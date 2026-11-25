import React from 'react';
import {
  FileText,
  FileSpreadsheet,
  FileArchive,
  Download,
  MessageCircle,
  X,
} from 'lucide-react';
import { DocumentGenerateResponse, TeacherProfile } from '../../types';

interface SuccessDownloadModalProps {
  isOpen: boolean;
  result: DocumentGenerateResponse | null;
  teacher?: TeacherProfile;
  onClose: () => void;
  onDownload: (url: string, filename: string) => void;
}

export const SuccessDownloadModal: React.FC<SuccessDownloadModalProps> = ({
  isOpen,
  result,
  onClose,
  onDownload,
}) => {
  if (!isOpen || !result) return null;

  const isExcel = result.file_format === 'xlsx';
  const isPdf = result.file_format === 'pdf';
  const isZip = result.file_format === 'zip';
  const formatBadge = isZip
    ? 'Paket ZIP (.zip)'
    : isExcel
    ? 'Excel (.xlsx)'
    : isPdf
    ? 'PDF (.pdf)'
    : 'Word (.docx)';

  const handleShareToWhatsApp = () => {
    // Session-protected web link: opening this URL checks auth session before allowing download
    const shareUrl = `${window.location.origin}/?download_file=${encodeURIComponent(result.filename)}`;
    const text = encodeURIComponent(
      `Halo Bapak/Ibu Guru,\nBerikut link unduhan dokumen administrasi mengajar:\n📄 *${result.filename}*\n\nUnduh dokumen di sini:\n👉 ${shareUrl}`
    );
    window.open(`https://wa.me/?text=${text}`, '_blank');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
      <div className="clay-card relative w-full max-w-md p-6 text-center sm:p-7">
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Tutup Modal"
          className="clay-btn-white absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full text-slate-500 hover:text-slate-800"
        >
          <X className="h-4 w-4" />
        </button>

        {/* File Icon & Badge */}
        <div className="mx-auto flex flex-col items-center">
          <div
            className={`flex h-16 w-16 items-center justify-center rounded-2xl shadow-md ${
              isZip
                ? 'bg-gradient-to-br from-amber-500 to-orange-600 text-white'
                : isExcel
                ? 'clay-icon-green bg-gradient-to-br from-emerald-500 to-teal-600'
                : isPdf
                ? 'bg-gradient-to-br from-rose-500 to-red-600 text-white'
                : 'clay-icon-blue bg-gradient-to-br from-blue-500 to-indigo-600'
            }`}
          >
            {isZip ? (
              <FileArchive className="h-8 w-8 text-white" />
            ) : isExcel ? (
              <FileSpreadsheet className="h-8 w-8 text-white" />
            ) : (
              <FileText className="h-8 w-8 text-white" />
            )}
          </div>

          <span className="mt-3 inline-block rounded-full bg-slate-100 px-3 py-1 text-[11px] font-bold text-slate-600">
            {formatBadge}
          </span>

          {/* Clean File Name */}
          <h3
            className="mt-2.5 max-w-full break-all px-2 text-base font-extrabold text-slate-900 sm:text-lg"
            title={result.filename}
          >
            {result.filename}
          </h3>
        </div>

        {/* Primary Download & WhatsApp Share CTAs */}
        <div className="mt-6 space-y-3">
          <button
            type="button"
            onClick={() => onDownload(result.download_url, result.filename)}
            className="clay-btn-primary flex w-full items-center justify-center gap-2.5 py-3.5 text-sm font-extrabold"
          >
            <Download className="h-4 w-4" />
            <span>Download Dokumen</span>
          </button>

          <button
            type="button"
            onClick={handleShareToWhatsApp}
            className="clay-btn-success flex w-full items-center justify-center gap-2.5 py-3.5 text-sm font-extrabold"
          >
            <MessageCircle className="h-4 w-4" />
            <span>Bagikan Link ke WhatsApp</span>
          </button>
        </div>
      </div>
    </div>
  );
};
