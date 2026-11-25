import React from 'react';
import {
  ChapterTopic,
  CurriculumSubject,
  CustomDocumentOverrides,
  ServiceId,
  StudentOverrideItem,
  TeacherProfile,
} from '../../../types';
import { buildDefaultJurnalRows } from '../../curriculum/JurnalEditorSection';
import { buildRaporPreviewData } from '../../curriculum/RaporGradesEditorSection';
import { DEFAULT_KESEPAKATAN_KELAS } from '../../curriculum/AdminKelasEditorSection';
import { SUPERVISI_BUNDLE_ITEMS } from '../../curriculum/SupervisiEditorSection';

export interface ClassroomTrackingPreviewsProps {
  serviceId: ServiceId;
  kelas: number;
  semester: number;
  selectedSubject: CurriculumSubject | null;
  currentSemesterChapters: ChapterTopic[];
  teacher: TeacherProfile;
  activeClassroomRombel?: string;
  effectiveStudents: StudentOverrideItem[];
  customOverrides: CustomDocumentOverrides;
}

const SAMPLE_DAY_NUMBERS = Array.from({ length: 15 }, (_, i) => i + 1);

export const ClassroomTrackingPreviews: React.FC<ClassroomTrackingPreviewsProps> = ({
  serviceId,
  kelas,
  semester,
  selectedSubject,
  currentSemesterChapters,
  teacher,
  activeClassroomRombel,
  effectiveStudents,
  customOverrides,
}) => {
  const rombelLabel = customOverrides.nama_rombel || activeClassroomRombel || `Kelas ${kelas}`;
  const previewStudents = effectiveStudents.slice(0, 15);
  const piketDays = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat'];

  if (serviceId === '02_admin_kelas') {
    const names = effectiveStudents.map((s) => s.nama_lengkap);
    const ketua = customOverrides.ketua_kelas || names[0] || '...................................';
    const wakil = customOverrides.wakil_ketua_kelas || names[1] || '...................................';
    const sekretaris = customOverrides.sekretaris_kelas || names[2] || '...................................';
    const bendahara = customOverrides.bendahara_kelas || names[3] || '...................................';
    const denahMode = customOverrides.denah_duduk || 'Kelompok Kolaboratif';
    const rules =
      customOverrides.kesepakatan_kelas && customOverrides.kesepakatan_kelas.length > 0
        ? customOverrides.kesepakatan_kelas
        : DEFAULT_KESEPAKATAN_KELAS;

    return (
      <div className="mt-5 space-y-4 text-xs leading-relaxed">
        <div data-keep-together="true" className="text-center">
          <h2 className="text-base font-extrabold uppercase text-slate-900">
            PERANGKAT ADMINISTRASI KELAS &amp; MANAJEMEN ROMBEL
          </h2>
          <p className="font-bold uppercase text-slate-700">
            {rombelLabel} | {selectedSubject?.jenjang} KELAS {kelas} | SEMESTER {semester} | WALI KELAS:{' '}
            {customOverrides.wali_kelas || teacher.nama_guru || '...................'}
          </p>
        </div>

        <div data-splittable-table="true" className="paper-table-container">
          <h3 className="mb-1.5 text-xs font-extrabold uppercase text-slate-800">
            A. Struktur Organisasi Kelas
          </h3>
          <table className="paper-table text-[11px]">
            <thead>
              <tr>
                <th className="w-8 text-center">No</th>
                <th className="w-44 text-left">Jabatan</th>
                <th className="text-left">Nama Pejabat / Pengurus</th>
              </tr>
            </thead>
            <tbody>
              {[
                { jabatan: 'Kepala Sekolah', nama: teacher.nama_kepala_sekolah || '...................................' },
                { jabatan: 'Wali Kelas / Pembina', nama: customOverrides.wali_kelas || teacher.nama_guru || '...................................' },
                { jabatan: 'Ketua Kelas', nama: ketua },
                { jabatan: 'Wakil Ketua Kelas', nama: wakil },
                { jabatan: 'Sekretaris Kelas', nama: sekretaris },
                { jabatan: 'Bendahara Kelas', nama: bendahara },
              ].map((row, idx) => (
                <tr key={row.jabatan}>
                  <td className="text-center font-bold">{idx + 1}</td>
                  <td className="font-semibold">{row.jabatan}</td>
                  <td>{row.nama}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div data-splittable-table="true" className="paper-table-container">
          <h3 className="mb-1.5 text-xs font-extrabold uppercase text-slate-800">
            B. Jadwal Piket Kebersihan Kelas &amp; Formasi Denah ({denahMode})
          </h3>
          <table className="paper-table text-[11px]">
            <thead>
              <tr>
                <th className="w-24 text-left">Hari</th>
                <th className="text-left">Petugas Piket Harian</th>
                <th className="w-52 text-left">Tugas Utama</th>
              </tr>
            </thead>
            <tbody>
              {piketDays.map((day, dIdx) => {
                const customList = customOverrides.jadwal_piket?.[day];
                const petugas =
                  customList && customList.length > 0
                    ? customList.join(', ')
                    : names.filter((_, sIdx) => sIdx % piketDays.length === dIdx).slice(0, 4).join(', ') || '-';
                return (
                  <tr key={day}>
                    <td className="font-bold">{day}</td>
                    <td>{petugas}</td>
                    <td>Kebersihan kelas, papan tulis, &amp; kerapian meja</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div data-keep-together="true" className="paper-table-container">
          <h3 className="mb-1.5 text-xs font-extrabold uppercase text-slate-800">
            C. Kesepakatan Kelas ({rules.length} Butir)
          </h3>
          <table className="paper-table text-[11px]">
            <thead>
              <tr>
                <th className="w-8 text-center">No</th>
                <th className="text-left">Butir Kesepakatan Bersama Guru &amp; Peserta Didik</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rText, idx) => (
                <tr key={`prev-rule-${idx}`}>
                  <td className="text-center font-bold">{idx + 1}</td>
                  <td>{rText}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (serviceId === '18_paket_supervisi') {
    const totalJp = currentSemesterChapters.reduce((acc, ch) => acc + (ch.alokasi_jp || 0), 0);
    return (
      <div className="mt-5 space-y-4 text-xs leading-relaxed">
        <div data-keep-together="true" className="text-center border-2 border-slate-800 rounded-lg p-4 bg-slate-50/70">
          <p className="text-[10px] font-bold uppercase tracking-widest text-blue-700">
            DOKUMEN INDUK MASTER BUNDLE (.ZIP &amp; BINDER PDF)
          </p>
          <h2 className="mt-1 text-base font-extrabold uppercase text-slate-900">
            PAKET SIAP SUPERVISI AKADEMIK GURU
          </h2>
          <p className="mt-1 text-xs font-bold text-slate-700">
            {selectedSubject?.nama_mapel} • {rombelLabel} • SEMESTER {semester} • SK MENGAJAR:{' '}
            {customOverrides.nomor_sk_mengajar || '800/SK-PBM/2025'}
          </p>
          <p className="mt-1 text-[11px] text-slate-600">
            Supervisor / Pengawas: <strong>{customOverrides.nama_pengawas || '........................................'}</strong>{' '}
            (NIP: {customOverrides.nip_pengawas || '-'}) • Tgl Supervisi:{' '}
            {customOverrides.tanggal_supervisi || 'Sesuai Jadwal'} • Cakupan: {currentSemesterChapters.length} Bab ({totalJp} JP)
          </p>
        </div>

        <div data-splittable-table="true" className="paper-table-container">
          <h3 className="mb-1.5 text-xs font-extrabold uppercase text-slate-800">
            Daftar Isi Bundel Master ZIP &amp; Instrumen Telaah Supervisi
          </h3>
          <table className="paper-table text-[11px]">
            <thead>
              <tr>
                <th className="w-12 text-center">Kode</th>
                <th className="text-left">Komponen Dokumen Perangkat Pembelajaran</th>
                <th className="w-28 text-center">Format Output</th>
                <th className="w-20 text-center">Status</th>
              </tr>
            </thead>
            <tbody>
              {SUPERVISI_BUNDLE_ITEMS.map((item) => (
                <tr key={item.code}>
                  <td className="text-center font-bold">{item.code}</td>
                  <td className="font-semibold">{item.title}</td>
                  <td className="text-center font-mono text-[10px]">{item.format}</td>
                  <td className="text-center font-bold text-emerald-700">[ ✓ ] Lengkap</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (serviceId === '13_presensi') {
    const bulanLabel = customOverrides.bulan_presensi || 'Agustus';

    return (
      <div className="mt-5 space-y-5 text-xs leading-relaxed">
        <div className="text-center">
          <h2 className="text-base font-extrabold uppercase text-slate-900">
            PRESENSI DAN KEHADIRAN PESERTA DIDIK
          </h2>
          <p className="font-bold uppercase text-slate-700">
            TAHUN AJARAN 2026/2027 — SEMESTER {semester}
          </p>
        </div>

        <div className="paper-table-container">
          <table className="paper-table">
            <tbody>
              <tr>
                <th className="w-1/4 text-left">Mata Pelajaran</th>
                <td className="w-1/4 font-semibold">{selectedSubject?.nama_mapel}</td>
                <th className="w-1/4 text-left">Guru Pengampu</th>
                <td className="w-1/4 font-semibold">{teacher.nama_guru || '-'}</td>
              </tr>
              <tr>
                <th className="text-left">Kelas / Rombel</th>
                <td className="font-semibold">{rombelLabel}</td>
                <th className="text-left">Bulan Presensi</th>
                <td className="font-semibold text-blue-700">{bulanLabel}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="paper-table-container">
          <table className="paper-table text-[11px]">
            <thead>
              <tr>
                <th rowSpan={2} className="w-8 text-center">No</th>
                <th rowSpan={2} className="w-20 text-center">NISN</th>
                <th rowSpan={2} className="text-left min-w-[140px]">Nama Lengkap Siswa</th>
                <th rowSpan={2} className="w-8 text-center">L/P</th>
                <th colSpan={15} className="text-center bg-teal-700 text-white">
                  Tanggal Presensi Bulan {bulanLabel} (Sampel Tgl 1 - 15)
                </th>
                <th colSpan={5} className="text-center bg-teal-800 text-white">
                  Rekapitulasi Kehadiran
                </th>
              </tr>
              <tr>
                {SAMPLE_DAY_NUMBERS.map((dayNum) => (
                  <th key={`day-${dayNum}`} className="w-5 text-center font-mono text-[10px] bg-teal-600 text-white">
                    {dayNum}
                  </th>
                ))}
                <th className="w-7 text-center font-bold bg-teal-700 text-white" title="Hadir (Formula =COUNTIF)">H</th>
                <th className="w-7 text-center font-bold bg-teal-700 text-white" title="Sakit (Formula =COUNTIF)">S</th>
                <th className="w-7 text-center font-bold bg-teal-700 text-white" title="Izin (Formula =COUNTIF)">I</th>
                <th className="w-7 text-center font-bold bg-teal-700 text-white" title="Alpa (Formula =COUNTIF)">A</th>
                <th className="w-10 text-center font-bold bg-teal-800 text-white" title="Persentase Kehadiran">%</th>
              </tr>
            </thead>
            <tbody>
              {previewStudents.map((s, idx) => (
                <tr key={s.nisn || `presensi-${s.nomor_absen || idx + 1}`}>
                  <td className="text-center font-bold">{s.nomor_absen || idx + 1}</td>
                  <td className="text-center font-mono text-[10px] text-slate-500">{s.nisn || '-'}</td>
                  <td className="font-semibold text-slate-900">{s.nama_lengkap}</td>
                  <td className="text-center font-bold">{s.jenis_kelamin || 'L'}</td>
                  {SAMPLE_DAY_NUMBERS.map((dayNum) => (
                    <td key={`cell-${idx}-${dayNum}`} className="text-center font-mono text-[10px] text-teal-800">
                      {(dayNum - 1) % 7 === 5 || (dayNum - 1) % 7 === 6 ? '•' : 'H'}
                    </td>
                  ))}
                  <td className="text-center font-mono font-bold text-teal-700">11</td>
                  <td className="text-center font-mono text-slate-500">0</td>
                  <td className="text-center font-mono text-slate-500">0</td>
                  <td className="text-center font-mono text-slate-500">0</td>
                  <td className="text-center font-mono font-bold text-teal-900 bg-teal-50">100%</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="bg-slate-100 font-bold border-t-2 border-slate-400">
                <td colSpan={4} className="text-right pr-2 uppercase text-[10px]">
                  Total Rekapitulasi Kelas (Formula Excel)
                </td>
                <td colSpan={15} className="text-center text-[10px] text-slate-500 italic">
                  Formula Aktif =COUNTIF(E10:AI10, &quot;H&quot;) per baris
                </td>
                <td className="text-center font-mono font-extrabold text-teal-800">=SUM</td>
                <td className="text-center font-mono font-extrabold text-teal-800">=SUM</td>
                <td className="text-center font-mono font-extrabold text-teal-800">=SUM</td>
                <td className="text-center font-mono font-extrabold text-teal-800">=SUM</td>
                <td className="text-center font-mono font-extrabold text-teal-900 bg-teal-100">=AVERAGE</td>
              </tr>
            </tfoot>
          </table>
        </div>
        <p className="text-[11px] text-slate-500 italic">
          * Dokumen unduhan (.xlsx) mencakup seluruh 31 hari penuh dengan formula aktif live, dapat dibuka dan
          dihitung otomatis di Microsoft Excel maupun Google Sheets.
        </p>
      </div>
    );
  }

  if (serviceId === '14_jurnal_mengajar') {
    const activeDays = customOverrides.hari_mengajar || ['Senin', 'Kamis'];
    const jamStr = customOverrides.jam_mengajar || '1-2';
    const effectiveRows =
      customOverrides.custom_jurnal_rows && customOverrides.custom_jurnal_rows.length > 0
        ? customOverrides.custom_jurnal_rows.map((r, idx) => ({
            ...r,
            no: idx + 1,
          }))
        : buildDefaultJurnalRows({
            kelas,
            semester,
            subjectName: selectedSubject?.nama_mapel,
            semesterChapters: currentSemesterChapters,
            hariMengajar: customOverrides.hari_mengajar,
            tanggalMulaiSemester: customOverrides.tanggal_mulai_semester,
            jamMengajar: customOverrides.jam_mengajar,
            jumlahPertemuan: customOverrides.jumlah_pertemuan_jurnal,
          });

    return (
      <div className="mt-5 space-y-4 text-xs leading-relaxed">
        <div data-keep-together="true" className="text-center">
          <h2 className="text-base font-extrabold uppercase text-slate-900">
            JURNAL MENGAJAR HARIAN DAN AGENDA GURU
          </h2>
          <p className="font-bold uppercase text-slate-700">
            {selectedSubject?.nama_mapel} | {rombelLabel} | SEMESTER {semester}
          </p>
        </div>

        <div data-keep-together="true" className="paper-table-container">
          <table className="paper-table">
            <tbody>
              <tr>
                <th className="w-1/4 text-left">Mata Pelajaran / Rombel</th>
                <td className="w-1/4 font-semibold">
                  {selectedSubject?.nama_mapel} — {rombelLabel}
                </td>
                <th className="w-1/4 text-left">Jadwal Rutin</th>
                <td className="w-1/4 font-semibold">
                  {activeDays.join(', ')} (Jam {jamStr})
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div data-splittable-table="true" className="paper-table-container">
          <table className="paper-table text-[10.5px]">
            <thead>
              <tr>
                <th className="w-8 text-center">No</th>
                <th className="w-28 text-left">Hari / Tanggal</th>
                <th className="w-24 text-center">Jam / Pert.</th>
                <th className="text-left">Tujuan Pembelajaran (TP)</th>
                <th className="w-32 text-left">Materi Pembelajaran</th>
                <th className="w-36 text-left">Ringkasan Kegiatan</th>
                <th className="w-24 text-left">Kehadiran Siswa</th>
                <th className="w-28 text-left">Hambatan &amp; Refleksi</th>
                <th className="w-12 text-center">Paraf</th>
              </tr>
            </thead>
            <tbody>
              {effectiveRows.map((row, idx) => (
                <tr key={`preview-jurnal-${row.no ?? idx + 1}`}>
                  <td className="text-center font-bold">{row.no ?? idx + 1}</td>
                  <td className="font-semibold">{row.hari_tanggal || '-'}</td>
                  <td className="text-center">{row.jam_pertemuan || '-'}</td>
                  <td>{row.tp || '-'}</td>
                  <td className="font-semibold">{row.materi || '-'}</td>
                  <td>{row.kegiatan || '-'}</td>
                  <td>{row.kehadiran || '-'}</td>
                  <td>{row.refleksi || '-'}</td>
                  <td className="text-center">{row.paraf || ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (serviceId === '15_daftar_nilai') {
    const kktpNilai = customOverrides.kktp_nilai || 75;

    return (
      <div className="mt-5 space-y-5 text-xs leading-relaxed">
        <div className="text-center">
          <h2 className="text-base font-extrabold uppercase text-slate-900">
            BUKU DAFTAR NILAI PESERTA DIDIK
          </h2>
          <p className="font-bold uppercase text-slate-700">
            KURIKULUM MERDEKA — TAHUN AJARAN 2026/2027 (SEMESTER {semester})
          </p>
        </div>

        <div className="paper-table-container">
          <table className="paper-table">
            <tbody>
              <tr>
                <th className="w-1/4 text-left">Mata Pelajaran</th>
                <td className="w-1/4 font-semibold">{selectedSubject?.nama_mapel}</td>
                <th className="w-1/4 text-left">Guru Pengampu</th>
                <td className="w-1/4 font-semibold">{teacher.nama_guru || '-'}</td>
              </tr>
              <tr>
                <th className="text-left">Kelas / Rombel</th>
                <td className="font-semibold">{rombelLabel}</td>
                <th className="text-left">KKTP Minimum</th>
                <td className="font-semibold text-blue-700">
                  {kktpNilai} (Tuntas &ge; {kktpNilai})
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="paper-table-container">
          <table className="paper-table text-[11px]">
            <thead>
              <tr>
                <th rowSpan={2} className="w-8 text-center">No</th>
                <th rowSpan={2} className="w-20 text-center">NISN</th>
                <th rowSpan={2} className="text-left min-w-[140px]">Nama Lengkap Siswa</th>
                <th rowSpan={2} className="w-8 text-center">L/P</th>
                <th colSpan={5} className="text-center bg-blue-900 text-white">
                  Asesmen Formatif (Lingkup TP)
                </th>
                <th colSpan={3} className="text-center bg-blue-800 text-white">
                  Asesmen Sumatif
                </th>
                <th colSpan={3} className="text-center bg-teal-800 text-white">
                  Hasil Akhir &amp; Keterangan
                </th>
              </tr>
              <tr>
                <th className="w-10 text-center font-mono text-[10px] bg-blue-800 text-white">TP 1</th>
                <th className="w-10 text-center font-mono text-[10px] bg-blue-800 text-white">TP 2</th>
                <th className="w-10 text-center font-mono text-[10px] bg-blue-800 text-white">TP 3</th>
                <th className="w-10 text-center font-mono text-[10px] bg-blue-800 text-white">TP 4</th>
                <th className="w-12 text-center font-bold font-mono text-[10px] bg-blue-700 text-white" title="=AVERAGE">
                  Rata F
                </th>
                <th className="w-10 text-center font-mono text-[10px] bg-blue-700 text-white">STS</th>
                <th className="w-10 text-center font-mono text-[10px] bg-blue-700 text-white">SAS</th>
                <th className="w-12 text-center font-bold font-mono text-[10px] bg-blue-600 text-white" title="=AVERAGE">
                  Rata S
                </th>
                <th
                  className="w-12 text-center font-bold font-mono text-[10px] bg-teal-700 text-white"
                  title="=ROUND((RataF*50% + RataS*50%),0)"
                >
                  NA
                </th>
                <th className="w-16 text-center font-bold bg-teal-800 text-white" title="=IF(NA>=KKTP)">
                  Status
                </th>
                <th className="min-w-[100px] text-left text-[10px] bg-teal-900 text-white">
                  Capaian Kompetensi
                </th>
              </tr>
            </thead>
            <tbody>
              {previewStudents.map((s, idx) => (
                <tr key={s.nisn || `nilai-${s.nomor_absen || idx + 1}`}>
                  <td className="text-center font-bold">{s.nomor_absen || idx + 1}</td>
                  <td className="text-center font-mono text-[10px] text-slate-500">{s.nisn || '-'}</td>
                  <td className="font-semibold text-slate-900">{s.nama_lengkap}</td>
                  <td className="text-center font-bold">{s.jenis_kelamin || 'L'}</td>
                  <td className="text-center font-mono text-slate-700">85</td>
                  <td className="text-center font-mono text-slate-700">80</td>
                  <td className="text-center font-mono text-slate-700">88</td>
                  <td className="text-center font-mono text-slate-700">82</td>
                  <td className="text-center font-mono font-bold text-blue-800 bg-blue-50">83.8</td>
                  <td className="text-center font-mono text-slate-700">80</td>
                  <td className="text-center font-mono text-slate-700">85</td>
                  <td className="text-center font-mono font-bold text-blue-800 bg-blue-50">82.5</td>
                  <td className="text-center font-mono font-extrabold text-teal-800 bg-teal-50">83</td>
                  <td className="text-center font-bold text-[10px] text-emerald-700 bg-emerald-50">TUNTAS</td>
                  <td className="text-[10px] text-slate-600">Menunjukkan penguasaan optimal</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="bg-slate-100 font-bold border-t border-slate-300">
                <td colSpan={4} className="text-right pr-2 uppercase text-[10px]">
                  Nilai Tertinggi Kelas
                </td>
                <td colSpan={8} className="text-center text-[10px] text-slate-400 italic">
                  Formula Excel Otomatis
                </td>
                <td className="text-center font-mono text-teal-800">=MAX</td>
                <td colSpan={2} className="text-[10px] text-slate-500">
                  Capaian tertinggi rombel
                </td>
              </tr>
              <tr className="bg-slate-100 font-bold">
                <td colSpan={4} className="text-right pr-2 uppercase text-[10px]">
                  Nilai Terendah Kelas
                </td>
                <td colSpan={8} className="text-center text-[10px] text-slate-400 italic">
                  Formula Excel Otomatis
                </td>
                <td className="text-center font-mono text-teal-800">=MIN</td>
                <td colSpan={2} className="text-[10px] text-slate-500">
                  Batas bawah evaluasi
                </td>
              </tr>
              <tr className="bg-slate-100 font-bold">
                <td colSpan={4} className="text-right pr-2 uppercase text-[10px]">
                  Rata-rata Kelas
                </td>
                <td colSpan={8} className="text-center text-[10px] text-slate-400 italic">
                  Formula Excel Otomatis
                </td>
                <td className="text-center font-mono text-teal-800">=AVERAGE</td>
                <td colSpan={2} className="text-[10px] text-slate-500">
                  Mean nilai akhir
                </td>
              </tr>
              <tr className="bg-teal-50 font-bold border-t-2 border-teal-600 text-teal-900">
                <td colSpan={4} className="text-right pr-2 uppercase text-[10px]">
                  Ketuntasan Klasikal (%)
                </td>
                <td colSpan={8} className="text-center text-[10px] text-teal-700 italic">
                  Formula =COUNTIF(Status, &quot;TUNTAS&quot;)/Total
                </td>
                <td colSpan={3} className="text-center font-mono font-extrabold text-teal-900">
                  =ROUND((COUNTIF/COUNT)*100, 1)%
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
        <p className="text-[11px] text-slate-500 italic">
          * Dokumen unduhan (.xlsx) mencakup formula aktif live: rata-rata formatif, pembobotan sumatif (STS/SAS),
          Nilai Akhir (NA), status KKTP, dan statistik kelas.
        </p>
      </div>
    );
  }

  if (serviceId === '16_deskripsi_rapor') {
    const { kktp, rows } = buildRaporPreviewData({
      kelas,
      subjectName: selectedSubject?.nama_mapel,
      semesterChapters: currentSemesterChapters,
      students: effectiveStudents,
      customOverrides,
    });

    return (
      <div className="mt-5 space-y-4 text-xs leading-relaxed">
        <div data-keep-together="true" className="text-center">
          <h2 className="text-base font-extrabold uppercase text-slate-900">
            DESKRIPSI CAPAIAN KOMPETENSI PESERTA DIDIK (e-RAPOR)
          </h2>
          <p className="font-bold uppercase text-slate-700">
            {selectedSubject?.nama_mapel} | {rombelLabel} | SEMESTER {semester} | KKTP: {kktp}
          </p>
        </div>

        <div data-splittable-table="true" className="paper-table-container">
          <table className="paper-table text-[10.5px]">
            <thead>
              <tr>
                <th className="w-8 text-center">No</th>
                <th className="w-20 text-center">NISN</th>
                <th className="w-36 text-left">Nama Peserta Didik</th>
                <th className="w-12 text-center">Nilai</th>
                <th className="text-left">Deskripsi Capaian Tertinggi (e-Rapor)</th>
                <th className="text-left">Deskripsi Perlu Pendampingan (e-Rapor)</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={`rapor16-${row.nisn}-${row.no}-${idx}`}>
                  <td className="text-center font-bold">{row.no}</td>
                  <td className="text-center font-mono text-[10px]">{row.nisn}</td>
                  <td className="font-semibold">{row.nama}</td>
                  <td className="text-center font-bold">{row.nilaiAkhir}</td>
                  <td>{row.deskripsiTinggi}</td>
                  <td>{row.deskripsiBimbingan}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (serviceId === '17_rekap_rapor') {
    const { kktp, wSumatif, wSas, rows } = buildRaporPreviewData({
      kelas,
      subjectName: selectedSubject?.nama_mapel,
      semesterChapters: currentSemesterChapters,
      students: effectiveStudents,
      customOverrides,
    });
    const avgScore = rows.length > 0 ? (rows.reduce((a, b) => a + b.nilaiAkhir, 0) / rows.length).toFixed(1) : '0';

    return (
      <div className="mt-5 space-y-4 text-xs leading-relaxed">
        <div data-keep-together="true" className="text-center">
          <h2 className="text-base font-extrabold uppercase text-slate-900">
            REKAPITULASI NILAI RAPOR FINAL &amp; PERINGKAT KELAS
          </h2>
          <p className="font-bold uppercase text-slate-700">
            {selectedSubject?.nama_mapel} | {rombelLabel} | BOBOT {wSumatif}% SUMATIF : {wSas}% SAS | KKTP: {kktp}
          </p>
        </div>

        <div data-splittable-table="true" className="paper-table-container">
          <table className="paper-table text-[11px]">
            <thead>
              <tr>
                <th className="w-8 text-center">No</th>
                <th className="w-20 text-center">NISN</th>
                <th className="text-left">Nama Peserta Didik</th>
                <th className="w-16 text-center">Sumatif</th>
                <th className="w-14 text-center">SAS</th>
                <th className="w-16 text-center">Nilai Rapor</th>
                <th className="w-16 text-center">Peringkat</th>
                <th className="w-24 text-center">Ketuntasan</th>
                <th className="w-28 text-left">Predikat</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={`rapor17-${row.nisn}-${row.no}-${idx}`}>
                  <td className="text-center font-bold">{row.no}</td>
                  <td className="text-center font-mono text-[10px]">{row.nisn}</td>
                  <td className="font-semibold">{row.nama}</td>
                  <td className="text-center">{row.sumatif}</td>
                  <td className="text-center">{row.sas}</td>
                  <td className="text-center font-extrabold text-blue-800">{row.nilaiAkhir}</td>
                  <td className="text-center font-bold">#{row.peringkat}</td>
                  <td className="text-center font-bold">{row.status}</td>
                  <td>{row.predikat}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="bg-slate-100 font-bold">
                <td colSpan={5} className="text-right pr-2">
                  Rata-rata Nilai Akhir Kelas (=AVERAGE)
                </td>
                <td className="text-center font-extrabold text-blue-800">{avgScore}</td>
                <td colSpan={3} className="text-[10px] text-slate-500">
                  Formula Excel: =ROUND / =RANK / =IF
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    );
  }

  return null;
};
