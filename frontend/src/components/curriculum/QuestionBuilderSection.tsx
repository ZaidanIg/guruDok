import React, { useState } from 'react';
import {
  Plus,
  Trash2,
  ArrowUp,
  ArrowDown,
  Copy,
  Database,
  Loader2,
} from 'lucide-react';
import {
  CustomQuestionItem,
  Jenjang,
  LearningObjective,
  ServiceId,
} from '../../types';
import { apiClient } from '../../services/api';

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
): CustomQuestionItem => {
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
  serviceId,
  jenjang,
  subjectId,
  chapterId,
  availableTps,
  questions,
  onChangeQuestions,
}) => {
  const [isLoadingBank, setIsLoadingBank] = useState(false);
  const [bankNotice, setBankNotice] = useState<string | null>(null);
  const [openStimulusMap, setOpenStimulusMap] = useState<Record<number, boolean>>({});

  const defaultTpCode = availableTps[0]?.code || '';
  const items = questions.length > 0 ? questions : [createEmptyQuestion(jenjang, 'PG', defaultTpCode)];

  const updateAt = (idx: number, patch: Partial<CustomQuestionItem>) => {
    const next = items.map((q, i) => (i === idx ? { ...q, ...patch } : q));
    onChangeQuestions(next);
  };

  const handleToggleType = (idx: number, nextType: 'PG' | 'URAIAN') => {
    const current = items[idx];
    if (current.tipe_soal === nextType) return;
    const defaultOpts = jenjang === 'SMA' ? ['', '', '', '', ''] : ['', '', '', ''];
    updateAt(idx, {
      tipe_soal: nextType,
      opsi: nextType === 'PG' ? (current.opsi.length >= 3 ? current.opsi : defaultOpts) : [],
      kunci_jawaban: nextType === 'PG' ? 'A' : '',
    });
  };

  const handleAddOption = (qIdx: number) => {
    const q = items[qIdx];
    if (q.opsi.length >= 5) return;
    updateAt(qIdx, { opsi: [...q.opsi, ''] });
  };

  const handleRemoveOption = (qIdx: number, optIdx: number) => {
    const q = items[qIdx];
    if (q.opsi.length <= 3) return;
    const nextOpsi = q.opsi.filter((_, i) => i !== optIdx);
    const currentKeyIdx = OPTION_LETTERS.indexOf((q.kunci_jawaban || 'A') as any);
    const nextKey = currentKeyIdx >= nextOpsi.length ? 'A' : (q.kunci_jawaban || 'A');
    updateAt(qIdx, { opsi: nextOpsi, kunci_jawaban: nextKey });
  };

  const handleMove = (idx: number, dir: -1 | 1) => {
    const target = idx + dir;
    if (target < 0 || target >= items.length) return;
    const copy = [...items];
    const [moved] = copy.splice(idx, 1);
    copy.splice(target, 0, moved);
    onChangeQuestions(copy);
  };

  const handleDuplicate = (idx: number) => {
    const src = items[idx];
    const clone: CustomQuestionItem = {
      ...src,
      id: `q-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      opsi: [...src.opsi],
    };
    const next = [...items];
    next.splice(idx + 1, 0, clone);
    onChangeQuestions(next);
  };

  const handleRemove = (idx: number) => {
    if (items.length <= 1) {
      onChangeQuestions([createEmptyQuestion(jenjang, 'PG', defaultTpCode)]);
      return;
    }
    onChangeQuestions(items.filter((_, i) => i !== idx));
  };

  const handleFillDraftFromTp = () => {
    const optCount = jenjang === 'SMA' ? 5 : 4;
    const tps = availableTps.length > 0
      ? availableTps
      : [{ code: 'TP.1.1', deskripsi: 'Memahami konsep inti materi pembelajaran.', alokasi_jp: 4 }];
    const count = serviceId === '10_kuis' ? 5 : serviceId === '11_sumatif_bab' ? 5 : 6;
    const levels: Array<'C1-C2' | 'C3' | 'C4-C6'> = ['C1-C2', 'C3', 'C4-C6'];
    const generated: CustomQuestionItem[] = Array.from({ length: count }, (_, i) => {
      const tp = tps[i % tps.length];
      const isUraian = i >= count - 1;
      return {
        id: `q-draft-${Date.now()}-${i}`,
        tipe_soal: isUraian ? 'URAIAN' : 'PG',
        tp_code: tp.code,
        level_kognitif: levels[i % levels.length],
        stimulus: '',
        pertanyaan: isUraian
          ? `Jelaskan dan berikan contoh penerapan dari: ${tp.deskripsi}`
          : `Manakah pernyataan yang paling tepat mengenai ${tp.deskripsi}?`,
        opsi: isUraian ? [] : Array.from({ length: optCount }, (__, o) => `Pilihan ${OPTION_LETTERS[o]} terkait ${tp.code}`),
        kunci_jawaban: isUraian ? `Penjelasan runtut sesuai indikator ${tp.code}.` : 'A',
        pembahasan: `Mengacu pada indikator ${tp.code}.`,
      };
    });
    onChangeQuestions(generated);
    setBankNotice(`${generated.length} draf soal berhasil diturunkan dari TP.`);
  };

  const handleImportFromBank = async () => {
    setIsLoadingBank(true);
    setBankNotice(null);
    try {
      const fetched = await apiClient.getQuestions({
        subjectId,
        chapterId,
        limit: 15,
      });
      if (!fetched || fetched.length === 0) {
        setBankNotice('Belum ada butir soal tersimpan untuk mata pelajaran ini di Bank Soal.');
        return;
      }
      const mapped: CustomQuestionItem[] = fetched.map((f: any, idx: number) => ({
        id: `q-bank-${f.id || idx}`,
        tipe_soal: f.tipe_soal === 'URAIAN' ? 'URAIAN' : 'PG',
        tp_code: f.tp_code || defaultTpCode,
        level_kognitif: f.level_kognitif || 'C1-C2',
        stimulus: f.stimulus || '',
        pertanyaan: f.pertanyaan || '',
        opsi: Array.isArray(f.opsi) ? f.opsi : [],
        kunci_jawaban: f.kunci_jawaban || 'A',
        bobot_skor: f.bobot_skor ?? undefined,
        pembahasan: f.pembahasan || '',
      }));
      const nonEmptyCurrent = questions.filter((q) => q.pertanyaan.trim().length > 0);
      onChangeQuestions([...nonEmptyCurrent, ...mapped]);
      setBankNotice(`${mapped.length} soal berhasil dimuat dari Bank Soal GuruDok.`);
    } finally {
      setIsLoadingBank(false);
    }
  };

  return (
    <div className="clay-card p-5">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
        <div>
          <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800">
            Pembuatan Soal
          </h2>
          <p className="text-[11px] font-medium text-slate-500">
            Tulis soal &amp; klik huruf kunci jawaban. Kisi-Kisi, Kartu Soal, &amp; Pedoman Penskoran (Skor Maks 100) terhitung otomatis.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleFillDraftFromTp}
            className="clay-btn-white inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-bold text-slate-700"
          >
            <span>Isi Draf dari TP</span>
          </button>
          <button
            type="button"
            onClick={handleImportFromBank}
            disabled={isLoadingBank}
            className="clay-btn-white inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-bold text-slate-700 disabled:opacity-60"
          >
            {isLoadingBank ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin text-blue-600" />
            ) : (
              <Database className="h-3.5 w-3.5 text-emerald-600" />
            )}
            <span>Ambil dari Bank Soal</span>
          </button>
        </div>
      </div>

      {bankNotice && (
        <div className="mt-3 flex items-center justify-between rounded-xl border border-blue-200 bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-800">
          <span>{bankNotice}</span>
          <button type="button" onClick={() => setBankNotice(null)} className="text-[11px] font-bold underline">
            Tutup
          </button>
        </div>
      )}

      <div className="mt-4 space-y-3.5">
        {items.map((q, idx) => {
          const showStimulus = Boolean(openStimulusMap[idx] || (q.stimulus && q.stimulus.length > 0));
          return (
            <div key={q.id || idx} className="clay-subcard p-4 space-y-3">
              {/* Header Bar Kartu Soal */}
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="clay-badge px-2.5 py-1 text-[11px]">
                    Soal #{idx + 1}
                  </span>
                  <div className="inline-flex gap-1">
                    <button
                      type="button"
                      onClick={() => handleToggleType(idx, 'PG')}
                      className={`px-2.5 py-1 text-[11px] font-bold ${
                        q.tipe_soal === 'PG' ? 'clay-btn-primary' : 'clay-btn-white'
                      }`}
                    >
                      Pilihan Ganda
                    </button>
                    <button
                      type="button"
                      onClick={() => handleToggleType(idx, 'URAIAN')}
                      className={`px-2.5 py-1 text-[11px] font-bold ${
                        q.tipe_soal === 'URAIAN' ? 'clay-btn-primary' : 'clay-btn-white'
                      }`}
                    >
                      Uraian / Isian
                    </button>
                  </div>
                </div>

                {/* Aksi Kartu: Urutan, Duplikat, Hapus */}
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => handleMove(idx, -1)}
                    disabled={idx === 0}
                    title="Pindah ke atas"
                    className="clay-btn-white p-1.5 disabled:opacity-40"
                  >
                    <ArrowUp className="h-3.5 w-3.5 text-slate-600" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleMove(idx, 1)}
                    disabled={idx === items.length - 1}
                    title="Pindah ke bawah"
                    className="clay-btn-white p-1.5 disabled:opacity-40"
                  >
                    <ArrowDown className="h-3.5 w-3.5 text-slate-600" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDuplicate(idx)}
                    title="Duplikat soal"
                    className="clay-btn-white p-1.5"
                  >
                    <Copy className="h-3.5 w-3.5 text-slate-600" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleRemove(idx)}
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
                  onChange={(e) => updateAt(idx, { tp_code: e.target.value })}
                  className="clay-input w-full px-3 py-2 text-xs font-semibold text-slate-700"
                  aria-label={`TP Terkait Soal ${idx + 1}`}
                >
                  <option value="">-- Pilih TP Kisi-Kisi --</option>
                  {availableTps.map((tp) => (
                    <option key={tp.code} value={tp.code}>
                      {tp.code}: {tp.deskripsi.slice(0, 60)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Baris 3: Level Kognitif (Sejajar Horizontal) + Tombol Stimulus */}
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-1.5">
                  {(['C1-C2', 'C3', 'C4-C6'] as const).map((lvl) => (
                    <button
                      key={lvl}
                      type="button"
                      onClick={() => updateAt(idx, { level_kognitif: lvl })}
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
                    onClick={() => setOpenStimulusMap((prev) => ({ ...prev, [idx]: true }))}
                    className="clay-btn-white shrink-0 whitespace-nowrap px-2.5 py-1 text-[11px] font-bold text-blue-700"
                  >
                    + Stimulus
                  </button>
                )}
              </div>

              {/* Stimulus / Wacana Singkat Opsional */}
              {showStimulus && (
                <div>
                  <label className="mb-1 block text-[11px] font-bold text-slate-600">
                    Stimulus / Wacana Singkat (Opsional)
                  </label>
                  <textarea
                    rows={2}
                    value={q.stimulus || ''}
                    onChange={(e) => updateAt(idx, { stimulus: e.target.value })}
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
                  onChange={(e) => updateAt(idx, { pertanyaan: e.target.value })}
                  placeholder={`Tuliskan pertanyaan Soal #${idx + 1} di sini...`}
                  className="clay-input w-full px-3 py-2 text-xs font-semibold text-slate-900 sm:text-sm"
                />
              </div>

              {/* Pilihan Ganda (1-Klik Kunci A-E) atau Uraian */}
              {q.tipe_soal === 'PG' ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-slate-600">
                      Opsi Jawaban (Klik huruf A–{OPTION_LETTERS[q.opsi.length - 1] || 'D'} untuk set Kunci Jawaban):
                    </span>
                    {q.opsi.length < 5 && (
                      <button
                        type="button"
                        onClick={() => handleAddOption(idx)}
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
                          onClick={() => updateAt(idx, { kunci_jawaban: letter })}
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
                            updateAt(idx, { opsi: nextOpsi });
                          }}
                          placeholder={`Tulis pilihan jawaban ${letter}...`}
                          className="clay-input flex-1 px-3 py-1.5 text-xs font-medium text-slate-800"
                        />
                        {q.opsi.length > 3 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveOption(idx, oIdx)}
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
                    onChange={(e) => updateAt(idx, { kunci_jawaban: e.target.value })}
                    placeholder="Tuliskan kunci jawaban ideal atau poin rubrik penilaian uraian..."
                    className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer Tombol Tambah Soal */}
      <div className="mt-4 flex flex-wrap items-center gap-2.5 pt-3 border-t border-slate-200">
        <button
          type="button"
          onClick={() => onChangeQuestions([...items, createEmptyQuestion(jenjang, 'PG', defaultTpCode)])}
          className="clay-btn-primary inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold"
        >
          <Plus className="h-3.5 w-3.5" />
          <span>Tambah Soal PG</span>
        </button>
        <button
          type="button"
          onClick={() => onChangeQuestions([...items, createEmptyQuestion(jenjang, 'URAIAN', defaultTpCode)])}
          className="clay-btn-white inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold text-slate-700"
        >
          <Plus className="h-3.5 w-3.5" />
          <span>Tambah Soal Uraian</span>
        </button>
      </div>
    </div>
  );
};
