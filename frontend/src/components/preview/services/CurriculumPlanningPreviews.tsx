import React from 'react';
import {
  ChapterTopic,
  CurriculumSubject,
  CustomCpElementItem,
  CustomDocumentOverrides,
  CustomRubrikDplItem,
  CustomTpItem,
  Jenjang,
  ServiceId,
  TeacherProfile,
} from '../../../types';

export interface CurriculumPlanningPreviewsProps {
  serviceId: ServiceId;
  jenjang: Jenjang;
  kelas: number;
  semester: number;
  faseCode: string;
  faseLabel: string;
  selectedSubject: CurriculumSubject | null;
  selectedChapter: ChapterTopic | null;
  allSubjectChapters: ChapterTopic[];
  currentSemesterChapters: ChapterTopic[];
  teacher: TeacherProfile;
  activeCpElements: CustomCpElementItem[];
  officialElements: CustomCpElementItem[];
  activeTps: CustomTpItem[];
  activeDimensions: string[];
  activeDplList: CustomRubrikDplItem[];
  currentAlokasiJp: number;
  pertemuanCount: number;
  jpPerMinggu: number;
  durasiMenitJp: number;
  modelPembelajaran: string;
  monthLabels: string[];
  includeLkpd: boolean;
  includeAsesmen: boolean;
  includeRubrik: boolean;
  effectiveKesiapanMurid: string;
  effectiveKarakteristikMateri: string;
  effectiveLintasDisiplin: string;
  effectiveTopikKontekstual: string;
  effectivePemantik: string[];
  effectiveSoalAwal: string[];
  effectiveSoalProses: string[];
  effectiveSoalAkhir: string[];
  customOverrides: CustomDocumentOverrides;
}

