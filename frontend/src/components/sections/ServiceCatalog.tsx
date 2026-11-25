import React, { useState } from 'react';
import {
  FileText,
  FileSpreadsheet,
  BookOpen,
  Calendar,
  ListOrdered,
  ChevronRight,
  Layers,
  X,
  CheckSquare,
  ClipboardList,
  Users,
  Award,
  BarChart3,
} from 'lucide-react';
import { CORE_SERVICES, UPCOMING_SERVICES, SERVICE_ICON_PACK } from '../../constants/services';
import { ServiceCatalogItem, ServiceId } from '../../types';

interface ServiceCatalogProps {
  selectedServiceId: ServiceId;
  searchQuery?: string;
  onSelectService: (serviceId: ServiceId) => void;
  onOpenClassroomModal?: () => void;
}

export const ServiceCatalog: React.FC<ServiceCatalogProps> = ({
  selectedServiceId,
  searchQuery = '',
  onSelectService,
  onOpenClassroomModal,
}) => {
  const [showRoadmapModal, setShowRoadmapModal] = useState(false);

  const renderIcon = (item: ServiceCatalogItem) => {
    if (item.id === '01_data_kelas') return <Users className="h-5 w-5 text-white" />;
    if (item.id === '06_promes') return <FileSpreadsheet className="h-5 w-5 text-white" />;
    if (item.id === '08_modul_ajar') return <BookOpen className="h-5 w-5 text-white" />;
    if (item.id === '05_prota') return <Calendar className="h-5 w-5 text-white" />;
    if (item.id === '04_atp') return <ListOrdered className="h-5 w-5 text-white" />;
    if (item.id === '07_kktp') return <CheckSquare className="h-5 w-5 text-white" />;
    if (item.id === '09_lkpd') return <ClipboardList className="h-5 w-5 text-white" />;
    if (item.id === '16_deskripsi_rapor') return <Award className="h-5 w-5 text-white" />;
    if (item.id === '17_rekap_rapor') return <BarChart3 className="h-5 w-5 text-white" />;
    if (item.id === 'coming_soon') return <Layers className="h-5 w-5 text-white" />;
    return <FileText className="h-5 w-5 text-white" />;
  };

  const getIconClass = (color: 'blue' | 'green' | 'amber') => {
    if (color === 'green') return 'clay-icon-green';
    if (color === 'amber') return 'clay-icon-amber';
    return 'clay-icon-blue';
  };

  const filteredServices = CORE_SERVICES.filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.title.toLowerCase().includes(q) ||
      item.description.toLowerCase().includes(q) ||
      item.shortTitle.toLowerCase().includes(q)
    );
  });

  return (
    <section id="katalog-section" className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      {/* Katalog Layanan Dokumen */}
      <div className="flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-end">
        <div>
          <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl">
            Katalog Layanan Administrasi Guru
          </h1>
          <p className="mt-1 text-xs font-medium text-slate-500 sm:text-sm">
            Pilih layanan di bawah ini untuk membuat dokumen.
          </p>
        </div>
      </div>

      {/* Responsive Grid: 1 col (mobile) -> 2 col (tablet) -> 3 col (laptop) -> 4-5 col (large screen) */}
      <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
        {filteredServices.map((item) => {
          const isSelected = item.id === selectedServiceId;

          return (
            <div
              key={item.id}
              className={`clay-card flex flex-col justify-between p-5 transition-all ${
                isSelected ? 'border-blue-600 ring-1 ring-blue-600' : 'hover:border-slate-300'
              }`}
            >
              <div>
                <div className="flex items-center justify-between">
                  {SERVICE_ICON_PACK[item.id] ? (
                    <div className="flex h-11 w-11 sm:h-12 sm:w-12 items-center justify-center">
                      <img
                        src={SERVICE_ICON_PACK[item.id]}
                        alt={item.title}
                        className="h-full w-full object-contain drop-shadow-md select-none pointer-events-none"
                        draggable={false}
                      />
                    </div>
                  ) : (
                    <div
                      className={`${getIconClass(
                        item.iconColor
                      )} flex h-10 w-10 items-center justify-center rounded-lg`}
                    >
                      {renderIcon(item)}
                    </div>
                  )}
                  <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-bold text-slate-600">
                    {item.codeLabel}
                  </span>
                </div>

                <h2 className="mt-3.5 text-base font-extrabold text-slate-900">
                  {item.title}
                </h2>
                <p className="mt-1.5 text-xs font-medium leading-relaxed text-slate-600">
                  {item.description}
                </p>

                <div className="mt-3 flex flex-wrap items-center gap-1.5">
                  {item.formats.map((fmt) => (
                    <span
                      key={fmt}
                      className="rounded border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-bold text-slate-600"
                    >
                      {fmt}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-5">
                {item.isComingSoon ? (
                  <button
                    type="button"
                    onClick={() => setShowRoadmapModal(true)}
                    className="clay-btn-white flex w-full items-center justify-between px-4 py-2.5 text-xs font-bold text-slate-700"
                  >
                    <span>Daftar 2 Layanan Tersisa</span>
                    <ChevronRight className="h-4 w-4" />
                  </button>
                ) : item.id === '01_data_kelas' ? (
                  <button
                    type="button"
                    onClick={() => onOpenClassroomModal?.()}
                    className="clay-btn-success flex w-full items-center justify-between px-4 py-2.5 text-xs font-bold"
                  >
                    <span>Kelola Data Kelas</span>
                    <ChevronRight className="h-4 w-4" />
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => onSelectService(item.id as ServiceId)}
                    className="clay-btn-primary flex w-full items-center justify-between px-4 py-2.5 text-xs font-bold"
                  >
                    <span>Pilih &amp; Buka Form</span>
                    <ChevronRight className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Roadmap 13 Additional Services Modal */}
      {showRoadmapModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm">
          <div className="clay-card relative max-h-[85vh] w-full max-w-2xl overflow-y-auto p-6">
            <button
              type="button"
              onClick={() => setShowRoadmapModal(false)}
              className="clay-btn-white absolute right-5 top-5 flex h-8 w-8 items-center justify-center rounded-lg"
            >
              <X className="h-4 w-4 text-slate-600" />
            </button>

            <div>
              <h3 className="text-lg font-extrabold text-slate-900">
                Daftar 2 Layanan Tambahan (Menuju 18 Service Lengkap)
              </h3>
              <p className="mt-1 text-xs font-medium text-slate-500">
                Melengkapi 16 layanan aktif saat ini menjadi total 18 layanan administrasi guru sesuai spesifikasi.
              </p>
            </div>

            <div className="mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
              {UPCOMING_SERVICES.map((srv) => (
                <div
                  key={srv.code}
                  className="clay-subcard flex items-center justify-between px-3.5 py-2.5"
                >
                  <div className="pr-2">
                    <span className="text-[10px] font-bold uppercase text-blue-700">
                      Layanan {srv.code}
                    </span>
                    <p className="text-xs font-bold text-slate-800">{srv.name}</p>
                  </div>
                  <span className="shrink-0 rounded border border-slate-200 bg-white px-2 py-0.5 text-[10px] font-bold text-slate-600">
                    {srv.format}
                  </span>
                </div>
              ))}
            </div>

            <div className="mt-5 flex justify-end">
              <button
                type="button"
                onClick={() => setShowRoadmapModal(false)}
                className="clay-btn-primary px-5 py-2 text-xs font-bold"
              >
                Tutup
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
