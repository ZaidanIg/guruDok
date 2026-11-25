import React, { useState } from 'react';
import { Plus, Trash2, Users } from 'lucide-react';
import { CustomDocumentOverrides, StudentOverrideItem } from '../../types';

const PIKET_DAYS = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat'] as const;

const DENAH_FORMATIONS = [
  'Kelompok Kolaboratif',
  'Tradisional Berbaris',
  'U-Shape',
] as const;

export const DEFAULT_KESEPAKATAN_KELAS: string[] = [
  'Hadir tepat waktu dan siap mengikuti pembelajaran sebelum bel masuk berbunyi.',
  'Saling menghormati guru dan sesama teman dengan bertutur kata santun.',
  'Menjaga kebersihan, kerapian, dan ketertiban ruang kelas serta melaksanakan tugas piket.',
  'Berpartisipasi aktif dalam diskusi, kerja kelompok, dan menyelesaikan tugas dengan jujur.',
  'Menggunakan gawai dan fasilitas kelas secara bijak hanya untuk mendukung kegiatan belajar.',
];

export interface AdminKelasEditorSectionProps {
  kelas: number;
  defaultRombel?: string;
  effectiveStudents: StudentOverrideItem[];
  customOverrides: CustomDocumentOverrides;
  onChangeCustomOverrides: (next: CustomDocumentOverrides) => void;
}

