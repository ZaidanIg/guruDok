import React from 'react';
import { PackageCheck, CheckCircle2 } from 'lucide-react';
import { CustomDocumentOverrides } from '../../types';

export const SUPERVISI_BUNDLE_ITEMS: { code: string; title: string; format: string }[] = [
  { code: '01', title: 'Cover, Daftar Isi, Pengesahan 3 Pihak & Instrumen Supervisi', format: 'DOCX / PDF' },
  { code: '02', title: 'Administrasi Kelas (Struktur, Piket, Denah, Kesepakatan)', format: 'DOCX' },
  { code: '03–06', title: 'CP-TP, ATP, Prota & Promes Berformula Aktif', format: 'DOCX & XLSX' },
  { code: '07–09', title: 'KKTP, Modul Ajar Pembelajaran Mendalam 3M & LKPD', format: 'DOCX' },
  { code: '13–17', title: 'Presensi, Jurnal Mengajar, Daftar Nilai, e-Rapor & Rekap', format: 'XLSX & DOCX' },
];

export interface SupervisiEditorSectionProps {
  customOverrides: CustomDocumentOverrides;
  onChangeCustomOverrides: (next: CustomDocumentOverrides) => void;
}

export const SupervisiEditorSection: React.FC<SupervisiEditorSectionProps> = ({
  customOverrides,
  onChangeCustomOverrides,
}) => {
  return (
    <div className="clay-card p-5 space-y-4">
      <div className="border-b border-slate-200 pb-3">
        <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-800 flex items-center gap-2">
          <PackageCheck className="h-4 w-4 text-emerald-600" />
          <span>3. Identitas &amp; Validasi Pengawas Supervisi Akademik</span>
        </h2>
        <p className="text-[11px] font-medium text-slate-500">
          Data SK Mengajar dan Supervisor akan dicetak pada Cover Resmi, Instrumen Telaah, &amp; Pengesahan 3 Pihak.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">
            Nomor SK Pembagian Tugas Mengajar
          </label>
          <input
            type="text"
            value={customOverrides.nomor_sk_mengajar || ''}
            placeholder="Contoh: 800/142/SK-PBM/2025"
            onChange={(e) =>
              onChangeCustomOverrides({
                ...customOverrides,
                nomor_sk_mengajar: e.target.value,
              })
            }
            className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">
            Tanggal Pelaksanaan Supervisi
          </label>
          <input
            type="date"
            value={customOverrides.tanggal_supervisi || ''}
            onChange={(e) =>
              onChangeCustomOverrides({
                ...customOverrides,
                tanggal_supervisi: e.target.value,
              })
            }
            className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">
            Nama Pengawas / Supervisor Pembina
          </label>
          <input
            type="text"
            value={customOverrides.nama_pengawas || ''}
            placeholder="Contoh: Drs. Hendra Wijaya, M.Pd."
            onChange={(e) =>
              onChangeCustomOverrides({
                ...customOverrides,
                nama_pengawas: e.target.value,
              })
            }
            className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">
            NIP Pengawas Pembina
          </label>
          <input
            type="text"
            value={customOverrides.nip_pengawas || ''}
            placeholder="Contoh: 196904121994031005"
            onChange={(e) =>
              onChangeCustomOverrides({
                ...customOverrides,
                nip_pengawas: e.target.value,
              })
            }
            className="clay-input w-full px-3 py-2 text-xs font-medium text-slate-800"
          />
        </div>
      </div>

      {/* Checklist Isi Arsip ZIP */}
      <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-3.5">
        <p className="text-xs font-extrabold text-emerald-900 mb-2">
          Cakupan Berkas Otomatis dalam Master Bundle (.ZIP / Binder PDF):
        </p>
        <div className="space-y-1.5">
          {SUPERVISI_BUNDLE_ITEMS.map((item) => (
            <div key={item.code} className="flex items-center justify-between gap-2 text-[11px]">
              <div className="flex items-center gap-1.5 text-emerald-800 font-semibold">
                <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
                <span>{item.title}</span>
              </div>
              <span className="shrink-0 rounded bg-white/90 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                {item.format}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
