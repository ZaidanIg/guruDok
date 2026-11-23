import React from 'react';
import { motion } from 'framer-motion';
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
      {/* Aurora Ambient Background Effect */}
      <div className="hero-aurora-bg pointer-events-none absolute inset-0">
        <div className="aurora-blob-1" />
        <div className="aurora-blob-2" />
        <div className="aurora-blob-3" />
      </div>

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

        {/* Brand Avatar Stage with Framer-Motion Pop-up Greeting */}
        <div className="relative my-7 flex items-center justify-center sm:my-9">
          {/* Circular Brand Avatar Container (White BG, Thin Black Border, Waist-up Framing) */}
          <div className="relative flex h-56 w-56 items-end justify-center overflow-hidden rounded-full border-[1.5px] border-slate-900 bg-white shadow-xl sm:h-64 sm:w-64">
            <img
              src="/character2.png"
              alt="Karakter Brand GuruDok"
              className="pointer-events-none h-full w-full select-none object-cover object-top scale-110 origin-top translate-y-1 transition-transform duration-300 hover:scale-115"
              draggable={false}
            />
          </div>

          {/* Pop-up Greeting Bubble (Animated with Framer Motion) */}
          <motion.div
            initial={{ opacity: 0, scale: 0.75, y: 15 }}
            animate={{
              opacity: 1,
              scale: 1,
              y: [0, -6, 0],
            }}
            transition={{
              opacity: { duration: 0.45, ease: 'easeOut', delay: 0.15 },
              scale: { type: 'spring', stiffness: 280, damping: 18, delay: 0.15 },
              y: {
                repeat: Infinity,
                repeatType: 'reverse',
                duration: 3.2,
                ease: 'easeInOut',
                delay: 0.6,
              },
            }}
            className="absolute -top-4 -right-4 z-20 max-w-[210px] rounded-2xl border border-slate-900 bg-white/95 px-3.5 py-2.5 text-left shadow-lg backdrop-blur-sm sm:-top-5 sm:-right-8 sm:max-w-[245px] sm:px-4 sm:py-3"
          >
            <div className="flex items-start gap-1.5">
              <span className="text-base sm:text-lg leading-none" role="img" aria-label="wave">
                👋
              </span>
              <p className="text-xs font-bold leading-snug text-slate-800 sm:text-sm">
                Selamat datang di website Administrasi guru
              </p>
            </div>
            {/* Speech Bubble Pointer Arrow */}
            <div className="absolute -bottom-1.5 left-7 h-3 w-3 rotate-45 border-b border-r border-slate-900 bg-white" />
          </motion.div>
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
