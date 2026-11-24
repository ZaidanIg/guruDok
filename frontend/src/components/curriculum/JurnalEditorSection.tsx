import React, { useState } from 'react';
import {
  ArrowDown,
  ArrowUp,
  Calendar,
  ChevronDown,
  ChevronUp,
  Copy,
  Edit3,
  Plus,
  RotateCcw,
  Trash2,
} from 'lucide-react';
import {
  ChapterTopic,
  CustomDocumentOverrides,
  CustomJurnalRowItem,
} from '../../types';

const DAY_NAME_MAP: Record<string, number> = {
  Minggu: 0,
  Senin: 1,
  Selasa: 2,
  Rabu: 3,
  Kamis: 4,
  Jumat: 5,
  Sabtu: 6,
};

const DAY_NAMES_ID = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];
const MONTH_NAMES_ID = [
  'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
];

export const buildDefaultJurnalRows = ({
  kelas,
  semester,
  subjectName,
  semesterChapters,
  hariMengajar,
  tanggalMulaiSemester,
  jamMengajar,
  jumlahPertemuan,
}: {
  kelas: number;
  semester: number;
  subjectName?: string;
  semesterChapters: ChapterTopic[];
  hariMengajar?: string[];
  tanggalMulaiSemester?: string;
  jamMengajar?: string;
  jumlahPertemuan?: number;
}): CustomJurnalRowItem[] => {
  const activeDays = hariMengajar && hariMengajar.length > 0 ? hariMengajar : ['Senin', 'Kamis'];
  const targetWeekdays = new Set(activeDays.map((d) => DAY_NAME_MAP[d]).filter((n) => n !== undefined));
  if (targetWeekdays.size === 0) {
    targetWeekdays.add(1);
    targetWeekdays.add(4);
  }

  const startIso = tanggalMulaiSemester || (semester === 1 ? '2026-07-13' : '2027-01-04');
  const parsedStart = new Date(`${startIso}T00:00:00`);
  const startDate = Number.isNaN(parsedStart.getTime())
    ? new Date(semester === 1 ? '2026-07-13T00:00:00' : '2027-01-04T00:00:00')
    : parsedStart;

  const totalPertemuan = Math.max(4, Math.min(48, jumlahPertemuan ?? 16));
  const jamStr = jamMengajar || '1-2';

  const tpEntries = semesterChapters.flatMap((bab) =>
    (bab.tujuan_pembelajaran || []).map((tp) => ({
      tpText: `${tp.code}: ${tp.deskripsi}`,
      materi: `Bab ${bab.nomor_bab}: ${bab.judul_bab}`,
    }))
  );
  const effectiveTpEntries =
    tpEntries.length > 0
      ? tpEntries
      : [
          {
            tpText: `TP.${kelas}.1.1: Memahami konsep inti ${subjectName || 'Pembelajaran'}`,
            materi: subjectName || 'Materi Pokok',
          },
        ];

  const scheduledRows: CustomJurnalRowItem[] = [];
  const cursor = new Date(startDate.getTime());
  let guard = 0;
  while (scheduledRows.length < totalPertemuan && guard < 240) {
    if (targetWeekdays.has(cursor.getDay())) {
      const idx = scheduledRows.length;
      const item = effectiveTpEntries[idx % effectiveTpEntries.length];
      const tglStr = `${DAY_NAMES_ID[cursor.getDay()]}, ${String(cursor.getDate()).padStart(2, '0')} ${MONTH_NAMES_ID[cursor.getMonth()]} ${cursor.getFullYear()}`;
      scheduledRows.push({
        no: idx + 1,
        hari_tanggal: tglStr,
        jam_pertemuan: `Jam ${jamStr} (Pert. ${idx + 1})`,
        tp: item.tpText,
        materi: item.materi,
        kegiatan: 'Memahami konsep, diskusi eksploratif, aplikasi studi kasus, dan refleksi.',
        kehadiran: 'Hadir lengkap / .... siswa tidak hadir',
        refleksi: 'Pembelajaran berjalan kondusif sesuai target TP.',
        paraf: '',
      });
    }
    cursor.setDate(cursor.getDate() + 1);
    guard++;
  }
  return scheduledRows;
};

