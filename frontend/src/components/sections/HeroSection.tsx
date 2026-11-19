import React from 'react';
import {
  BookOpen,
  FileText,
  FileSpreadsheet,
  Calendar,
  ListOrdered,
  LayoutGrid,
  History,
  CheckSquare,
  ClipboardList,
} from 'lucide-react';
import { CORE_SERVICES } from '../../constants/services';
import { ServiceId } from '../../types';

interface HeroSectionProps {
  onOpenCatalog: () => void;
  onOpenHistory: () => void;
  onSelectService: (serviceId: ServiceId) => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  onOpenCatalog,
  onOpenHistory,
  onSelectService,
}) => {
  const activeServices = CORE_SERVICES.filter((s) => !s.isComingSoon);

  const renderServiceIcon = (id: string) => {
    if (id === '06_promes') return <FileSpreadsheet className="h-6 w-6 text-white" />;
    if (id === '08_modul_ajar') return <BookOpen className="h-6 w-6 text-white" />;
    if (id === '05_prota') return <Calendar className="h-6 w-6 text-white" />;
    if (id === '04_atp') return <ListOrdered className="h-6 w-6 text-white" />;
    if (id === '07_kktp') return <CheckSquare className="h-6 w-6 text-white" />;
    if (id === '09_lkpd') return <ClipboardList className="h-6 w-6 text-white" />;
    return <FileText className="h-6 w-6 text-white" />;
  };

  return (
    <section className="relative flex min-h-[calc(100vh-140px)] w-full flex-col justify-center overflow-hidden">
      {/* Full-Screen Thin Grid & Large Centered Radial Glow */}
      <div className="hero-grid-bg pointer-events-none absolute inset-0" />
      <div className="hero-radial-glow pointer-events-none absolute inset-0" />

      <div className="relative z-10 mx-auto flex w-full max-w-5xl flex-col items-center px-4 py-8 text-center sm:px-6 sm:py-12 lg:px-8">
        {/* Centered Headline Text */}
        <h1 className="max-w-3xl text-3xl font-extrabold leading-tight tracking-tight text-slate-900 sm:text-4xl lg:text-5xl">
          Bereskan Administrasi Guru{' '}
          <span className="text-blue-700">dalam Hitungan Menit</span>
        </h1>

        {/* Centered Sub Headline */}
        <p className="mt-3 max-w-xl text-sm font-medium leading-relaxed text-slate-600 sm:mt-4 sm:text-base">
          Pilih layanan dan unduh dokumennya langsung. Rapi, otomatis, dan sesuai standar BSKAP 2025.
        </p>

        {/* Planetary Orbit Stage around /hero-clay-3d.png (3 Orbit Independen Pelan) */}
        <div className="relative my-6 flex h-72 w-72 items-center justify-center sm:my-8 sm:h-80 sm:w-80">
          {/* 3 Subtle Orbital Rings */}
          <div className="pointer-events-none absolute inset-0 rounded-full border border-dashed border-blue-400/35" />
          <div className="pointer-events-none absolute inset-6 rounded-full border border-dashed border-emerald-400/30" />
          <div className="pointer-events-none absolute inset-12 rounded-full border border-rose-400/25" />

          {/* Orbit 1 (Luar — 42s CW): Word 3D Clay */}
          <div className="animate-orbit-1 pointer-events-none absolute inset-0">
            <div className="absolute -top-6 left-1/2 -translate-x-1/2">
              <img
                src="/doc-word-clay.png"
                alt="Dokumen Word 3D Clay"
                className="animate-orbit-counter-1 h-12 w-12 object-contain drop-shadow-xl sm:h-14 sm:w-14"
              />
            </div>
          </div>

          {/* Orbit 2 (Tengah — 34s CCW): Excel 3D Clay */}
          <div
            className="animate-orbit-2 pointer-events-none absolute inset-6"
            style={{ animationDelay: '-10s' }}
          >
            <div className="absolute -bottom-5 left-1/2 -translate-x-1/2">
              <img
                src="/doc-excel-clay.png"
                alt="Dokumen Excel 3D Clay"
                className="animate-orbit-counter-2 h-11 w-11 object-contain drop-shadow-xl sm:h-12 sm:w-12"
                style={{ animationDelay: '-10s' }}
              />
            </div>
          </div>

          {/* Orbit 3 (Dalam — 26s CW): PDF 3D Clay */}
          <div
            className="animate-orbit-3 pointer-events-none absolute inset-12"
            style={{ animationDelay: '-5s' }}
          >
            <div className="absolute top-1/2 -right-5 -translate-y-1/2">
              <img
                src="/doc-pdf-clay.png"
                alt="Dokumen PDF 3D Clay"
                className="animate-orbit-counter-3 h-10 w-10 object-contain drop-shadow-xl sm:h-11 sm:w-11"
                style={{ animationDelay: '-5s' }}
              />
            </div>
          </div>

          {/* Center 3D Clay Illustration (Tanpa Box) */}
          <img
            src="/hero-clay-3d.png"
            alt="Ilustrasi 3D Administrasi Guru GuruDok.id"
            className="relative z-10 h-36 w-36 object-contain drop-shadow-2xl transition-transform duration-300 hover:scale-105 sm:h-44 sm:w-44"
          />
        </div>

        {/* Centered Quick Service Section (Tanpa Box Pembungkus) */}
        <div className="mt-2 w-full">
          <h2 className="text-xs font-extrabold uppercase tracking-wider text-slate-500 sm:text-sm">
            Quick Service
          </h2>

          <div className="mt-4 flex flex-wrap items-start justify-center gap-5 sm:gap-8">
            {activeServices.map((srv) => (
              <button
                key={srv.id}
                type="button"
                onClick={() => onSelectService(srv.id as ServiceId)}
                className="group flex w-20 flex-col items-center gap-2 focus:outline-none sm:w-24"
              >
                <div
                  className={`${
                    srv.iconColor === 'green' ? 'clay-icon-green' : 'clay-icon-blue'
                  } flex h-12 w-12 items-center justify-center rounded-2xl shadow-lg transition-all duration-200 group-hover:-translate-y-1 group-hover:scale-110 sm:h-14 sm:w-14`}
                >
                  {renderServiceIcon(srv.id)}
                </div>
                <span className="text-center text-xs font-bold leading-tight text-slate-700 transition group-hover:text-blue-700">
                  {srv.shortTitle || srv.title}
                </span>
              </button>
            ))}

            {/* Quick Link: Katalog */}
            <button
              type="button"
              onClick={onOpenCatalog}
              className="group flex w-20 flex-col items-center gap-2 focus:outline-none sm:w-24"
            >
              <div className="clay-icon-blue flex h-12 w-12 items-center justify-center rounded-2xl shadow-lg transition-all duration-200 group-hover:-translate-y-1 group-hover:scale-110 sm:h-14 sm:w-14">
                <LayoutGrid className="h-6 w-6 text-white" />
              </div>
              <span className="text-center text-xs font-bold leading-tight text-slate-700 transition group-hover:text-blue-700">
                Katalog
              </span>
            </button>

            {/* Quick Link: Riwayat */}
            <button
              type="button"
              onClick={onOpenHistory}
              className="group flex w-20 flex-col items-center gap-2 focus:outline-none sm:w-24"
            >
              <div className="clay-icon-amber flex h-12 w-12 items-center justify-center rounded-2xl shadow-lg transition-all duration-200 group-hover:-translate-y-1 group-hover:scale-110 sm:h-14 sm:w-14">
                <History className="h-6 w-6 text-white" />
              </div>
              <span className="text-center text-xs font-bold leading-tight text-slate-700 transition group-hover:text-blue-700">
                Riwayat
              </span>
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};
