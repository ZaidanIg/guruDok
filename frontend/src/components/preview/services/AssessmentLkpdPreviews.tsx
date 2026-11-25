import React from 'react';
import { ChapterTopic, CurriculumSubject, CustomTpItem } from '../../../types';

export interface AssessmentLkpdPreviewsProps {
  selectedSubject: CurriculumSubject | null;
  selectedChapter: ChapterTopic | null;
  activeTps: CustomTpItem[];
}

export const AssessmentLkpdPreviews: React.FC<AssessmentLkpdPreviewsProps> = ({
  selectedSubject,
  selectedChapter,
  activeTps,
}) => {
  return (
    <div className="mt-5 space-y-5 text-xs leading-relaxed">
      <div className="text-center">
        <h2 className="text-base font-extrabold uppercase text-slate-900">
          LEMBAR KERJA PESERTA DIDIK (LKPD) MANDIRI
        </h2>
        <p className="font-bold uppercase text-slate-700">
          MATA PELAJARAN {selectedSubject?.nama_mapel.toUpperCase()} — FASE {selectedSubject?.fase} (KELAS{' '}
          {selectedSubject?.kelas})
        </p>
      </div>

      <div>
        <h3 className="font-extrabold uppercase text-slate-900">Identitas Peserta Didik</h3>
        <div className="paper-table-container">
          <table className="paper-table mt-1.5">
            <tbody>
              <tr>
                <th className="w-1/3 text-left">Nama Peserta Didik</th>
                <td>............................................................</td>
              </tr>
              <tr>
                <th className="text-left">Kelas / No. Absen</th>
                <td>Kelas {selectedSubject?.kelas} / ........</td>
              </tr>
              <tr>
                <th className="text-left">Topik / Materi Pokok</th>
                <td>{selectedChapter?.judul_bab || selectedSubject?.nama_mapel}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <h3 className="font-extrabold uppercase text-slate-900">A. Tujuan Pembelajaran</h3>
        <ul className="mt-1.5 list-disc space-y-1 pl-5">
          {activeTps.map((tp, idx) => (
            <li key={`${tp.code}-${idx}`}>
              <strong>[{tp.code}]</strong> {tp.deskripsi}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h3 className="font-extrabold uppercase text-slate-900">
          B. Langkah Aktivitas Pembelajaran Mendalam (3M)
        </h3>
        <div className="paper-table-container">
          <table className="paper-table mt-1.5">
            <thead>
              <tr>
                <th className="w-32 text-left">Tahap 3M</th>
                <th className="text-left">Panduan Aktivitas Mandiri / Kelompok</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="font-bold">1. Memahami</td>
                <td>
                  {selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.memahami ||
                    `Membaca dan memahami konsep inti pada materi ${selectedChapter?.judul_bab || selectedSubject?.nama_mapel}.`}
                </td>
              </tr>
              <tr>
                <td className="font-bold">2. Mengaplikasi</td>
                <td>
                  {selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.mengaplikasi ||
                    'Mengerjakan studi kasus atau praktik pemecahan masalah secara terstruktur.'}
                </td>
              </tr>
              <tr>
                <td className="font-bold">3. Merefleksi</td>
                <td>
                  {selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.merefleksi ||
                    'Menuliskan kesimpulan dan refleksi pemahaman diri setelah aktivitas.'}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <h3 className="font-extrabold uppercase text-slate-900">C. Soal Latihan / Tugas Mandiri</h3>
        <ol className="mt-1.5 list-decimal space-y-1.5 pl-5">
          <li>
            Jelaskan konsep utama yang dipelajari pada topik{' '}
            {selectedChapter?.judul_bab || selectedSubject?.nama_mapel} dengan bahasamu sendiri!
          </li>
          <li>Berikan satu contoh penerapan nyata dari materi ini dalam kehidupan sehari-hari!</li>
          <li>Apa bagian yang paling menantang dan bagaimana kamu menyelesaikannya?</li>
        </ol>
      </div>
    </div>
  );
};
