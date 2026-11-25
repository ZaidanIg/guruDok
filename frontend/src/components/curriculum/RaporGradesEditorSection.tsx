import React, { useState } from 'react';
import { Award, ChevronDown, ChevronUp, Edit3, RotateCcw } from 'lucide-react';
import {
  ChapterTopic,
  CustomDocumentOverrides,
  CustomRaporEntryItem,
  StudentOverrideItem,
} from '../../types';

export interface RaporComputedRow {
  no: number;
  nisn: string;
  nama: string;
  sumatif: number;
  sas: number;
  nilaiAkhir: number;
  peringkat: number;
  status: 'TUNTAS' | 'BELUM TUNTAS';
  predikat: string;
  tpMaxCode: string;
  tpMaxDesc: string;
  tpMinCode: string;
  tpMinDesc: string;
  deskripsiTinggi: string;
  deskripsiBimbingan: string;
}

const cleanPhrase = (raw: string): string => {
  const s = (raw || '').trim().replace(/\.+$/, '');
  if (!s) return 'memahami konsep inti pembelajaran';
  if (s.length > 1 && s[0] === s[0].toUpperCase() && s[1] === s[1].toLowerCase()) {
    return s[0].toLowerCase() + s.slice(1);
  }
  return s;
};

export const buildRaporPreviewData = ({
  kelas,
  subjectName,
  semesterChapters,
  students,
  customOverrides,
}: {
  kelas: number;
  subjectName?: string;
  semesterChapters: ChapterTopic[];
  students: StudentOverrideItem[];
  customOverrides: CustomDocumentOverrides;
}) => {
  const kktp = customOverrides.kktp_nilai ?? 75;
  const rawBobot = customOverrides.bobot_nilai || { sumatif: 60, sas: 40 };
  const rawSum = Number(rawBobot.sumatif ?? 60);
  const rawSas = Number(rawBobot.sas ?? 40);
  const sumSafe = Number.isFinite(rawSum) ? Math.max(0, Math.min(100, rawSum)) : 60;
  const sasSafe = Number.isFinite(rawSas) ? Math.max(0, Math.min(100, rawSas)) : 40;
  const totalW = sumSafe + sasSafe;
  const wSumatif = totalW <= 0 ? 60 : totalW === 100 ? sumSafe : Math.round((sumSafe / totalW) * 100);
  const wSas = totalW <= 0 ? 40 : 100 - wSumatif;

  const tpList = semesterChapters.flatMap((bab) =>
    (bab.tujuan_pembelajaran || []).map((tp) => ({
      code: tp.code,
      ringkasan: cleanPhrase(tp.ringkasan_rapor || tp.deskripsi),
    }))
  );
  const effectiveTpList =
    tpList.length > 0
      ? tpList
      : [
          { code: `${kelas}.1.1`, ringkasan: `memahami konsep utama ${subjectName || 'pembelajaran'}` },
          { code: `${kelas}.1.2`, ringkasan: `menerapkan ${subjectName || 'materi'} dalam studi kasus` },
        ];
  const tpByCode = new Map(effectiveTpList.map((t) => [t.code, t]));

  const hasCustomEntries = Array.isArray(customOverrides.rapor_entries) && customOverrides.rapor_entries.length > 0;
  const baseRows = hasCustomEntries
    ? customOverrides.rapor_entries!.map((entry, idx) => {
        const sScore = entry.nilai_sumatif ?? 82;
        const sasScore = entry.nilai_sas ?? 80;
        const tpHi = tpByCode.get(entry.tp_tertinggi_code || '') || effectiveTpList[0];
        const tpLo = tpByCode.get(entry.tp_terendah_code || '') || effectiveTpList[effectiveTpList.length - 1];
        const na = Math.round((sScore * wSumatif + sasScore * wSas) / 100);
        return {
          no: entry.nomor_absen || idx + 1,
          nisn: entry.nisn || '-',
          nama: entry.nama_lengkap,
          sumatif: sScore,
          sas: sasScore,
          nilaiAkhir: na,
          tpMaxCode: tpHi.code,
          tpMaxDesc: tpHi.ringkasan,
          tpMinCode: tpLo.code,
          tpMinDesc: tpLo.ringkasan,
        };
      })
    : (students.length > 0
        ? students
        : Array.from({ length: 10 }, (_, idx) => ({
            nomor_absen: idx + 1,
            nisn: `2026${String(idx + 1).padStart(4, '0')}`,
            nama_lengkap: `Peserta Didik ${idx + 1}`,
          }))
      ).map((st, idx) => {
        const sScore = idx % 3 === 2 ? 74 : 86;
        const sasScore = idx % 3 === 2 ? 72 : 84;
        const tpHi = effectiveTpList[idx % effectiveTpList.length];
        const tpLo = effectiveTpList[(idx + effectiveTpList.length - 1) % effectiveTpList.length];
        const na = Math.round((sScore * wSumatif + sasScore * wSas) / 100);
        return {
          no: st.nomor_absen || idx + 1,
          nisn: st.nisn || '-',
          nama: st.nama_lengkap,
          sumatif: sScore,
          sas: sasScore,
          nilaiAkhir: na,
          tpMaxCode: tpHi.code,
          tpMaxDesc: tpHi.ringkasan,
          tpMinCode: tpLo.code,
          tpMinDesc: tpLo.ringkasan,
        };
      });

  const sortedDesc = [...baseRows].map((r) => r.nilaiAkhir).sort((a, b) => b - a);
  const rows: RaporComputedRow[] = baseRows.map((r) => {
    const status: 'TUNTAS' | 'BELUM TUNTAS' = r.nilaiAkhir >= kktp ? 'TUNTAS' : 'BELUM TUNTAS';
    const predikat =
      r.nilaiAkhir >= 90
        ? 'A (Sangat Baik)'
        : r.nilaiAkhir >= 80
        ? 'B (Baik)'
        : r.nilaiAkhir >= kktp
        ? 'C (Cukup)'
        : 'D (Perlu Bimbingan)';
    return {
      ...r,
      peringkat: sortedDesc.indexOf(r.nilaiAkhir) + 1,
      status,
      predikat,
      deskripsiTinggi: `Menunjukkan penguasaan yang sangat baik dalam ${r.tpMaxDesc}.`,
      deskripsiBimbingan: `Perlu bimbingan dan pendampingan lebih lanjut dalam ${r.tpMinDesc}.`,
    };
  });

  return {
    kktp,
    wSumatif,
    wSas,
    tpOptions: effectiveTpList,
    rows,
  };
};

