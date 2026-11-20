import React, { useState, useRef } from 'react';
import { X, UploadCloud, FileSpreadsheet, CheckCircle2, AlertTriangle, ArrowRight, Download, RefreshCw } from 'lucide-react';
import { apiClient } from '../../services/api';
import { addStudentsToClassroom } from '../../services/classroomStorage';

interface ExcelUploadModalProps {
  isOpen: boolean;
  classroomId: string;
  classroomName: string;
  onClose: () => void;
  onSuccess: () => void;
}

interface ParsedStudent {
  nomor_absen: number;
  nisn: string;
  nama_lengkap: string;
  jenis_kelamin: 'L' | 'P';
}

export const ExcelUploadModal: React.FC<ExcelUploadModalProps> = ({
  isOpen,
  classroomId,
  classroomName,
  onClose,
  onSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [parsedStudents, setParsedStudents] = useState<ParsedStudent[] | null>(null);
  const [detectedHeaderRow, setDetectedHeaderRow] = useState<number>(1);
  const [importMode, setImportMode] = useState<'replace' | 'append'>('replace');
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileSelect = (selectedFile: File) => {
    setError(null);
    if (!selectedFile.name.toLowerCase().endsWith('.xlsx')) {
      setError('Hanya file Excel (.xlsx) yang didukung.');
      return;
    }
    if (selectedFile.size > 2 * 1024 * 1024) {
      setError('Ukuran file melebihi batas 2 MB.');
      return;
    }
    setFile(selectedFile);
    setParsedStudents(null);
  };

  const handleProcessFile = async () => {
    if (!file) {
      setError('Silakan pilih file Excel terlebih dahulu.');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const result = await apiClient.parseClassroomExcel(file);
      if (result.students.length === 0) {
        setError('Tidak ada data siswa yang berhasil dibaca. Pastikan kolom Nama terisi.');
        setIsProcessing(false);
        return;
      }
      setParsedStudents(result.students);
      setDetectedHeaderRow(result.detected_header_row);
    } catch (err: any) {
      setError(err?.message || 'Gagal memproses file Excel.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApplyToClassroom = () => {
    if (!parsedStudents || parsedStudents.length === 0) return;

    addStudentsToClassroom(
      classroomId,
      parsedStudents.map((s) => ({
        nomor_absen: s.nomor_absen,
        nisn: s.nisn,
        nama_lengkap: s.nama_lengkap,
        jenis_kelamin: s.jenis_kelamin,
      })),
      importMode === 'replace'
    );

    onSuccess();
    onClose();
  };

  const handleDownloadTemplate = async () => {
    try {
      await apiClient.downloadStudentTemplate();
    } catch (err: any) {
      setError(err?.message || 'Gagal mengunduh template Excel.');
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden my-8">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-teal-500/10 text-teal-600 flex items-center justify-center font-bold">
              <FileSpreadsheet className="w-5 h-5 text-teal-600" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800 text-lg">Upload Excel Siswa</h3>
              <p className="text-xs text-slate-500">
                Impor ke rombel: <span className="font-semibold text-teal-600">{classroomName}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-9 h-9 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5">
          {error && (
            <div className="p-3.5 bg-rose-50 border border-rose-100 rounded-2xl flex items-start gap-3 text-rose-600 text-sm">
              <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {!parsedStudents ? (
            <>
              {/* Dropzone */}
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setIsDragging(false);
                  if (e.dataTransfer.files?.[0]) {
                    handleFileSelect(e.dataTransfer.files[0]);
                  }
                }}
                onClick={() => fileInputRef.current?.click()}
                className={`relative border-2 border-dashed rounded-3xl p-8 text-center cursor-pointer transition-all duration-200 ${
                  isDragging
                    ? 'border-teal-500 bg-teal-50/50 scale-[0.99]'
                    : file
                    ? 'border-teal-400 bg-slate-50/80'
                    : 'border-slate-200 hover:border-teal-400 bg-slate-50/40'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      handleFileSelect(e.target.files[0]);
                    }
                  }}
                />

                <div className="w-14 h-14 mx-auto mb-3 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center shadow-inner">
                  <UploadCloud className="w-7 h-7" />
                </div>

                {file ? (
                  <div className="space-y-1">
                    <p className="font-semibold text-slate-800 text-sm">{file.name}</p>
                    <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB — Siap diproses</p>
                    <span className="inline-block mt-2 text-xs text-teal-600 font-medium hover:underline">
                      Klik untuk mengganti file
                    </span>
                  </div>
                ) : (
                  <div className="space-y-1">
                    <p className="font-medium text-slate-700 text-sm">
                      Seret & lepas file Excel (.xlsx) di sini, atau <span className="text-teal-600 font-semibold">pilih file</span>
                    </p>
                    <p className="text-xs text-slate-400">
                      Sistem cerdas otomatis mendeteksi kolom Nama, NISN, dan Jenis Kelamin (Maks. 2 MB)
                    </p>
                  </div>
                )}
              </div>

              {/* Template Download Prompt */}
              <div className="flex items-center justify-between p-3.5 bg-slate-50 rounded-2xl border border-slate-100 text-xs">
                <div className="flex items-center gap-2 text-slate-600">
                  <FileSpreadsheet className="w-4 h-4 text-teal-600" />
                  <span>Belum punya format Excel siswa?</span>
                </div>
                <button
                  type="button"
                  onClick={handleDownloadTemplate}
                  className="inline-flex items-center gap-1.5 font-semibold text-teal-600 hover:text-teal-700 hover:underline"
                >
                  <Download className="w-3.5 h-3.5" />
                  Unduh Format Resmi
                </button>
              </div>

              {/* Action */}
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-5 py-2.5 rounded-2xl text-slate-600 hover:bg-slate-100 font-semibold text-sm transition-colors"
                >
                  Batal
                </button>
                <button
                  type="button"
                  disabled={!file || isProcessing}
                  onClick={handleProcessFile}
                  className="px-6 py-2.5 rounded-2xl bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-semibold text-sm shadow-md shadow-teal-500/20 inline-flex items-center gap-2 transition-all"
                >
                  {isProcessing ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Memproses...
                    </>
                  ) : (
                    <>
                      Proses & Pratinjau
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </>
          ) : (
            /* Parsed Preview View */
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3.5 bg-teal-50/70 border border-teal-100 rounded-2xl text-xs text-teal-900">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-teal-600" />
                  <span>
                    Berhasil mendeteksi <strong>{parsedStudents.length} siswa</strong> (Header di baris {detectedHeaderRow}).
                  </span>
                </div>
                <button
                  onClick={() => {
                    setParsedStudents(null);
                    setFile(null);
                  }}
                  className="font-medium text-teal-700 hover:underline inline-flex items-center gap-1"
                >
                  <RefreshCw className="w-3 h-3" />
                  Pilih file lain
                </button>
              </div>

              {/* Preview Table */}
              <div className="border border-slate-200 rounded-2xl overflow-hidden max-h-56 overflow-y-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100 text-slate-700 sticky top-0">
                    <tr>
                      <th className="px-3 py-2 w-12 text-center">No</th>
                      <th className="px-3 py-2 w-28">NISN / NIS</th>
                      <th className="px-3 py-2">Nama Lengkap</th>
                      <th className="px-3 py-2 w-16 text-center">L/P</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-800">
                    {parsedStudents.slice(0, 10).map((st, i) => (
                      <tr key={i} className="hover:bg-slate-50/60">
                        <td className="px-3 py-1.5 text-center text-slate-500">{st.nomor_absen}</td>
                        <td className="px-3 py-1.5 font-mono text-slate-600">{st.nisn}</td>
                        <td className="px-3 py-1.5 font-medium">{st.nama_lengkap}</td>
                        <td className="px-3 py-1.5 text-center">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              st.jenis_kelamin === 'L' ? 'bg-sky-100 text-sky-700' : 'bg-pink-100 text-pink-700'
                            }`}
                          >
                            {st.jenis_kelamin}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {parsedStudents.length > 10 && (
                <p className="text-right text-[11px] text-slate-400">
                  + {parsedStudents.length - 10} siswa lainnya...
                </p>
              )}

              {/* Import Mode Options */}
              <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-100 space-y-2">
                <p className="text-xs font-semibold text-slate-700">Metode Pengisian Rombel:</p>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <label className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 bg-white cursor-pointer hover:border-teal-400">
                    <input
                      type="radio"
                      name="importMode"
                      value="replace"
                      checked={importMode === 'replace'}
                      onChange={() => setImportMode('replace')}
                      className="text-teal-600 focus:ring-teal-500"
                    />
                    <div>
                      <p className="font-semibold text-slate-800">Ganti Data Rombel</p>
                      <p className="text-[10px] text-slate-400">Menimpa daftar siswa saat ini</p>
                    </div>
                  </label>
                  <label className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200 bg-white cursor-pointer hover:border-teal-400">
                    <input
                      type="radio"
                      name="importMode"
                      value="append"
                      checked={importMode === 'append'}
                      onChange={() => setImportMode('append')}
                      className="text-teal-600 focus:ring-teal-500"
                    />
                    <div>
                      <p className="font-semibold text-slate-800">Tambahkan Siswa</p>
                      <p className="text-[10px] text-slate-400">Sisipkan ke akhir daftar rombel</p>
                    </div>
                  </label>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-5 py-2.5 rounded-2xl text-slate-600 hover:bg-slate-100 font-semibold text-sm transition-colors"
                >
                  Batal
                </button>
                <button
                  type="button"
                  onClick={handleApplyToClassroom}
                  className="px-6 py-2.5 rounded-2xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-sm shadow-md shadow-teal-500/20 inline-flex items-center gap-2 transition-all"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Simpan ke Rombel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