export const AdminKelasEditorSection: React.FC<AdminKelasEditorSectionProps> = ({
  kelas,
  defaultRombel,
  effectiveStudents,
  customOverrides,
  onChangeCustomOverrides,
}) => {
  const [newRuleInput, setNewRuleInput] = useState('');

  const studentNames = effectiveStudents.map((s) => s.nama_lengkap);
  const effectiveRules =
    customOverrides.kesepakatan_kelas && customOverrides.kesepakatan_kelas.length > 0
      ? customOverrides.kesepakatan_kelas
      : DEFAULT_KESEPAKATAN_KELAS;

  const activeRombelLabel = customOverrides.nama_rombel || defaultRombel || `Kelas ${kelas}`;

  const handleRuleChange = (idx: number, value: string) => {
    const nextRules = [...effectiveRules];
    nextRules[idx] = value;
    onChangeCustomOverrides({
      ...customOverrides,
      kesepakatan_kelas: nextRules,
    });
  };

  const handleAddRule = () => {
    const trimmed = newRuleInput.trim();
    if (!trimmed) return;
    onChangeCustomOverrides({
      ...customOverrides,
      kesepakatan_kelas: [...effectiveRules, trimmed],
    });
    setNewRuleInput('');
  };

  const handleRemoveRule = (idx: number) => {
    const nextRules = effectiveRules.filter((_, i) => i !== idx);
    onChangeCustomOverrides({
      ...customOverrides,
      kesepakatan_kelas: nextRules,
    });
  };

  const handlePiketDayChange = (day: string, value: string) => {
    const names = value
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
    onChangeCustomOverrides({
      ...customOverrides,
      jadwal_piket: {
        ...(customOverrides.jadwal_piket || {}),
        [day]: names,
      },
    });
  };

  const getDefaultPiketForDay = (dayIdx: number, day: string): string => {
    const customDay = customOverrides.jadwal_piket?.[day];
    if (customDay && customDay.length > 0) return customDay.join(', ');
    if (studentNames.length === 0) return '';
    return studentNames
      .filter((_, idx) => idx % PIKET_DAYS.length === dayIdx)
      .slice(0, 4)
      .join(', ');
  };

  return (
    <div className="clay-card p-5 space-y-4">
      <div className="border-b border-slate-200 pb-3">
        <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800 flex items-center gap-2">
          <Users className="h-4 w-4 text-blue-600" />
          <span>3. Pengaturan Administrasi Kelas ({activeRombelLabel})</span>
        </h2>
        <p className="text-[11px] font-medium text-slate-500">
          Atur struktur pengurus kelas, formasi denah duduk, jadwal piket Senin–Jumat, &amp; kesepakatan kelas.
        </p>
      </div>

      {/* Struktur Pengurus Kelas */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {(
          [
            { key: 'ketua_kelas', label: 'Ketua Kelas', fallback: studentNames[0] || '' },
            { key: 'wakil_ketua_kelas', label: 'Wakil Ketua Kelas', fallback: studentNames[1] || '' },
            { key: 'sekretaris_kelas', label: 'Sekretaris Kelas', fallback: studentNames[2] || '' },
            { key: 'bendahara_kelas', label: 'Bendahara Kelas', fallback: studentNames[3] || '' },
          ] as const
        ).map((role) => (
          <div key={role.key}>
            <label className="mb-1 block text-xs font-bold text-slate-700">{role.label}</label>
            <input
              type="text"
              value={customOverrides[role.key] ?? role.fallback}
              placeholder={`Nama ${role.label}...`}
              onChange={(e) =>
                onChangeCustomOverrides({
                  ...customOverrides,
                  [role.key]: e.target.value,
                })
              }
              className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
            />
          </div>
        ))}
      </div>

      {/* Formasi Denah Duduk */}
      <div>
        <label className="mb-1.5 block text-xs font-bold text-slate-700">
          Formasi Denah Duduk Siswa
        </label>
        <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-3">
          {DENAH_FORMATIONS.map((formation) => (
            <button
              key={formation}
              type="button"
              onClick={() =>
                onChangeCustomOverrides({
                  ...customOverrides,
                  denah_duduk: formation,
                })
              }
              className={`px-3 py-2 text-xs font-bold ${
                (customOverrides.denah_duduk || 'Kelompok Kolaboratif') === formation
                  ? 'clay-btn-primary'
                  : 'clay-btn-white'
              }`}
            >
              {formation}
            </button>
          ))}
        </div>
      </div>

      {/* Jadwal Piket Senin-Jumat */}
      <div className="space-y-2">
        <label className="block text-xs font-bold text-slate-700">
          Jadwal Piket Kebersihan (Pisahkan nama dengan koma)
        </label>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {PIKET_DAYS.map((day, dayIdx) => (
            <div key={day} className="clay-subcard p-2.5">
              <span className="mb-1 block text-[11px] font-extrabold uppercase text-blue-700">
                {day}
              </span>
              <input
                type="text"
                value={getDefaultPiketForDay(dayIdx, day)}
                placeholder={`Petugas hari ${day}...`}
                onChange={(e) => handlePiketDayChange(day, e.target.value)}
                className="clay-input w-full px-2.5 py-1.5 text-xs font-medium text-slate-800"
              />
            </div>
          ))}
        </div>
      </div>

      {/* Kesepakatan Kelas */}
      <div className="space-y-2">
        <label className="block text-xs font-bold text-slate-700">
          Butir Kesepakatan Kelas ({effectiveRules.length} Poin)
        </label>
        <div className="space-y-1.5">
          {effectiveRules.map((ruleText, idx) => (
            <div key={`rule-${idx}`} className="flex items-center gap-2">
              <span className="text-xs font-extrabold text-slate-500 w-5 text-right">{idx + 1}.</span>
              <input
                type="text"
                value={ruleText}
                onChange={(e) => handleRuleChange(idx, e.target.value)}
                className="clay-input flex-1 px-2.5 py-1.5 text-xs font-medium text-slate-800"
              />
              {effectiveRules.length > 1 && (
                <button
                  type="button"
                  onClick={() => handleRemoveRule(idx)}
                  aria-label="Hapus kesepakatan"
                  className="clay-btn-white p-1.5 text-rose-600 hover:bg-rose-50"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2 pt-1">
          <input
            type="text"
            value={newRuleInput}
            placeholder="Tambah poin kesepakatan kelas baru..."
            onChange={(e) => setNewRuleInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddRule();
              }
            }}
            className="clay-input flex-1 px-3 py-1.5 text-xs font-medium text-slate-800"
          />
          <button
            type="button"
            onClick={handleAddRule}
            className="clay-btn-primary flex items-center gap-1 px-3 py-1.5 text-xs font-bold"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Tambah</span>
          </button>
        </div>
      </div>
    </div>
  );
};