interface JurnalEditorSectionProps {
  kelas: number;
  semester: number;
  subjectName?: string;
  defaultRombel?: string;
  semesterChapters: ChapterTopic[];
  customOverrides: CustomDocumentOverrides;
  onChangeCustomOverrides: (next: CustomDocumentOverrides) => void;
}

export const JurnalEditorSection: React.FC<JurnalEditorSectionProps> = ({
  kelas,
  semester,
  subjectName,
  defaultRombel,
  semesterChapters,
  customOverrides,
  onChangeCustomOverrides,
}) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const generatedRows = buildDefaultJurnalRows({
    kelas,
    semester,
    subjectName,
    semesterChapters,
    hariMengajar: customOverrides.hari_mengajar,
    tanggalMulaiSemester: customOverrides.tanggal_mulai_semester,
    jamMengajar: customOverrides.jam_mengajar,
    jumlahPertemuan: customOverrides.jumlah_pertemuan_jurnal,
  });

  const isCustomMode = Array.isArray(customOverrides.custom_jurnal_rows) && customOverrides.custom_jurnal_rows.length > 0;
  const activeRows = isCustomMode ? customOverrides.custom_jurnal_rows! : generatedRows;

  const tpOptions = semesterChapters.flatMap((bab) =>
    (bab.tujuan_pembelajaran || []).map((tp) => ({
      label: `${tp.code} — ${tp.deskripsi}`,
      tpValue: `${tp.code}: ${tp.deskripsi}`,
      materiValue: `Bab ${bab.nomor_bab}: ${bab.judul_bab}`,
    }))
  );

  const commitRows = (nextRows: CustomJurnalRowItem[]) => {
    const normalized = nextRows.map((row, idx) => ({
      ...row,
      no: idx + 1,
    }));
    onChangeCustomOverrides({
      ...customOverrides,
      custom_jurnal_rows: normalized,
      jumlah_pertemuan_jurnal: Math.max(4, Math.min(48, normalized.length)),
    });
  };

  const handleUpdateRow = (index: number, patch: Partial<CustomJurnalRowItem>) => {
    const next = activeRows.map((row, i) => (i === index ? { ...row, ...patch } : row));
    commitRows(next);
  };

  const handleAddRow = () => {
    const nextNo = activeRows.length + 1;
    const defaultTp = tpOptions[0]?.tpValue || `TP.${kelas}.1.1: Memahami konsep inti ${subjectName || 'Pembelajaran'}`;
    const defaultMateri = tpOptions[0]?.materiValue || subjectName || 'Materi Pokok';
    const newRow: CustomJurnalRowItem = {
      no: nextNo,
      hari_tanggal: `Pertemuan Ke-${nextNo}`,
      jam_pertemuan: `Jam ${customOverrides.jam_mengajar || '1-2'} (Pert. ${nextNo})`,
      tp: defaultTp,
      materi: defaultMateri,
      kegiatan: 'Memahami konsep, diskusi eksploratif, aplikasi studi kasus, dan refleksi.',
      kehadiran: 'Hadir lengkap',
      refleksi: 'Pembelajaran berjalan kondusif.',
      paraf: '',
    };
    const next = [...activeRows, newRow];
    commitRows(next);
    setExpandedIndex(next.length - 1);
  };

  const handleDuplicateRow = (index: number) => {
    const target = activeRows[index];
    if (!target) return;
    const copy: CustomJurnalRowItem = { ...target };
    const next = [
      ...activeRows.slice(0, index + 1),
      copy,
      ...activeRows.slice(index + 1),
    ];
    commitRows(next);
    setExpandedIndex(index + 1);
  };

  const handleMoveRow = (index: number, dir: -1 | 1) => {
    const targetIdx = index + dir;
    if (targetIdx < 0 || targetIdx >= activeRows.length) return;
    const next = [...activeRows];
    const [moved] = next.splice(index, 1);
    next.splice(targetIdx, 0, moved);
    commitRows(next);
    if (expandedIndex === index) {
      setExpandedIndex(targetIdx);
    } else if (expandedIndex === targetIdx) {
      setExpandedIndex(index);
    }
  };

  const handleDeleteRow = (index: number) => {
    if (activeRows.length <= 1) return;
    const next = activeRows.filter((_, i) => i !== index);
    commitRows(next);
    if (expandedIndex === index) {
      setExpandedIndex(null);
    } else if (expandedIndex !== null && expandedIndex > index) {
      setExpandedIndex(expandedIndex - 1);
    }
  };

  const handleResetToAutoSchedule = () => {
    setExpandedIndex(null);
    onChangeCustomOverrides({
      ...customOverrides,
      custom_jurnal_rows: undefined,
    });
  };

  return (
    <div className="clay-card p-5 space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-blue-600" />
          <h3 className="text-sm font-bold text-slate-800">
            Jadwal &amp; CRUD Jurnal Mengajar
          </h3>
        </div>
        <span
          className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${
            isCustomMode
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
              : 'bg-blue-50 text-blue-700 border-blue-200'
          }`}
        >
          {isCustomMode ? `Edit Manual (${activeRows.length} Pertemuan)` : 'Otomatis Jadwal & TP'}
        </span>
      </div>

      {/* Parameter Jadwal Dasar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1.5">
            Rombel / Kelas Sasaran
          </label>
          <input
            type="text"
            value={customOverrides.nama_rombel ?? defaultRombel ?? `Kelas ${kelas}`}
            onChange={(e) =>
              onChangeCustomOverrides({
                ...customOverrides,
                nama_rombel: e.target.value,
              })
            }
            placeholder={`Contoh: ${kelas}A / VII-A`}
            className="clay-input w-full px-3.5 py-2.5 text-sm font-medium text-slate-800"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1.5">
            Tanggal Mulai Semester
          </label>
          <input
            type="date"
            value={
              customOverrides.tanggal_mulai_semester ||
              (semester === 1 ? '2026-07-13' : '2027-01-04')
            }
            onChange={(e) =>
              onChangeCustomOverrides({
                ...customOverrides,
                tanggal_mulai_semester: e.target.value,
              })
            }
            className="clay-input w-full px-3.5 py-2.5 text-sm font-medium text-slate-800"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-bold text-slate-700 mb-1.5">
          Hari Mengajar dalam Seminggu
        </label>
        <div className="flex flex-wrap gap-2">
          {(['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'] as const).map((hari) => {
            const currentDays = customOverrides.hari_mengajar || ['Senin', 'Kamis'];
            const isSelected = currentDays.includes(hari);
            return (
              <button
                key={hari}
                type="button"
                onClick={() => {
                  const nextDays = isSelected
                    ? currentDays.length > 1
                      ? currentDays.filter((d) => d !== hari)
                      : currentDays
                    : [...currentDays, hari];
                  onChangeCustomOverrides({
                    ...customOverrides,
                    hari_mengajar: nextDays,
                  });
                }}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${
                  isSelected
                    ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                {hari}
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1.5">
            Jam Mengajar (Jam Ke-)
          </label>
          <input
            type="text"
            value={customOverrides.jam_mengajar ?? '1-2'}
            onChange={(e) =>
              onChangeCustomOverrides({
                ...customOverrides,
                jam_mengajar: e.target.value,
              })
            }
            placeholder="Contoh: 1-2 atau 3-4"
            className="clay-input w-full px-3.5 py-2.5 text-sm font-medium text-slate-800"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1.5">
            Target Pertemuan Otomatis (4–48)
          </label>
          <input
            type="number"
            min={4}
            max={48}
            value={customOverrides.jumlah_pertemuan_jurnal ?? 16}
            onChange={(e) => {
              const val = parseInt(e.target.value, 10);
              onChangeCustomOverrides({
                ...customOverrides,
                jumlah_pertemuan_jurnal: Number.isNaN(val) ? 16 : Math.max(4, Math.min(48, val)),
              });
            }}
            className="clay-input w-full px-3.5 py-2.5 text-sm font-medium text-slate-800"
          />
        </div>
      </div>

      {/* Toolbar CRUD Daftar Pertemuan */}
      <div className="border-t border-slate-200 pt-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-800">
              Daftar Baris Pertemuan Jurnal ({activeRows.length})
            </h4>
            <p className="text-[11px] text-slate-500">
              Tambah, edit isi tiap kolom, urutkan, duplikat, atau hapus baris agenda secara langsung.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {isCustomMode && (
              <button
                type="button"
                onClick={handleResetToAutoSchedule}
                className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border border-slate-200 bg-white text-[11px] font-bold text-slate-700 hover:bg-slate-50"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Reset Jadwal</span>
              </button>
            )}
            <button
              type="button"
              onClick={handleAddRow}
              disabled={activeRows.length >= 60}
              className="clay-btn-primary inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold disabled:opacity-50"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Tambah Pertemuan</span>
            </button>
          </div>
        </div>

        {/* List Pertemuan */}
        <div className="space-y-2 max-h-[540px] overflow-y-auto pr-1">
          {activeRows.map((row, idx) => {
            const isExpanded = expandedIndex === idx;
            return (
              <div
                key={`jurnal-row-${idx}`}
                className={`rounded-xl border transition-all ${
                  isExpanded
                    ? 'border-blue-300 bg-blue-50/40 shadow-sm'
                    : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
              >
                {/* Header Item */}
                <div className="flex items-center justify-between gap-2 px-3 py-2.5">
                  <button
                    type="button"
                    onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                    className="flex min-w-0 flex-1 items-center gap-2.5 text-left"
                  >
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-[11px] font-extrabold text-blue-700">
                      {idx + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="text-xs font-bold text-slate-800 truncate">
                          {row.hari_tanggal || '(Tanggal kosong)'}
                        </span>
                        <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600">
                          {row.jam_pertemuan}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 truncate">
                        {row.materi} — {row.tp}
                      </p>
                    </div>
                  </button>

                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      type="button"
                      disabled={idx === 0}
                      onClick={() => handleMoveRow(idx, -1)}
                      title="Geser Naik"
                      className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      <ArrowUp className="h-3 w-3" />
                    </button>
                    <button
                      type="button"
                      disabled={idx === activeRows.length - 1}
                      onClick={() => handleMoveRow(idx, 1)}
                      title="Geser Turun"
                      className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      <ArrowDown className="h-3 w-3" />
                    </button>
                    <button
                      type="button"
                      disabled={activeRows.length >= 60}
                      onClick={() => handleDuplicateRow(idx)}
                      title="Duplikat Baris"
                      className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-100 disabled:opacity-30"
                    >
                      <Copy className="h-3 w-3" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                      title={isExpanded ? 'Tutup Editor' : 'Edit Baris'}
                      className="inline-flex items-center gap-1 px-2 py-1.5 rounded-lg border border-blue-200 bg-blue-50 text-[11px] font-bold text-blue-700 hover:bg-blue-100"
                    >
                      <Edit3 className="h-3 w-3" />
                      {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                    </button>
                    <button
                      type="button"
                      disabled={activeRows.length <= 1}
                      onClick={() => handleDeleteRow(idx)}
                      title={activeRows.length <= 1 ? 'Minimal 1 baris pertemuan' : 'Hapus Baris'}
                      className="p-1.5 rounded-lg border border-rose-200 bg-rose-50 text-rose-600 hover:bg-rose-100 disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                </div>

                {/* Expanded Form Fields */}
                {isExpanded && (
                  <div className="border-t border-blue-200/80 px-3.5 py-3 space-y-3 bg-white/80 rounded-b-xl">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 mb-1">
                          Hari / Tanggal
                        </label>
                        <input
                          type="text"
                          value={row.hari_tanggal}
                          onChange={(e) => handleUpdateRow(idx, { hari_tanggal: e.target.value })}
                          placeholder="Senin, 13 Juli 2026"
                          className="clay-input w-full px-3 py-2 text-xs text-slate-800"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 mb-1">
                          Jam Ke- / Pertemuan
                        </label>
                        <input
                          type="text"
                          value={row.jam_pertemuan}
                          onChange={(e) => handleUpdateRow(idx, { jam_pertemuan: e.target.value })}
                          placeholder="Jam 1-2 (Pert. 1)"
                          className="clay-input w-full px-3 py-2 text-xs text-slate-800"
                        />
                      </div>
                    </div>

                    {tpOptions.length > 0 && (
                      <div>
                        <label className="block text-[11px] font-bold text-slate-700 mb-1">
                          Pilih Cepat TP &amp; Materi dari Kurikulum
                        </label>
                        <select
                          value=""
                          onChange={(e) => {
                            const found = tpOptions.find((opt) => opt.tpValue === e.target.value);
                            if (found) {
                              handleUpdateRow(idx, {
                                tp: found.tpValue,
                                materi: found.materiValue,
                              });
                            }
                          }}
                          className="clay-input w-full px-3 py-2 text-xs text-slate-700"
                        >
                          <option value="">— Pilih TP untuk mengisi TP &amp; Materi otomatis —</option>
                          {tpOptions.map((opt, optIdx) => (
                            <option key={`tp-opt-${optIdx}`} value={opt.tpValue}>
                              {opt.label.slice(0, 95)}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 mb-1">
                        Tujuan Pembelajaran (TP)
                      </label>
                      <textarea
                        rows={2}
                        value={row.tp}
                        onChange={(e) => handleUpdateRow(idx, { tp: e.target.value })}
                        className="clay-input w-full px-3 py-2 text-xs text-slate-800"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 mb-1">
                        Materi Pembelajaran
                      </label>
                      <input
                        type="text"
                        value={row.materi}
                        onChange={(e) => handleUpdateRow(idx, { materi: e.target.value })}
                        className="clay-input w-full px-3 py-2 text-xs text-slate-800"
                      />
                    </div>

                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 mb-1">
                        Ringkasan Kegiatan
                      </label>
                      <textarea
                        rows={2}
                        value={row.kegiatan}
                        onChange={(e) => handleUpdateRow(idx, { kegiatan: e.target.value })}
                        className="clay-input w-full px-3 py-2 text-xs text-slate-800"
                      />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                      <div className="sm:col-span-1">
                        <label className="block text-[11px] font-bold text-slate-700 mb-1">
                          Kehadiran Siswa
                        </label>
                        <input
                          type="text"
                          value={row.kehadiran}
                          onChange={(e) => handleUpdateRow(idx, { kehadiran: e.target.value })}
                          className="clay-input w-full px-3 py-2 text-xs text-slate-800"
                        />
                      </div>
                      <div className="sm:col-span-1">
                        <label className="block text-[11px] font-bold text-slate-700 mb-1">
                          Hambatan &amp; Refleksi
                        </label>
                        <input
                          type="text"
                          value={row.refleksi}
                          onChange={(e) => handleUpdateRow(idx, { refleksi: e.target.value })}
                          className="clay-input w-full px-3 py-2 text-xs text-slate-800"
                        />
                      </div>
                      <div className="sm:col-span-1">
                        <label className="block text-[11px] font-bold text-slate-700 mb-1">
                          Paraf
                        </label>
                        <input
                          type="text"
                          value={row.paraf}
                          onChange={(e) => handleUpdateRow(idx, { paraf: e.target.value })}
                          placeholder="Opsional"
                          className="clay-input w-full px-3 py-2 text-xs text-slate-800"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
