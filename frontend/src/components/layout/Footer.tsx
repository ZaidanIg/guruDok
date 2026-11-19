import React from 'react';
import { BookOpen } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-12 border-t border-slate-200 bg-white pb-20 md:pb-8">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 py-6 sm:flex-row sm:px-6 lg:px-8">
        <div className="flex items-center gap-2.5">
          <div className="clay-icon-blue flex h-7 w-7 items-center justify-center rounded-md">
            <BookOpen className="h-3.5 w-3.5 text-white" />
          </div>
          <span className="text-sm font-extrabold tracking-tight text-slate-900">
            GuruDok<span className="text-blue-700">.id</span>
          </span>
        </div>

        <p className="text-center text-xs font-medium text-slate-500">
          Sistem Penyusunan Dokumen Administrasi Kurikulum Merdeka — Kepka BSKAP No. 046/H/KR/2025 &amp; Permendikdasmen No. 13/2025
        </p>

        <div className="text-xs font-semibold text-slate-600">
          Standar Cetak F4 &amp; A4
        </div>
      </div>
    </footer>
  );
};
