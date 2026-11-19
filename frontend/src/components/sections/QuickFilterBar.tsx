import React from 'react';
import { Search } from 'lucide-react';
import { Jenjang } from '../../types';
import { GRADES_BY_JENJANG } from '../../constants/services';

interface QuickFilterBarProps {
  selectedJenjang: Jenjang | 'ALL';
  selectedKelas: number | 'ALL';
  searchQuery: string;
  onChangeJenjang: (val: Jenjang | 'ALL') => void;
  onChangeKelas: (val: number | 'ALL') => void;
  onChangeSearch: (val: string) => void;
  onTriggerSearch: () => void;
}

export const QuickFilterBar: React.FC<QuickFilterBarProps> = ({
  selectedJenjang,
  selectedKelas,
  searchQuery,
  onChangeJenjang,
  onChangeKelas,
  onChangeSearch,
  onTriggerSearch,
}) => {
  const availableGrades =
    selectedJenjang === 'ALL'
      ? [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
      : GRADES_BY_JENJANG[selectedJenjang];

  return (
    <div className="mx-auto max-w-7xl px-4 pt-6 sm:px-6 lg:px-8">
      <div className="clay-card p-4 sm:p-5">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-12">
          {/* Jenjang Selector */}
          <div className="md:col-span-4">
            <label className="mb-1 block text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Jenjang Pendidikan
            </label>
            <select
              aria-label="Filter Jenjang Pendidikan"
              value={selectedJenjang}
              onChange={(e) => {
                const next = e.target.value as Jenjang | 'ALL';
                onChangeJenjang(next);
                onChangeKelas('ALL');
              }}
              className="clay-input w-full px-3.5 py-2.5 text-sm font-semibold text-slate-800"
            >
              <option value="ALL">Semua Jenjang (SD / SMP / SMA)</option>
              <option value="SD">SD / MI (Kelas 1–6 • Fase A–C)</option>
              <option value="SMP">SMP / MTs (Kelas 7–9 • Fase D)</option>
              <option value="SMA">SMA / MA (Kelas 10–12 • Fase E–F)</option>
            </select>
          </div>

          {/* Kelas Selector */}
          <div className="md:col-span-3">
            <label className="mb-1 block text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Tingkat Kelas
            </label>
            <select
              aria-label="Filter Tingkat Kelas"
              value={selectedKelas}
              onChange={(e) =>
                onChangeKelas(e.target.value === 'ALL' ? 'ALL' : Number(e.target.value))
              }
              className="clay-input w-full px-3.5 py-2.5 text-sm font-semibold text-slate-800"
            >
              <option value="ALL">Semua Kelas (1–12)</option>
              {availableGrades.map((g) => (
                <option key={g} value={g}>
                  Kelas {g}
                </option>
              ))}
            </select>
          </div>

          {/* Search Input + Button */}
          <div className="md:col-span-5">
            <label className="mb-1 block text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Pencarian Layanan Dokumen
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => onChangeSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && onTriggerSearch()}
                placeholder="Ketik nama layanan (mis. Modul Ajar, ATP)..."
                className="clay-input flex-1 px-3.5 py-2.5 text-sm font-medium text-slate-800 placeholder:text-slate-400"
              />
              <button
                type="button"
                onClick={onTriggerSearch}
                className="clay-btn-primary flex shrink-0 items-center gap-1.5 px-4 py-2.5 text-sm font-bold"
              >
                <Search className="h-4 w-4" />
                <span>Filter</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