interface RaporGradesEditorSectionProps {
  serviceId: '16_deskripsi_rapor' | '17_rekap_rapor';
  kelas: number;
  subjectName?: string;
  semesterChapters: ChapterTopic[];
  effectiveStudents: StudentOverrideItem[];
  customOverrides: CustomDocumentOverrides;
  onChangeCustomOverrides: (next: CustomDocumentOverrides) => void;
}

export const RaporGradesEditorSection: React.FC<RaporGradesEditorSectionProps> = ({
  serviceId,
  kelas,
  subjectName,
  semesterChapters,
  effectiveStudents,
  customOverrides,
  onChangeCustomOverrides,
}) => {
  const [expandedRowIdx, setExpandedRowIdx] = useState<number | null>(null);
  const isRekapRapor = serviceId === '17_rekap_rapor';

  const { kktp, wSumatif, wSas, tpOptions, rows } = buildRaporPreviewData({
    kelas,
    subjectName,
    semesterChapters,
    students: effectiveStudents,
    customOverrides,
  });

  const isCustomMode =
    Array.isArray(customOverrides.rapor_entries) && customOverrides.rapor_entries.length > 0;

  const commitEntries = (nextEntries: CustomRaporEntryItem[]) => {
    onChangeCustomOverrides({
      ...customOverrides,
      rapor_entries: nextEntries,
    });
  };

  const materializeFromRows = (): CustomRaporEntryItem[] =>
    rows.map((r) => ({
      nomor_absen: r.no,
      nisn: r.nisn,
      nama_lengkap: r.nama,
      nilai_sumatif: r.sumatif,
      nilai_sas: r.sas,
      tp_tertinggi_code: r.tpMaxCode,
      tp_terendah_code: r.tpMinCode,
    }));

  const handleUpdateEntry = (idx: number, patch: Partial<CustomRaporEntryItem>) => {
    const base = isCustomMode ? [...customOverrides.rapor_entries!] : materializeFromRows();
    const updated = base.map((item, i) => (i === idx ? { ...item, ...patch } : item));
    commitEntries(updated);
  };

  const handleResetEntries = () => {
    setExpandedRowIdx(null);
    onChangeCustomOverrides({
      ...customOverrides,
      rapor_entries: undefined,
    });
  };

  return (
    <div className="clay-card p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
        <div className="flex items-center gap-2">
          <Award className="h-4 w-4 text-emerald-600" />
          <h3 className="text-sm font-extrabold uppercase tracking-wider text-slate-800">
            {isRekapRapor ? '3. Bobot & Nilai Rapor Siswa' : '3. Pengaturan TP & Deskripsi e-Rapor'}
          </h3>
        </div>
        {isCustomMode && (
          <button
            type="button"
            onClick={handleResetEntries}
            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-bold text-slate-600 hover:bg-slate-50"
          >
            <RotateCcw className="h-3 w-3" />
            <span>Reset Rombel</span>
          </button>
        )}
      </div>

      {/* KKTP & Bobot Nilai */}
      <div className={`grid grid-cols-1 gap-3 ${isRekapRapor ? 'sm:grid-cols-3' : 'sm:grid-cols-1'}`}>
        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">KKTP Minimum</label>
          <input
            type="number"
            min={1}
            max={100}
            value={kktp}
            onChange={(e) => {
              const v = parseInt(e.target.value, 10);
              onChangeCustomOverrides({
                ...customOverrides,
                kktp_nilai: Number.isNaN(v) ? 75 : Math.max(1, Math.min(100, v)),
              });
            }}
            className="clay-input w-full px-3 py-2 text-xs font-bold text-slate-800"
          />
        </div>

        {isRekapRapor && (
          <>
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Bobot Sumatif (%)</label>
              <input
                type="number"
                min={0}
                max={100}
                value={wSumatif}
                onChange={(e) => {
                  const v = Math.max(0, Math.min(100, parseInt(e.target.value, 10) || 0));
                  onChangeCustomOverrides({
                    ...customOverrides,
                    bobot_nilai: { sumatif: v, sas: 100 - v },
                  });
                }}
                className="clay-input w-full px-3 py-2 text-xs font-bold text-slate-800"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Bobot SAS (%)</label>
              <input
                type="number"
                min={0}
                max={100}
                value={wSas}
                onChange={(e) => {
                  const v = Math.max(0, Math.min(100, parseInt(e.target.value, 10) || 0));
                  onChangeCustomOverrides({
                    ...customOverrides,
                    bobot_nilai: { sumatif: 100 - v, sas: v },
                  });
                }}
                className="clay-input w-full px-3 py-2 text-xs font-bold text-slate-800"
              />
            </div>
          </>
        )}
      </div>

      {/* Daftar Nilai & TP Per Siswa */}
      <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
        {rows.map((row, idx) => {
          const isOpen = expandedRowIdx === idx;
          return (
            <div
              key={`${row.nisn}-${row.no}-${idx}`}
              className="rounded-xl border border-slate-200 bg-white overflow-hidden"
            >
              <div className="flex items-center justify-between gap-2 px-3 py-2">
                <button
                  type="button"
                  onClick={() => setExpandedRowIdx(isOpen ? null : idx)}
                  className="flex min-w-0 flex-1 items-center gap-2 text-left"
                >
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-emerald-100 text-[11px] font-bold text-emerald-800">
                    {row.no}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-bold text-slate-800 truncate">{row.nama}</p>
                    <p className="text-[10px] text-slate-500">
                      Nilai Rapor: <strong>{row.nilaiAkhir}</strong> •{' '}
                      <span className={row.status === 'TUNTAS' ? 'text-emerald-700 font-bold' : 'text-rose-600 font-bold'}>
                        {row.status}
                      </span>
                    </p>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setExpandedRowIdx(isOpen ? null : idx)}
                  className="inline-flex items-center gap-1 rounded-lg border border-blue-200 bg-blue-50 px-2 py-1 text-[11px] font-bold text-blue-700 hover:bg-blue-100"
                >
                  <Edit3 className="h-3 w-3" />
                  {isOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                </button>
              </div>

              {isOpen && (
                <div className="border-t border-slate-100 bg-slate-50/70 p-3 space-y-2.5">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 mb-1">Nilai Sumatif (0–100)</label>
                      <input
                        type="number"
                        min={0}
                        max={100}
                        value={row.sumatif}
                        onChange={(e) =>
                          handleUpdateEntry(idx, {
                            nilai_sumatif: Math.max(0, Math.min(100, parseInt(e.target.value, 10) || 0)),
                          })
                        }
                        className="clay-input w-full px-2.5 py-1.5 text-xs font-bold text-slate-800"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 mb-1">Nilai SAS (0–100)</label>
                      <input
                        type="number"
                        min={0}
                        max={100}
                        value={row.sas}
                        onChange={(e) =>
                          handleUpdateEntry(idx, {
                            nilai_sas: Math.max(0, Math.min(100, parseInt(e.target.value, 10) || 0)),
                          })
                        }
                        className="clay-input w-full px-2.5 py-1.5 text-xs font-bold text-slate-800"
                      />
                    </div>
                  </div>

                  {!isRekapRapor && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 mb-1">
                          TP Penguasaan Tertinggi
                        </label>
                        <select
                          value={row.tpMaxCode}
                          onChange={(e) => handleUpdateEntry(idx, { tp_tertinggi_code: e.target.value })}
                          className="clay-input w-full px-2.5 py-1.5 text-xs text-slate-800"
                        >
                          {tpOptions.map((tp) => (
                            <option key={`hi-${tp.code}`} value={tp.code}>
                              [{tp.code}] {tp.ringkasan.slice(0, 48)}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 mb-1">
                          TP Perlu Pendampingan
                        </label>
                        <select
                          value={row.tpMinCode}
                          onChange={(e) => handleUpdateEntry(idx, { tp_terendah_code: e.target.value })}
                          className="clay-input w-full px-2.5 py-1.5 text-xs text-slate-800"
                        >
                          {tpOptions.map((tp) => (
                            <option key={`lo-${tp.code}`} value={tp.code}>
                              [{tp.code}] {tp.ringkasan.slice(0, 48)}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
