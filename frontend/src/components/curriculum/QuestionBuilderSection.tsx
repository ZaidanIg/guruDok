import React, { useState } from 'react';
import {
  Plus,
  Trash2,
  ArrowUp,
  ArrowDown,
  Copy,
  ArrowRightLeft,
} from 'lucide-react';
import {
  CustomQuestionItem,
  Jenjang,
  LearningObjective,
  ServiceId,
} from '../../types';

export type IdentifiedQuestionItem = CustomQuestionItem & { id: string };

interface QuestionBuilderSectionProps {
  serviceId: ServiceId;
  jenjang: Jenjang;
  subjectId: string;
  chapterId?: string;
  availableTps: LearningObjective[];
  questions: CustomQuestionItem[];
  onChangeQuestions: (next: CustomQuestionItem[]) => void;
}

const OPTION_LETTERS = ['A', 'B', 'C', 'D', 'E'] as const;

export const createEmptyQuestion = (
  jenjang: Jenjang,
  tipe: 'PG' | 'URAIAN' = 'PG',
  defaultTpCode = ''
): IdentifiedQuestionItem => {
  const optCount = jenjang === 'SMA' ? 5 : 4;
  return {
    id: `q-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    tipe_soal: tipe,
    tp_code: defaultTpCode,
    level_kognitif: 'C1-C2',
    stimulus: '',
    pertanyaan: '',
    opsi: tipe === 'PG' ? Array.from({ length: optCount }, () => '') : [],
    kunci_jawaban: tipe === 'PG' ? 'A' : '',
    bobot_skor: undefined,
    pembahasan: '',
  };
};

export const QuestionBuilderSection: React.FC<QuestionBuilderSectionProps> = ({
  jenjang,
  availableTps,
  questions,
  onChangeQuestions,
}) => {
  const [openStimulusMap, setOpenStimulusMap] = useState<Record<string, boolean>>({});

  const defaultTpCode = availableTps[0]?.code || '';

  // Ensure each item has a definite string id
  const items: IdentifiedQuestionItem[] = (
    questions.length > 0 ? questions : [createEmptyQuestion(jenjang, 'PG', defaultTpCode)]
  ).map((q, idx) => ({
    ...q,
    id: q.id || `q-${idx}-${Date.now()}`,
  }));

  const pgItems: IdentifiedQuestionItem[] = items.filter((q) => q.tipe_soal === 'PG');
  const essaiItems: IdentifiedQuestionItem[] = items.filter((q) => q.tipe_soal !== 'PG');

  const updateById = (id: string, patch: Partial<CustomQuestionItem>) => {
    const next = items.map((q) => (q.id === id ? { ...q, ...patch } : q));
    onChangeQuestions(next);
  };

  const handleAddPgQuestion = () => {
    const newQ = createEmptyQuestion(jenjang, 'PG', defaultTpCode);
    onChangeQuestions([...pgItems, newQ, ...essaiItems]);
  };

  const handleAddEssaiQuestion = () => {
    const newQ = createEmptyQuestion(jenjang, 'URAIAN', defaultTpCode);
    onChangeQuestions([...pgItems, ...essaiItems, newQ]);
  };

  const handleMovePg = (pgIdx: number, dir: -1 | 1) => {
    const targetIdx = pgIdx + dir;
    if (targetIdx < 0 || targetIdx >= pgItems.length) return;
    const nextPg = [...pgItems];
    const [moved] = nextPg.splice(pgIdx, 1);
    nextPg.splice(targetIdx, 0, moved);
    onChangeQuestions([...nextPg, ...essaiItems]);
  };

  const handleMoveEssai = (esIdx: number, dir: -1 | 1) => {
    const targetIdx = esIdx + dir;
    if (targetIdx < 0 || targetIdx >= essaiItems.length) return;
    const nextEs = [...essaiItems];
    const [moved] = nextEs.splice(esIdx, 1);
    nextEs.splice(targetIdx, 0, moved);
    onChangeQuestions([...pgItems, ...nextEs]);
  };

  const handleSwitchToEssai = (id: string) => {
    const target = items.find((q) => q.id === id);
    if (!target) return;
    const transformed: IdentifiedQuestionItem = {
      ...target,
      tipe_soal: 'URAIAN',
      opsi: [],
      kunci_jawaban: target.pembahasan || '',
    };
    const nextPg = pgItems.filter((q) => q.id !== id);
    onChangeQuestions([...nextPg, ...essaiItems, transformed]);
  };

  const handleSwitchToPg = (id: string) => {
    const target = items.find((q) => q.id === id);
    if (!target) return;
    const optCount = jenjang === 'SMA' ? 5 : 4;
    const transformed: IdentifiedQuestionItem = {
      ...target,
      tipe_soal: 'PG',
      opsi: target.opsi && target.opsi.length >= 3 ? target.opsi : Array.from({ length: optCount }, () => ''),
      kunci_jawaban: 'A',
    };
    const nextEs = essaiItems.filter((q) => q.id !== id);
    onChangeQuestions([...pgItems, transformed, ...nextEs]);
  };

  const handleDuplicate = (id: string, isPg: boolean) => {
    const target = items.find((q) => q.id === id);
    if (!target) return;
    const clone: IdentifiedQuestionItem = {
      ...target,
      id: `q-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      opsi: [...target.opsi],
    };
    if (isPg) {
      const idx = pgItems.findIndex((q) => q.id === id);
      const nextPg = [...pgItems];
      nextPg.splice(idx + 1, 0, clone);
      onChangeQuestions([...nextPg, ...essaiItems]);
    } else {
      const idx = essaiItems.findIndex((q) => q.id === id);
      const nextEs = [...essaiItems];
      nextEs.splice(idx + 1, 0, clone);
      onChangeQuestions([...pgItems, ...nextEs]);
    }
  };

  const handleRemove = (id: string) => {
    const remaining = items.filter((q) => q.id !== id);
    if (remaining.length === 0) {
      onChangeQuestions([createEmptyQuestion(jenjang, 'PG', defaultTpCode)]);
      return;
    }
    onChangeQuestions(remaining);
  };

  const handleAddOption = (id: string) => {
    const q = items.find((item) => item.id === id);
    if (!q || q.opsi.length >= 5) return;
    updateById(id, { opsi: [...q.opsi, ''] });
  };

  const handleRemoveOption = (id: string, optIdx: number) => {
    const q = items.find((item) => item.id === id);
    if (!q || q.opsi.length <= 3) return;
    const nextOpsi = q.opsi.filter((_, i) => i !== optIdx);
    const currentKeyIdx = OPTION_LETTERS.indexOf((q.kunci_jawaban || 'A') as any);
    const nextKey = currentKeyIdx >= nextOpsi.length ? 'A' : (q.kunci_jawaban || 'A');
    updateById(id, { opsi: nextOpsi, kunci_jawaban: nextKey });
  };

  const renderQuestionCard = (q: IdentifiedQuestionItem, sectionIdx: number, isPg: boolean) => {
    const showStimulus = Boolean(openStimulusMap[q.id] || (q.stimulus && q.stimulus.length > 0));

    return (
      <div key={q.id} className="clay-subcard space-y-3 p-4">
        {/* Header Bar Kartu Soal */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`clay-badge px-2.5 py-1 text-[11px] font-extrabold ${isPg ? 'text-blue-800' : 'text-emerald-800'}`}>
              {isPg ? `PG #${sectionIdx + 1}` : `Essai #${sectionIdx + 1}`}
            </span>
            <button
              type="button"
              onClick={() => (isPg ? handleSwitchToEssai(q.id) : handleSwitchToPg(q.id))}
              title={isPg ? 'Ubah menjadi Soal Essai (Pindah ke Bagian B)' : 'Ubah menjadi Soal PG (Pindah ke Bagian A)'}
              className="clay-btn-white inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-bold text-slate-600 hover:text-blue-700"
            >
              <ArrowRightLeft className="h-3 w-3" />
              <span>{isPg ? 'Pindah ke Essai' : 'Pindah ke PG'}</span>
            </button>
          </div>

          {/* Aksi Kartu: Urutan, Duplikat, Hapus */}
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => (isPg ? handleMovePg(sectionIdx, -1) : handleMoveEssai(sectionIdx, -1))}
              disabled={sectionIdx === 0}
              title="Pindah ke atas"
              className="clay-btn-white p-1.5 disabled:opacity-40"
            >
              <ArrowUp className="h-3.5 w-3.5 text-slate-600" />
            </button>
            <button
              type="button"
              onClick={() => (isPg ? handleMovePg(sectionIdx, 1) : handleMoveEssai(sectionIdx, 1))}
              disabled={sectionIdx === (isPg ? pgItems.length - 1 : essaiItems.length - 1)}
              title="Pindah ke bawah"
              className="clay-btn-white p-1.5 disabled:opacity-40"
            >
              <ArrowDown className="h-3.5 w-3.5 text-slate-600" />
            </button>
            <button
              type="button"
              onClick={() => handleDuplicate(q.id, isPg)}
              title="Duplikat soal"
              className="clay-btn-white p-1.5"
            >
              <Copy className="h-3.5 w-3.5 text-slate-600" />
            </button>
            <button
              type="button"
              onClick={() => handleRemove(q.id)}
              title="Hapus soal"
              className="clay-btn-white p-1.5 text-rose-600"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Baris 2: Pemilih TP Kisi-Kisi (Full Width agar lega) */}
        <div>
          <select
            value={q.tp_code || ''}
            onChange={(e) => updateById(q.id, { tp_code: e.target.value })}
            className="clay-input w-full px-3 py-2 text-xs font-semibold text-slate-700"
            aria-label={`TP Terkait Soal ${isPg ? 'PG' : 'Essai'} ${sectionIdx + 1}`}
          >
            <option value="">-- Pilih TP Kisi-Kisi --</option>
            {availableTps.map((tp) => (
              <option key={tp.code} value={tp.code}>
                {tp.code}: {tp.deskripsi.slice(0, 60)}
              </option>
            ))}
          </select>
        </div>

        {/* Baris 3: Level Kognitif (Sejajar Horizontal) + Tombol Wacana/Stimulus */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-1.5">
            {(['C1-C2', 'C3', 'C4-C6'] as const).map((lvl) => (
              <button
                key={lvl}
                type="button"
                onClick={() => updateById(q.id, { level_kognitif: lvl })}
                className={`whitespace-nowrap px-2.5 py-1 text-[11px] font-bold ${
                  q.level_kognitif === lvl ? 'clay-btn-success' : 'clay-btn-white'
                }`}
              >
                {lvl === 'C1-C2' ? 'Mudah' : lvl === 'C3' ? 'Sedang' : 'HOTS'} ({lvl})
              </button>
            ))}
          </div>
          {!showStimulus && (
            <button
              type="button"
              onClick={() => setOpenStimulusMap((prev) => ({ ...prev, [q.id]: true }))}
              className="clay-btn-white shrink-0 whitespace-nowrap px-2.5 py-1 text-[11px] font-bold text-blue-700"
            >
              + Wacana / Teks Pengantar
            </button>
          )}
        </div>

        {/* Wacana / Teks Pengantar Singkat Opsional */}
        {showStimulus && (
          <div>
            <div className="mb-1 flex items-center justify-between">
              <label className="text-[11px] font-bold text-slate-600">
                Wacana Pengantar / Teks Bacaan (Opsional):
              </label>
              <button
                type="button"
                onClick={() => {
                  updateById(q.id, { stimulus: '' });
                  setOpenStimulusMap((prev) => ({ ...prev, [q.id]: false }));
                }}
                className="text-[10px] font-semibold text-rose-500 underline"
              >
                Hapus Wacana
              </button>
            </div>
            <textarea
              rows={2}
              value={q.stimulus || ''}
              onChange={(e) => updateById(q.id, { stimulus: e.target.value })}
              placeholder="Tempel teks bacaan singkat, tabel narasi, atau kasus pengantar soal..."
              className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
            />
          </div>
        )}

        {/* Pertanyaan Utama */}
        <div>
          <textarea
            rows={2}
            value={q.pertanyaan}
            onChange={(e) => updateById(q.id, { pertanyaan: e.target.value })}
            placeholder={`Tuliskan pertanyaan ${isPg ? 'Pilihan Ganda' : 'Essai'} No. ${sectionIdx + 1} di sini...`}
            className="clay-input w-full px-3 py-2 text-xs font-semibold text-slate-900 sm:text-sm"
          />
        </div>

        {/* Konten Opsi PG atau Kunci Jawaban Essai */}
        {isPg ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-slate-600">
                Opsi Jawaban (Klik huruf A–{OPTION_LETTERS[q.opsi.length - 1] || 'D'} untuk set Kunci Jawaban):
              </span>
              {q.opsi.length < 5 && (
                <button
                  type="button"
                  onClick={() => handleAddOption(q.id)}
                  className="clay-btn-white px-2 py-0.5 text-[11px] font-bold text-blue-700"
                >
                  + Opsi {OPTION_LETTERS[q.opsi.length]}
                </button>
              )}
            </div>
            {q.opsi.map((optVal, oIdx) => {
              const letter = OPTION_LETTERS[oIdx] || String(oIdx + 1);
              const isKey = (q.kunci_jawaban || 'A').toUpperCase() === letter;
              return (
                <div key={oIdx} className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => updateById(q.id, { kunci_jawaban: letter })}
                    title={`Jadikan ${letter} sebagai kunci jawaban`}
                    className={`flex h-8 w-8 shrink-0 items-center justify-center text-xs font-extrabold ${
                      isKey ? 'clay-btn-success' : 'clay-btn-white text-slate-700'
                    }`}
                  >
                    {letter}
                  </button>
                  <input
                    type="text"
                    value={optVal}
                    onChange={(e) => {
                      const nextOpsi = [...q.opsi];
                      nextOpsi[oIdx] = e.target.value;
                      updateById(q.id, { opsi: nextOpsi });
                    }}
                    placeholder={`Tulis pilihan jawaban ${letter}...`}
                    className="clay-input flex-1 px-3 py-1.5 text-xs font-medium text-slate-800"
                  />
                  {q.opsi.length > 3 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveOption(q.id, oIdx)}
                      className="clay-btn-white px-2 py-1 text-xs font-bold text-slate-500"
                      title="Hapus opsi"
                    >
                      ×
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div>
            <label className="mb-1 block text-[11px] font-bold text-emerald-700">
              Kunci Jawaban / Poin Rubrik Uraian
            </label>
            <textarea
              rows={2}
              value={q.kunci_jawaban || ''}
              onChange={(e) => updateById(q.id, { kunci_jawaban: e.target.value })}
              placeholder="Tuliskan kunci jawaban ideal atau poin rubrik penilaian uraian..."
              className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
            />
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="clay-card space-y-6 p-5">
      {/* Header Judul Pembuatan Soal */}
      <div className="border-b border-slate-200 pb-3">
        <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800">
          Pembuatan Soal Evaluasi
        </h2>
        <p className="text-[11px] font-medium text-slate-500">
          Susun butir soal secara manual pada Bagian A (Pilihan Ganda) dan Bagian B (Essai).
        </p>
      </div>

      {/* SEKSI 1: BAGIAN A - SOAL PILIHAN GANDA */}
      <div className="rounded-2xl border border-blue-100 bg-blue-50/30 p-4 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-blue-600 text-xs font-extrabold text-white">
              A
            </span>
            <h3 className="text-xs font-black uppercase tracking-wide text-blue-900">
              Bagian A: Soal Pilihan Ganda
            </h3>
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-extrabold text-blue-800">
              {pgItems.length} Soal
            </span>
          </div>
          <button
            type="button"
            onClick={handleAddPgQuestion}
            className="clay-btn-primary inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Tambah Soal PG</span>
          </button>
        </div>

        {pgItems.length === 0 ? (
          <div className="rounded-xl border border-dashed border-blue-200 bg-white/60 p-4 text-center">
            <p className="text-xs font-semibold text-slate-500">
              Belum ada soal Pilihan Ganda. Klik tombol "+ Tambah Soal PG" di atas untuk menambahkan.
            </p>
          </div>
        ) : (
          <div className="space-y-3.5">
            {pgItems.map((q, idx) => renderQuestionCard(q, idx, true))}
          </div>
        )}

        {pgItems.length > 0 && (
          <div className="pt-2">
            <button
              type="button"
              onClick={handleAddPgQuestion}
              className="clay-btn-white inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-blue-700"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>+ Tambah Soal PG Lagi</span>
            </button>
          </div>
        )}
      </div>

      {/* SEKSI 2: BAGIAN B - SOAL ESSAI / URAIAN */}
      <div className="rounded-2xl border border-emerald-100 bg-emerald-50/30 p-4 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-emerald-600 text-xs font-extrabold text-white">
              B
            </span>
            <h3 className="text-xs font-black uppercase tracking-wide text-emerald-900">
              Bagian B: Soal Essai
            </h3>
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-extrabold text-emerald-800">
              {essaiItems.length} Soal
            </span>
          </div>
          <button
            type="button"
            onClick={handleAddEssaiQuestion}
            className="clay-btn-white inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-emerald-800 hover:bg-emerald-50"
          >
            <Plus className="h-3.5 w-3.5 text-emerald-600" />
            <span>Tambah Soal Essai</span>
          </button>
        </div>

        {essaiItems.length === 0 ? (
          <div className="rounded-xl border border-dashed border-emerald-200 bg-white/60 p-4 text-center">
            <p className="text-xs font-semibold text-slate-500">
              Belum ada soal Essai. Klik tombol "+ Tambah Soal Essai" di atas untuk menambahkan.
            </p>
          </div>
        ) : (
          <div className="space-y-3.5">
            {essaiItems.map((q, idx) => renderQuestionCard(q, idx, false))}
          </div>
        )}

        {essaiItems.length > 0 && (
          <div className="pt-2">
            <button
              type="button"
              onClick={handleAddEssaiQuestion}
              className="clay-btn-white inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-emerald-800"
            >
              <Plus className="h-3.5 w-3.5 text-emerald-600" />
              <span>+ Tambah Soal Essai Lagi</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