export const CurriculumPlanningPreviews: React.FC<CurriculumPlanningPreviewsProps> = ({
  serviceId,
  jenjang,
  kelas,
  semester,
  faseCode,
  faseLabel,
  selectedSubject,
  selectedChapter,
  allSubjectChapters,
  currentSemesterChapters,
  teacher,
  activeCpElements,
  officialElements,
  activeTps,
  activeDimensions,
  activeDplList,
  currentAlokasiJp,
  pertemuanCount,
  jpPerMinggu,
  durasiMenitJp,
  modelPembelajaran,
  monthLabels,
  includeLkpd,
  includeAsesmen,
  includeRubrik,
  effectiveKesiapanMurid,
  effectiveKarakteristikMateri,
  effectiveLintasDisiplin,
  effectiveTopikKontekstual,
  effectivePemantik,
  effectiveSoalAwal,
  effectiveSoalProses,
  effectiveSoalAkhir,
  customOverrides,
}) => {
  const tujuanSubjectLines = selectedSubject?.tujuan_bskap
    ? selectedSubject.tujuan_bskap
        .split(';')
        .map((s) => s.trim())
        .filter(Boolean)
    : [
        `Menguasai konsep dan prinsip esensial ${selectedSubject?.nama_mapel} pada ${faseLabel}.`,
        `Mengembangkan keterampilan inkuiri, penalaran kritis, dan kolaborasi dalam memecahkan persoalan kontekstual.`,
        `Menumbuhkan karakter mandiri, kreatif, dan bertanggung jawab sesuai 8 Dimensi Profil Lulusan.`,
      ];

  const petunjukLkpdLines = customOverrides.petunjuk_lkpd
    ? customOverrides.petunjuk_lkpd
        .split('\n')
        .map((l) => l.trim())
        .filter(Boolean)
    : [];

  if (serviceId === '03_cp_tp') {
    return (
      <div className="mt-5 space-y-5 text-xs leading-relaxed">
        <div className="text-center">
          <h2 className="text-base font-extrabold uppercase text-slate-900">
            CAPAIAN PEMBELAJARAN DAN TUJUAN PEMBELAJARAN
          </h2>
          <p className="font-bold uppercase text-slate-700">
            MATA PELAJARAN {selectedSubject?.nama_mapel.toUpperCase()} — FASE {faseCode} (KELAS {kelas})
          </p>
        </div>

        <div className="paper-table-container">
          <table className="paper-table">
            <tbody>
              <tr>
                <th className="w-1/3 text-left">Mata Pelajaran</th>
                <td>{selectedSubject?.nama_mapel}</td>
              </tr>
              <tr>
                <th className="text-left">Jenjang / Fase / Kelas</th>
                <td>
                  {jenjang} / {faseLabel} / Kelas {kelas}
                </td>
              </tr>
              <tr>
                <th className="text-left">Alokasi Waktu</th>
                <td>
                  {selectedSubject?.total_alokasi_jp_tahun || 108} JP/Tahun ({jpPerMinggu} JP/Minggu ×{' '}
                  {durasiMenitJp} Menit)
                </td>
              </tr>
              <tr>
                <th className="text-left">Dasar Hukum</th>
                <td>
                  Kepka BSKAP Kemendikdasmen No. 046/H/KR/2025 &amp; Permendikdasmen No. 13/2025
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div>
          <h3 className="font-extrabold text-slate-900">
            1. Rasional Mata Pelajaran {selectedSubject?.nama_mapel}
          </h3>
          <p className="mt-1 text-justify text-slate-800">
            {selectedSubject?.rasional_bskap ||
              `Mata pelajaran ${selectedSubject?.nama_mapel} membekali peserta didik dengan kemampuan berpikir kritis, analitis, kreatif, serta keterampilan pemecahan masalah secara sistematis sesuai perkembangan ilmu pengetahuan dan teknologi.`}
          </p>
        </div>

        <div>
          <h3 className="font-extrabold text-slate-900">
            2. Tujuan Mata Pelajaran {selectedSubject?.nama_mapel}
          </h3>
          <div className="paper-table-container">
            <table className="paper-table mt-1.5">
              <thead>
                <tr>
                  <th className="w-10 text-center">No</th>
                  <th>Rumusan Tujuan Mata Pelajaran</th>
                </tr>
              </thead>
              <tbody>
                {tujuanSubjectLines.map((tuj, idx) => (
                  <tr key={`tuj-${idx}`}>
                    <td className="text-center font-bold">{idx + 1}</td>
                    <td>{tuj}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h3 className="font-extrabold text-slate-900">
            3. Karakteristik &amp; 4. Capaian Pembelajaran {faseLabel} Berdasarkan Elemen
          </h3>
          <p className="mt-1 text-slate-800">
            {selectedSubject?.karakteristik_bskap || effectiveKarakteristikMateri}
          </p>
          <div className="paper-table-container">
            <table className="paper-table mt-2">
              <thead>
                <tr>
                  <th className="w-1/4">Elemen</th>
                  <th>Deskripsi Capaian Pembelajaran Resmi (BSKAP 046/2025)</th>
                </tr>
              </thead>
              <tbody>
                {activeCpElements.map((el, i) => (
                  <tr key={el.kode_elemen || `cp-el-${i}`}>
                    <td className="font-bold">{el.nama_elemen}</td>
                    <td>{el.deskripsi_cp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h3 className="font-extrabold text-slate-900">
            5. Pemetaan Capaian dan Tujuan Pembelajaran Semester {semester}
          </h3>
          {currentSemesterChapters.map((bab) => {
            const isCurrentSelected = bab.id === selectedChapter?.id;
            const babTps = isCurrentSelected ? activeTps : bab.tujuan_pembelajaran;
            const babJp = isCurrentSelected ? currentAlokasiJp : bab.alokasi_jp;
            return (
              <div key={bab.id} className="mt-3">
                <p className="font-bold text-blue-900">
                  BAB {bab.nomor_bab}: {bab.judul_bab.toUpperCase()} (Semester {bab.semester})
                </p>
                <div className="paper-table-container">
                  <table className="paper-table mt-1">
                    <thead>
                      <tr>
                        <th className="w-1/4">KATEGORI</th>
                        <th>RUMUSAN</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td className="font-bold">Elemen</td>
                        <td>{bab.elemen_cp || officialElements[0]?.nama_elemen}</td>
                      </tr>
                      <tr>
                        <td className="font-bold">Kalimat CP</td>
                        <td>
                          Peserta didik mampu menguasai konsep {bab.judul_bab} pada elemen{' '}
                          {bab.elemen_cp || officialElements[0]?.nama_elemen} serta menerapkannya secara
                          kontekstual.
                        </td>
                      </tr>
                      <tr>
                        <td className="font-bold">Tujuan Pembelajaran</td>
                        <td>
                          <ol className="list-decimal pl-4 space-y-1">
                            {babTps.map((t, idx) => (
                              <li key={`${t.code}-${idx}`}>
                                <strong>[{t.code}]</strong> {t.deskripsi} ({t.alokasi_jp} JP)
                              </li>
                            ))}
                          </ol>
                        </td>
                      </tr>
                      <tr>
                        <td className="font-bold">Alokasi Waktu</td>
                        <td className="font-bold">{babJp} Jam Pelajaran (JP)</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  if (serviceId === '04_atp') {
    return (
      <div className="mt-5 space-y-5 text-xs leading-relaxed">
        <div className="text-center">
          <h2 className="text-base font-extrabold uppercase text-slate-900">
            ALUR TUJUAN PEMBELAJARAN (ATP)
          </h2>
          <p className="font-bold uppercase text-slate-700">
            MATA PELAJARAN {selectedSubject?.nama_mapel.toUpperCase()} — FASE {faseCode} KELAS {kelas}
          </p>
        </div>

        <div>
          <h3 className="font-extrabold uppercase text-slate-900">
            CAPAIAN PEMBELAJARAN FASE {faseCode} BERDASARKAN ELEMEN
          </h3>
          <div className="paper-table-container">
            <table className="paper-table mt-1.5">
              <thead>
                <tr>
                  <th className="w-1/4">Elemen</th>
                  <th>Capaian Pembelajaran</th>
                </tr>
              </thead>
              <tbody>
                {activeCpElements.map((el, i) => (
                  <tr key={el.kode_elemen || `atp-cp-${i}`}>
                    <td className="font-bold">{el.nama_elemen}</td>
                    <td>{el.deskripsi_cp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h3 className="font-extrabold uppercase text-slate-900">
            RINCIAN ALUR TUJUAN PEMBELAJARAN SEMESTER {semester}
          </h3>
          {currentSemesterChapters.map((bab) => {
            const isCurrentSelected = bab.id === selectedChapter?.id;
            const babTps = isCurrentSelected ? activeTps : bab.tujuan_pembelajaran;
            const babJp = isCurrentSelected ? currentAlokasiJp : bab.alokasi_jp;
            return (
              <div key={bab.id} className="mt-3">
                <div className="paper-table-container">
                  <table className="paper-table">
                    <thead>
                      <tr>
                        <th colSpan={2} className="text-left">
                          BAB {bab.nomor_bab}: {bab.judul_bab.toUpperCase()} (SEMESTER {bab.semester})
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td className="w-1/3 font-bold">Elemen</td>
                        <td>{bab.elemen_cp || officialElements[0]?.nama_elemen}</td>
                      </tr>
                      <tr>
                        <td className="font-bold">Capaian Pembelajaran Pertahun</td>
                        <td>
                          Memahami, menerapkan, dan mengevaluasi konsep {bab.judul_bab} pada{' '}
                          {selectedSubject?.nama_mapel} Kelas {kelas}.
                        </td>
                      </tr>
                      <tr>
                        <td className="font-bold">Fase {faseCode} / Alur Tujuan Pembelajaran</td>
                        <td>
                          <ol className="list-decimal pl-4 space-y-1">
                            {babTps.map((t, i) => (
                              <li key={`${t.code}-${i}`}>
                                <strong>{t.code}:</strong> {t.deskripsi} ({t.alokasi_jp} JP)
                              </li>
                            ))}
                          </ol>
                        </td>
                      </tr>
                      <tr>
                        <td className="font-bold">Jumlah Jam</td>
                        <td className="font-bold">
                          {babJp} JP ({Math.max(1, Math.round(babJp / jpPerMinggu))} Pertemuan)
                        </td>
                      </tr>
                      <tr>
                        <td className="font-bold">Kata Kunci</td>
                        <td>
                          {bab.judul_bab}, {bab.elemen_cp || 'Konsep Inti'}, Analisis Kontekstual
                        </td>
                      </tr>
                      <tr>
                        <td className="font-bold">Topik / Konten Inti</td>
                        <td>{isCurrentSelected ? effectiveTopikKontekstual : bab.judul_bab}</td>
                      </tr>
                      <tr>
                        <td className="font-bold">Glosarium</td>
                        <td>
                          {bab.judul_bab}: Lingkup kompetensi utama pada mata pelajaran{' '}
                          {selectedSubject?.nama_mapel} Kelas {kelas}.
                        </td>
                      </tr>
                      <tr>
                        <td className="font-bold">Dimensi Profil Lulusan</td>
                        <td>{(bab.dimensi_profil_lulusan || activeDimensions).join(', ')}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })}
        </div>

        <div className="space-y-2 border-t border-slate-300 pt-3">
          <p>
            <strong>Rasional Penyusunan Alur Tujuan Pembelajaran:</strong> Penyusunan ATP{' '}
            {selectedSubject?.nama_mapel} Kelas {kelas} dilakukan secara berjenjang dari kompetensi fondasi
            menuju aplikasi kontekstual dan evaluasi reflektif.
          </p>
          {customOverrides.catatan_khusus && (
            <p>
              <strong>Catatan Khusus Penggunaan ATP:</strong> {customOverrides.catatan_khusus}
            </p>
          )}
        </div>
      </div>
    );
  }

  if (serviceId === '08_modul_ajar') {
    return (
      <div className="mt-5 space-y-5 text-xs leading-relaxed">
        <div className="text-center">
          <h2 className="text-base font-extrabold uppercase text-slate-900">MODUL AJAR DEEP LEARNING</h2>
          <p className="font-bold uppercase text-slate-700">
            {selectedSubject?.nama_mapel.toUpperCase()} — BAB {selectedChapter?.nomor_bab || 1}:{' '}
            {(selectedChapter?.judul_bab || '').toUpperCase()}
          </p>
        </div>

        <div>
          <h3 className="font-extrabold uppercase text-slate-900">A. Identitas Modul</h3>
          <div className="paper-table-container">
            <table className="paper-table mt-1.5">
              <tbody>
                <tr>
                  <th className="w-1/3 text-left">Nama Penyusun</th>
                  <td>
                    {teacher.nama_guru || 'Nama Guru Anda'} (NIP. {teacher.nip_guru || '-'})
                  </td>
                </tr>
                <tr>
                  <th className="text-left">Institusi / Sekolah</th>
                  <td>{teacher.nama_sekolah || 'Nama Sekolah Anda'}</td>
                </tr>
                <tr>
                  <th className="text-left">Tahun Penyusunan / Semester</th>
                  <td>
                    Tahun Ajaran 2025/2026 / Semester {semester} ({semester === 1 ? 'Ganjil' : 'Genap'})
                  </td>
                </tr>
                <tr>
                  <th className="text-left">Jenjang / Fase / Kelas</th>
                  <td>
                    {jenjang} / {faseLabel} / Kelas {kelas}
                  </td>
                </tr>
                <tr>
                  <th className="text-left">Mata Pelajaran</th>
                  <td>{selectedSubject?.nama_mapel}</td>
                </tr>
                <tr>
                  <th className="text-left">Bab / Materi Pokok</th>
                  <td>
                    Bab {selectedChapter?.nomor_bab || 1}: {selectedChapter?.judul_bab}
                  </td>
                </tr>
                <tr>
                  <th className="text-left">Alokasi Waktu</th>
                  <td>
                    {currentAlokasiJp} JP ({pertemuanCount} Pertemuan × {jpPerMinggu} JP @ {durasiMenitJp} Menit)
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="space-y-2.5">
          <div>
            <h3 className="font-extrabold uppercase text-slate-900">
              B. Identifikasi Kesiapan Peserta Didik
            </h3>
            <p className="mt-1 text-slate-800">{effectiveKesiapanMurid}</p>
          </div>
          <div>
            <h3 className="font-extrabold uppercase text-slate-900">C. Karakteristik Materi Pelajaran</h3>
            <p className="mt-1 text-slate-800">{effectiveKarakteristikMateri}</p>
          </div>
        </div>

        <div>
          <h3 className="font-extrabold uppercase text-slate-900">D. Dimensi Profil Lulusan Pembelajaran</h3>
          <div className="paper-table-container">
            <table className="paper-table mt-1.5">
              <thead>
                <tr>
                  <th className="w-1/3">Dimensi Profil Lulusan</th>
                  <th>Implementasi pada Pembelajaran Bab Ini</th>
                </tr>
              </thead>
              <tbody>
                {activeDimensions.map((dim, i) => (
                  <tr key={`${dim}-${i}`}>
                    <td className="font-bold">{dim}</td>
                    <td>
                      Dikembangkan melalui aktivitas diskusi, eksplorasi konsep {selectedChapter?.judul_bab},
                      dan refleksi pemecahan masalah.
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="space-y-3 border-t-2 border-slate-800 pt-3">
          <h3 className="text-sm font-extrabold uppercase text-slate-900">DESAIN PEMBELAJARAN</h3>

          <div className="paper-table-container">
            <table className="paper-table">
              <tbody>
                <tr>
                  <th className="w-1/3 text-left">A. Capaian Pembelajaran (CP)</th>
                  <td>
                    <strong>Elemen {selectedChapter?.elemen_cp || officialElements[0]?.nama_elemen}:</strong>{' '}
                    {officialElements[0]?.deskripsi_cp}
                  </td>
                </tr>
                <tr>
                  <th className="text-left">B. Lintas Disiplin Ilmu</th>
                  <td>{effectiveLintasDisiplin}</td>
                </tr>
                <tr>
                  <th className="text-left">C. Tujuan Pembelajaran (TP)</th>
                  <td>
                    <ol className="list-decimal pl-4 space-y-1">
                      {activeTps.map((tp, idx) => (
                        <li key={`${tp.code}-${idx}`}>
                          <strong>Pertemuan {idx + 1} [{tp.code}]:</strong> {tp.deskripsi} ({tp.alokasi_jp} JP)
                        </li>
                      ))}
                    </ol>
                  </td>
                </tr>
                <tr>
                  <th className="text-left">D. Topik Pembelajaran Kontekstual</th>
                  <td>{effectiveTopikKontekstual}</td>
                </tr>
                <tr>
                  <th className="text-left">E. Kerangka Pembelajaran</th>
                  <td>
                    <p>
                      <strong>Model Pedagogis:</strong> {modelPembelajaran}
                    </p>
                    <p className="mt-1">
                      <strong>Pertanyaan Pemantik:</strong> {effectivePemantik.join(' | ')}
                    </p>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div>
            <h4 className="font-extrabold uppercase text-slate-900">
              F. Langkah-Langkah Pembelajaran Berdiferensiasi (Pendekatan Deep Learning 3M)
            </h4>
            {activeTps.map((tp, idx) => (
              <div key={`step-${tp.code}-${idx}`} className="paper-table-container">
                <table className="paper-table mt-2">
                  <thead>
                    <tr>
                      <th colSpan={2} className="text-left">
                        PERTEMUAN {idx + 1} — Fokus TP: [{tp.code}] {tp.deskripsi} ({tp.alokasi_jp} JP)
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="w-1/4 font-bold">1. Kegiatan Pendahuluan (15%)</td>
                      <td>
                        Guru membuka kelas dengan salam, doa, presensi, apersepsi mengaitkan pengalaman nyata
                        siswa dengan topik {selectedChapter?.judul_bab}, serta menyampaikan pertanyaan
                        pemantik: <em>&ldquo;{effectivePemantik[idx % effectivePemantik.length]}&rdquo;</em>.
                      </td>
                    </tr>
                    <tr>
                      <td className="font-bold">
                        2. Kegiatan Inti — Memahami, Mengaplikasi, Merefleksi (70%)
                      </td>
                      <td>
                        <ul className="list-disc pl-4 space-y-1">
                          <li>
                            <strong>Memahami (Mindful Learning):</strong> Peserta didik mengeksplorasi konsep
                            dan literatur terkait {tp.deskripsi}.
                          </li>
                          <li>
                            <strong>Mengaplikasi (Meaningful Learning):</strong> Peserta didik bekerja dalam
                            kelompok mengerjakan studi kasus / LKPD tentang {selectedChapter?.judul_bab}.
                          </li>
                          <li>
                            <strong>Merefleksi (Joyful Learning):</strong> Kelompok mempresentasikan hasil
                            karya dan melakukan evaluasi pemahaman bersama guru.
                          </li>
                        </ul>
                      </td>
                    </tr>
                    <tr>
                      <td className="font-bold">3. Kegiatan Penutup (15%)</td>
                      <td>
                        Peserta didik bersama guru menyimpulkan poin penting pertemuan {idx + 1}, melakukan
                        refleksi singkat, dan menerima informasi materi pertemuan berikutnya.
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            ))}
          </div>

          {includeAsesmen && (
            <div>
              <h4 className="font-extrabold uppercase text-slate-900">
                G. Asesmen Pembelajaran &amp; Butir Soal
              </h4>
              <div className="paper-table-container">
                <table className="paper-table mt-1.5">
                  <thead>
                    <tr>
                      <th className="w-1/4">Jenis Asesmen</th>
                      <th>Teknik &amp; Butir Soal Instrumen</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="font-bold">1. Asesmen Awal (Diagnostik)</td>
                      <td>
                        <p className="font-semibold">Soal Asesmen Awal:</p>
                        <ol className="list-decimal pl-4">
                          {effectiveSoalAwal.map((s, i) => (
                            <li key={`awal-${i}`}>{s}</li>
                          ))}
                        </ol>
                      </td>
                    </tr>
                    <tr>
                      <td className="font-bold">2. Asesmen Proses (Formatif)</td>
                      <td>
                        <p className="font-semibold">Soal / Tugas Asesmen Proses:</p>
                        <ol className="list-decimal pl-4">
                          {effectiveSoalProses.map((s, i) => (
                            <li key={`proses-${i}`}>{s}</li>
                          ))}
                        </ol>
                      </td>
                    </tr>
                    <tr>
                      <td className="font-bold">3. Asesmen Akhir (Sumatif)</td>
                      <td>
                        <p className="font-semibold">Soal Asesmen Akhir Bab:</p>
                        <ol className="list-decimal pl-4">
                          {effectiveSoalAkhir.map((s, i) => (
                            <li key={`akhir-${i}`}>{s}</li>
                          ))}
                        </ol>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {includeLkpd && (
            <div data-page-break="before" className="pt-1">
              <div className="text-center mb-3">
                <h4 className="text-sm font-extrabold uppercase text-slate-900">
                  {customOverrides.judul_lkpd ||
                    selectedChapter?.modul_ajar_template?.lampiran?.lkpd?.judul_lkpd ||
                    'LAMPIRAN 1: LEMBAR KERJA PESERTA DIDIK (LKPD)'}
                </h4>
                <p className="text-xs font-bold text-slate-700">
                  {customOverrides.tujuan_lkpd ||
                    selectedChapter?.modul_ajar_template?.lampiran?.lkpd?.tujuan_aktivitas ||
                    `Materi: ${selectedChapter?.judul_bab || 'Materi Pokok'} — Pendekatan Deep Learning 3M`}
                </p>
              </div>

              <div className="paper-table-container">
                <table className="paper-table">
                  <tbody>
                    <tr>
                      <th className="w-1/4 text-left">Nama Kelompok / Kelas</th>
                      <td>........................................................... / Kelas {kelas}</td>
                      <th className="w-1/4 text-left">Hari, Tanggal</th>
                      <td>...........................................................</td>
                    </tr>
                    <tr>
                      <th className="text-left">Nama Anggota</th>
                      <td colSpan={3}>
                        1. ........................................................... 2. ...........................................................
                        <br />
                        3. ........................................................... 4. ...........................................................
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="mt-3 space-y-2">
                <p className="font-bold text-slate-900">Petunjuk Pengerjaan:</p>
                {petunjukLkpdLines.length > 0 ? (
                  <ol className="list-decimal pl-4 space-y-1 text-[11px] text-slate-700">
                    {petunjukLkpdLines.map((line, idx) => (
                      <li key={`petunjuk-${idx}`}>{line.replace(/^\d+[\.\)]\s*/, '')}</li>
                    ))}
                  </ol>
                ) : (
                  <ol className="list-decimal pl-4 space-y-1 text-[11px] text-slate-700">
                    <li>Berdoalah sebelum memulai kegiatan bersama anggota kelompok Anda.</li>
                    <li>Bacalah dengan cermat setiap instruksi pemecahan masalah dan bahan ajar yang diberikan.</li>
                    <li>Bekerjasamalah secara aktif dan selesaikan tugas-tugas di bawah ini dengan tepat waktu.</li>
                  </ol>
                )}
              </div>

              <div className="paper-table-container mt-3">
                <table className="paper-table">
                  <thead>
                    <tr>
                      <th className="w-12 text-center">No</th>
                      <th className="w-1/3">Tahap Aktivitas (3M)</th>
                      <th>Instruksi Tugas &amp; Lembar Kerja Siswa</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="text-center font-bold">1</td>
                      <td className="font-bold">
                        Memahami
                        <br />
                        <span className="text-[10px] font-normal text-slate-500">(Eksplorasi Konsep)</span>
                      </td>
                      <td>
                        {customOverrides.tugas_lkpd_memahami ||
                          customOverrides.langkah_inti_memahami?.[0] ||
                          selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.memahami ||
                          `Pahamilah konsep dasar mengenai ${selectedChapter?.judul_bab || selectedSubject?.nama_mapel}. Tuliskan intisari pengertian dan prinsip utamanya pada lembar ini!`}
                        <div className="mt-2 h-14 border border-dashed border-slate-300 rounded p-1.5 text-[10px] text-slate-400 italic">
                          [Ruang Jawaban / Intisari Pemahaman Konsep Siswa]
                        </div>
                      </td>
                    </tr>
                    <tr>
                      <td className="text-center font-bold">2</td>
                      <td className="font-bold">
                        Mengaplikasi
                        <br />
                        <span className="text-[10px] font-normal text-slate-500">(Investigasi &amp; Praktik)</span>
                      </td>
                      <td>
                        {customOverrides.tugas_lkpd_mengaplikasi ||
                          customOverrides.langkah_inti_mengaplikasi?.[0] ||
                          selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.mengaplikasi ||
                          `Diskusikan bersama kelompok studi kasus kontekstual penerapan ${selectedChapter?.judul_bab}. Temukan solusi dan langkah-langkah pemecahannya secara logis!`}
                        <div className="mt-2 h-16 border border-dashed border-slate-300 rounded p-1.5 text-[10px] text-slate-400 italic">
                          [Ruang Analisis &amp; Sketsa Solusi Pemecahan Masalah]
                        </div>
                      </td>
                    </tr>
                    <tr>
                      <td className="text-center font-bold">3</td>
                      <td className="font-bold">
                        Merefleksi
                        <br />
                        <span className="text-[10px] font-normal text-slate-500">(Kesimpulan &amp; Evaluasi)</span>
                      </td>
                      <td>
                        {customOverrides.tugas_lkpd_merefleksi ||
                          customOverrides.langkah_inti_merefleksi?.[0] ||
                          selectedChapter?.modul_ajar_template?.pembelajaran_mendalam_3m?.merefleksi ||
                          'Simpulkan manfaat pembelajaran hari ini dan hal apa yang masih perlu diperdalam pada pertemuan selanjutnya!'}
                        <div className="mt-2 h-12 border border-dashed border-slate-300 rounded p-1.5 text-[10px] text-slate-400 italic">
                          [Ruang Refleksi Diri &amp; Kesimpulan Bersama]
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {includeRubrik && (
            <div data-page-break="before" className="pt-1">
              <div className="text-center mb-3">
                <h4 className="text-sm font-extrabold uppercase text-slate-900">
                  LAMPIRAN 2: RUBRIK PENILAIAN 8 DIMENSI PROFIL LULUSAN
                </h4>
                <p className="text-xs font-bold text-slate-700">
                  Standar Kompetensi Lulusan sesuai Permendikdasmen No. 10 Tahun 2025
                </p>
              </div>

              <div className="paper-table-container">
                <table className="paper-table text-[10.5px]">
                  <thead>
                    <tr>
                      <th className="w-8 text-center">No</th>
                      <th className="w-1/4">Dimensi Profil Lulusan</th>
                      <th>Indikator Perilaku Amatan di Kelas</th>
                      <th className="w-12 text-center">MB</th>
                      <th className="w-12 text-center">B</th>
                      <th className="w-12 text-center">BSH</th>
                      <th className="w-12 text-center">SB</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeDplList.map((dpl, idx) => (
                      <tr key={dpl.no || `dpl-${idx}`}>
                        <td className="text-center font-bold">{idx + 1}</td>
                        <td>
                          <p className="font-bold text-slate-900">{dpl.nama_dimensi}</p>
                        </td>
                        <td>{dpl.indikator}</td>
                        <td className="text-center font-mono text-[11px] text-slate-400">[ &nbsp; ]</td>
                        <td className="text-center font-mono text-[11px] text-slate-400">[ &nbsp; ]</td>
                        <td className="text-center font-mono text-[11px] text-slate-400">[ &nbsp; ]</td>
                        <td className="text-center font-mono text-[11px] text-slate-400">[ &nbsp; ]</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-2 space-y-1 text-[10px] text-slate-500 italic">
                <p>
                  * Keterangan Skala: MB = Mulai Berkembang (Skor 1), B = Berkembang (Skor 2), BSH = Berkembang
                  Sesuai Harapan (Skor 3), SB = Sangat Berkembang (Skor 4).
                </p>
                <p className="text-slate-600 font-medium">
                  Catatan / Rekomendasi Guru: ........................................................................................................................................
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (serviceId === '05_prota') {
    const totalTahunJp =
      allSubjectChapters.reduce(
        (acc, b) => acc + (b.id === selectedChapter?.id ? currentAlokasiJp : b.alokasi_jp),
        0
      ) + (customOverrides.cadangan_jp ?? 0);

    return (
      <div className="mt-5 space-y-5 text-xs leading-relaxed">
        <div className="text-center">
          <h2 className="text-base font-extrabold uppercase text-slate-900">PROGRAM TAHUNAN (PROTA)</h2>
          <p className="font-bold uppercase text-slate-700">
            MATA PELAJARAN {selectedSubject?.nama_mapel.toUpperCase()} — KELAS {kelas} ({faseLabel}) TAHUN AJARAN
            2025/2026
          </p>
        </div>

        <div>
          <h3 className="font-extrabold uppercase text-slate-900">
            CAPAIAN PEMBELAJARAN FASE {faseCode} BERDASARKAN ELEMEN
          </h3>
          <div className="paper-table-container">
            <table className="paper-table mt-1.5">
              <thead>
                <tr>
                  <th className="w-1/4">Elemen</th>
                  <th>Capaian Pembelajaran</th>
                </tr>
              </thead>
              <tbody>
                {activeCpElements.map((el, i) => (
                  <tr key={el.kode_elemen || `prota-cp-${i}`}>
                    <td className="font-bold">{el.nama_elemen}</td>
                    <td>{el.deskripsi_cp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h3 className="font-extrabold uppercase text-slate-900">
            DISTRIBUSI ALOKASI WAKTU TAHUNAN (SEMESTER 1 &amp; SEMESTER 2)
          </h3>
          <div className="paper-table-container">
            <table className="paper-table mt-1.5">
              <thead>
                <tr>
                  <th className="w-24 text-center">SEMESTER</th>
                  <th className="w-12 text-center">NO</th>
                  <th>MATERI POKOK / JUDUL BAB &amp; TUJUAN PEMBELAJARAN</th>
                  <th className="w-24 text-center">ALOKASI (JP)</th>
                  <th className="w-28 text-center">KETERANGAN</th>
                </tr>
              </thead>
              <tbody>
                {allSubjectChapters.map((bab, idx) => {
                  const isCurrent = bab.id === selectedChapter?.id;
                  const babJp = isCurrent ? currentAlokasiJp : bab.alokasi_jp;
                  const babTps = isCurrent ? activeTps : bab.tujuan_pembelajaran;
                  return (
                    <tr key={bab.id}>
                      <td className="text-center font-bold">SEMESTER {bab.semester}</td>
                      <td className="text-center font-bold">{idx + 1}</td>
                      <td>
                        <p className="font-bold">
                          Bab {bab.nomor_bab}: {bab.judul_bab}
                        </p>
                        <ul className="mt-1 list-disc pl-4 text-[11px] text-slate-700">
                          {babTps.map((t, i) => (
                            <li key={`${t.code}-${i}`}>
                              [{t.code}] {t.deskripsi} ({t.alokasi_jp} JP)
                            </li>
                          ))}
                        </ul>
                      </td>
                      <td className="text-center font-bold">{babJp} JP</td>
                      <td className="text-center">{Math.max(1, Math.round(babJp / jpPerMinggu))} Pertemuan</td>
                    </tr>
                  );
                })}
                <tr>
                  <td colSpan={3} className="text-right font-bold">
                    Cadangan Jam Pelajaran
                  </td>
                  <td className="text-center font-bold">{customOverrides.cadangan_jp ?? 0} JP</td>
                  <td className="text-center">Pengayaan / STS / SAS</td>
                </tr>
                <tr className="bg-slate-100">
                  <td colSpan={3} className="text-right font-extrabold">
                    Jumlah Jam Pelajaran Tahunan
                  </td>
                  <td className="text-center font-extrabold">{totalTahunJp} JP</td>
                  <td className="text-center font-bold">1 Tahun Ajaran</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  if (serviceId === '06_promes') {
    return (
      <div className="mt-5 space-y-5 text-xs leading-relaxed">
        <div className="text-center">
          <h2 className="text-base font-extrabold uppercase text-slate-900">
            PROGRAM SEMESTER (PROMES) — SEMESTER {semester} ({semester === 1 ? 'GANJIL' : 'GENAP'})
          </h2>
          <p className="font-bold uppercase text-slate-700">
            MATA PELAJARAN {selectedSubject?.nama_mapel.toUpperCase()} — KELAS {kelas} ({faseLabel}) TAHUN AJARAN
            2025/2026
          </p>
        </div>

        <div>
          <h3 className="font-extrabold uppercase text-slate-900">
            CAPAIAN PEMBELAJARAN FASE {faseCode} BERDASARKAN ELEMEN
          </h3>
          <div className="paper-table-container">
            <table className="paper-table mt-1.5">
              <thead>
                <tr>
                  <th className="w-1/4">Elemen</th>
                  <th>Capaian Pembelajaran</th>
                </tr>
              </thead>
              <tbody>
                {activeCpElements.map((el, i) => (
                  <tr key={el.kode_elemen || `promes-cp-${i}`}>
                    <td className="font-bold">{el.nama_elemen}</td>
                    <td>{el.deskripsi_cp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="paper-table-container">
          <h3 className="font-extrabold uppercase text-slate-900">
            MATRIKS DISTRIBUSI MINGGU EFEKTIF SEMESTER {semester}
          </h3>
          <table className="paper-table mt-1.5">
            <thead>
              <tr>
                <th className="w-10 text-center">NO</th>
                <th>BAB / TUJUAN PEMBELAJARAN (TP)</th>
                <th className="w-14 text-center">JP</th>
                {monthLabels.map((m) => (
                  <th key={m} className="w-12 text-center">
                    {m}
                  </th>
                ))}
                <th className="w-20 text-center">KET</th>
              </tr>
            </thead>
            <tbody>
              {currentSemesterChapters.map((bab, bIdx) => {
                const isCurrent = bab.id === selectedChapter?.id;
                const babTps = isCurrent ? activeTps : bab.tujuan_pembelajaran;
                const babJp = isCurrent ? currentAlokasiJp : bab.alokasi_jp;
                return (
                  <React.Fragment key={bab.id}>
                    <tr className="bg-slate-100 font-bold">
                      <td className="text-center">{bIdx + 1}</td>
                      <td>
                        BAB {bab.nomor_bab}: {bab.judul_bab.toUpperCase()}
                      </td>
                      <td className="text-center">{babJp}</td>
                      {monthLabels.map((m) => (
                        <td key={m} className="text-center" />
                      ))}
                      <td className="text-center">Intrakurikuler</td>
                    </tr>
                    {babTps.map((tp, tIdx) => {
                      const targetMonthIdx = (bIdx * 2 + tIdx) % 6;
                      return (
                        <tr key={`${bab.id}-${tp.code}-${tIdx}`}>
                          <td className="text-center text-slate-500">
                            {bIdx + 1}.{tIdx + 1}
                          </td>
                          <td>
                            <strong>[{tp.code}]</strong> {tp.deskripsi}
                          </td>
                          <td className="text-center font-semibold">{tp.alokasi_jp}</td>
                          {monthLabels.map((m, mIdx) => (
                            <td
                              key={m}
                              className={`text-center font-bold ${
                                mIdx === targetMonthIdx ? 'bg-blue-50 text-blue-800' : 'text-slate-300'
                              }`}
                            >
                              {mIdx === targetMonthIdx ? tp.alokasi_jp : '-'}
                            </td>
                          ))}
                          <td className="text-center text-[11px]">TM</td>
                        </tr>
                      );
                    })}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (serviceId === '07_kktp') {
    return (
      <div className="mt-5 space-y-5 text-xs leading-relaxed">
        <div className="text-center">
          <h2 className="text-base font-extrabold uppercase text-slate-900">
            KRITERIA KETERCAPAIAN TUJUAN PEMBELAJARAN (KKTP)
          </h2>
          <p className="font-bold uppercase text-slate-700">
            MATA PELAJARAN {selectedSubject?.nama_mapel.toUpperCase()} — FASE {selectedSubject?.fase} (KELAS{' '}
            {selectedSubject?.kelas})
          </p>
        </div>

        <div>
          <h3 className="font-extrabold uppercase text-slate-900">Identitas Dokumen</h3>
          <div className="paper-table-container">
            <table className="paper-table mt-1.5">
              <tbody>
                <tr>
                  <th className="w-1/3 text-left">Mata Pelajaran</th>
                  <td>{selectedSubject?.nama_mapel}</td>
                </tr>
                <tr>
                  <th className="text-left">Jenjang / Kelas / Fase</th>
                  <td>
                    {selectedSubject?.jenjang} / Kelas {selectedSubject?.kelas} / Fase {selectedSubject?.fase}
                  </td>
                </tr>
                <tr>
                  <th className="text-left">Semester / Tahun Ajaran</th>
                  <td>Semester {semester} / 2025/2026</td>
                </tr>
                <tr>
                  <th className="text-left">Materi / Bab</th>
                  <td>{selectedChapter?.judul_bab || 'Semua Bab'}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h3 className="font-extrabold uppercase text-slate-900">
            A. Skala Interval Nilai KKTP (4 Interval — PPA Revisi 2025)
          </h3>
          <div className="paper-table-container">
            <table className="paper-table mt-1.5">
              <thead>
                <tr>
                  <th className="w-24 text-center">Interval</th>
                  <th className="w-40 text-left">Kriteria</th>
                  <th className="text-left">Tindak Lanjut / Intervensi</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="text-center font-bold">0 - 40%</td>
                  <td>Belum Mencapai</td>
                  <td>Remedial di seluruh bagian</td>
                </tr>
                <tr>
                  <td className="text-center font-bold">41 - 65%</td>
                  <td>Belum Mencapai Ketuntasan</td>
                  <td>Remedial di bagian yang diperlukan</td>
                </tr>
                <tr>
                  <td className="text-center font-bold">66 - 85%</td>
                  <td>Sudah Mencapai Ketuntasan</td>
                  <td>Tidak perlu remedial</td>
                </tr>
                <tr>
                  <td className="text-center font-bold">86 - 100%</td>
                  <td>Sudah Mencapai Ketuntasan</td>
                  <td>Perlu pengayaan atau tantangan lebih</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h3 className="font-extrabold uppercase text-slate-900">
            B. Rubrik Ketercapaian Tujuan Pembelajaran (TP)
          </h3>
          <div className="paper-table-container">
            <table className="paper-table mt-1.5">
              <thead>
                <tr>
                  <th className="w-20 text-center">Kode TP</th>
                  <th className="text-left">Tujuan Pembelajaran &amp; Indikator Ketercapaian</th>
                  <th className="w-16 text-center">JP</th>
                </tr>
              </thead>
              <tbody>
                {activeTps.map((tp, idx) => (
                  <tr key={`${tp.code}-${idx}`}>
                    <td className="text-center font-bold">{tp.code}</td>
                    <td>{tp.deskripsi}</td>
                    <td className="text-center">{tp.alokasi_jp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  return null;
};
