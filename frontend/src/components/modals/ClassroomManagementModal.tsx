import React, { useState, useEffect } from 'react';
import {
  X,
  Users,
  Plus,
  Trash2,
  FileSpreadsheet,
  Download,
  ArrowUpDown,
  Edit2,
  Check,
  AlertCircle,
  GraduationCap,
  Save,
} from 'lucide-react';
import {
  ClassroomRombel,
  StudentItem,
  getClassrooms,
  saveClassroom,
  deleteClassroom,
  getActiveClassroomId,
  setActiveClassroomId,
  clearAllClassrooms,
  sortStudents,
} from '../../services/classroomStorage';
import { apiClient } from '../../services/api';
import { ExcelUploadModal } from './ExcelUploadModal';

interface ClassroomManagementModalProps {
  isOpen: boolean;
  onClose: () => void;
  onClassroomSelected?: (classroom: ClassroomRombel) => void;
}

export const ClassroomManagementModal: React.FC<ClassroomManagementModalProps> = ({
  isOpen,
  onClose,
  onClassroomSelected,
}) => {
  const [classrooms, setClassrooms] = useState<ClassroomRombel[]>([]);
  const [activeId, setActiveId] = useState<string>('');
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isCreatingRombel, setIsCreatingRombel] = useState(false);
  const [editingStudentId, setEditingStudentId] = useState<string | null>(null);

  // New Rombel Form State
  const [newRombelName, setNewRombelName] = useState('');
  const [newRombelJenjang, setNewRombelJenjang] = useState<'SD' | 'SMP' | 'SMA'>('SD');
  const [newRombelKelas, setNewRombelKelas] = useState(4);
  const [newRombelTahun, setNewRombelTahun] = useState('2026/2027');
  const [newRombelWali, setNewRombelWali] = useState('');

  // Add Manual Student Form State
  const [isAddingStudent, setIsAddingStudent] = useState(false);
  const [manualName, setManualName] = useState('');
  const [manualNisn, setManualNisn] = useState('');
  const [manualGender, setManualGender] = useState<'L' | 'P'>('L');

  // Inline Edit State
  const [editName, setEditName] = useState('');
  const [editNisn, setEditNisn] = useState('');
  const [editGender, setEditGender] = useState<'L' | 'P'>('L');

  const [notification, setNotification] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const loadData = () => {
    const list = getClassrooms();
    setClassrooms(list);
    const active = getActiveClassroomId();
    if (active && list.some((c) => c.id === active)) {
      setActiveId(active);
    } else if (list.length > 0) {
      setActiveId(list[0].id);
      setActiveClassroomId(list[0].id);
    } else {
      setActiveId('');
    }
  };

  if (!isOpen) return null;

  const activeRombel = classrooms.find((c) => c.id === activeId);

  const showNotice = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 3000);
  };

  const handleCreateRombel = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRombelName.trim()) return;

    const newClass: ClassroomRombel = {
      id: `rombel-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      nama_rombel: newRombelName.trim(),
      jenjang: newRombelJenjang,
      tingkat_kelas: Number(newRombelKelas),
      tahun_ajaran: newRombelTahun.trim() || '2026/2027',
      wali_kelas: newRombelWali.trim() || '-',
      students: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    saveClassroom(newClass);
    setActiveId(newClass.id);
    setActiveClassroomId(newClass.id);
    setIsCreatingRombel(false);
    setNewRombelName('');
    setNewRombelWali('');
    loadData();
    showNotice(`Rombel "${newClass.nama_rombel}" berhasil dibuat!`);
  };

  const handleDeleteActiveRombel = () => {
    if (!activeRombel) return;
    if (confirm(`Yakin ingin menghapus rombel "${activeRombel.nama_rombel}" beserta seluruh data siswanya?`)) {
      deleteClassroom(activeRombel.id);
      loadData();
      showNotice('Rombel berhasil dihapus.');
    }
  };

  const handleClearAll = () => {
    if (confirm('PERINGATAN: Tindakan ini akan menghapus SELURUH data rombel dan siswa dari browser ini. Lanjutkan?')) {
      clearAllClassrooms();
      loadData();
      showNotice('Seluruh data kelas telah dibersihkan.');
    }
  };

  const handleAddManualStudent = (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeRombel || !manualName.trim()) return;

    const newStudent: StudentItem = {
      id: `std-${Date.now()}`,
      nomor_absen: activeRombel.students.length + 1,
      nisn: manualNisn.trim() || '-',
      nama_lengkap: manualName.trim(),
      jenis_kelamin: manualGender,
    };

    const updated = {
      ...activeRombel,
      students: [...activeRombel.students, newStudent],
    };

    saveClassroom(updated);
    setManualName('');
    setManualNisn('');
    setManualGender('L');
    setIsAddingStudent(false);
    loadData();
    showNotice(`Siswa "${newStudent.nama_lengkap}" berhasil ditambahkan.`);
  };

  const handleStartEditStudent = (s: StudentItem) => {
    setEditingStudentId(s.id);
    setEditName(s.nama_lengkap);
    setEditNisn(s.nisn);
    setEditGender(s.jenis_kelamin);
  };

  const handleSaveEditStudent = (studentId: string) => {
    if (!activeRombel) return;
    const updatedStudents = activeRombel.students.map((s) => {
      if (s.id === studentId) {
        return {
          ...s,
          nama_lengkap: editName.trim() || s.nama_lengkap,
          nisn: editNisn.trim() || '-',
          jenis_kelamin: editGender,
        };
      }
      return s;
    });

    saveClassroom({
      ...activeRombel,
      students: updatedStudents,
    });

    setEditingStudentId(null);
    loadData();
  };

  const handleDeleteStudent = (studentId: string) => {
    if (!activeRombel) return;
    const filtered = activeRombel.students.filter((s) => s.id !== studentId);
    filtered.forEach((s, idx) => {
      s.nomor_absen = idx + 1;
    });

    saveClassroom({
      ...activeRombel,
      students: filtered,
    });

    loadData();
    showNotice('Siswa berhasil dihapus.');
  };

  const handleSort = (sortBy: 'absen' | 'nama') => {
    if (!activeRombel) return;
    sortStudents(activeRombel.id, sortBy);
    loadData();
    showNotice(`Daftar siswa diurutkan berdasarkan ${sortBy === 'nama' ? 'abjad nama' : 'nomor absen'}.`);
  };

  const countL = activeRombel?.students.filter((s) => s.jenis_kelamin === 'L').length || 0;
  const countP = activeRombel?.students.filter((s) => s.jenis_kelamin === 'P').length || 0;

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in overflow-y-auto">
        <div className="relative w-full max-w-4xl bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden my-6 flex flex-col max-h-[92vh]">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex-shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-teal-500/10 text-teal-600 flex items-center justify-center font-bold">
                <Users className="w-5 h-5 text-teal-600" />
              </div>
              <div>
                <h3 className="font-bold text-slate-800 text-lg">Data Kelas</h3>
              </div>
            </div>
            <button
              onClick={onClose}
              className="w-9 h-9 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Toast Notification */}
          {notification && (
            <div className="px-6 py-2 bg-teal-500 text-white text-xs font-medium flex items-center justify-between animate-fade-in">
              <span>{notification}</span>
              <button onClick={() => setNotification(null)} className="text-white/80 hover:text-white">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Rombel Tabs Bar */}
          <div className="px-6 py-3 border-b border-slate-100 bg-white flex items-center gap-2 overflow-x-auto flex-shrink-0">
            {classrooms.map((c) => (
              <button
                key={c.id}
                onClick={() => {
                  setActiveId(c.id);
                  setActiveClassroomId(c.id);
                  if (onClassroomSelected) onClassroomSelected(c);
                }}
                className={`px-4 py-2 rounded-2xl font-semibold text-xs whitespace-nowrap transition-all flex items-center gap-2 ${
                  activeId === c.id
                    ? 'bg-teal-600 text-white shadow-md shadow-teal-500/20'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
                }`}
              >
                <GraduationCap className="w-3.5 h-3.5" />
                <span>{c.nama_rombel}</span>
                <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-black/10 font-mono">
                  {c.students.length}
                </span>
              </button>
            ))}

            <button
              onClick={() => setIsCreatingRombel(!isCreatingRombel)}
              className="px-3.5 py-2 rounded-2xl border border-dashed border-teal-400 text-teal-600 hover:bg-teal-50 font-semibold text-xs whitespace-nowrap flex items-center gap-1.5 transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Tambah Rombel</span>
            </button>
          </div>

          {/* Create Rombel Inline Form */}
          {isCreatingRombel && (
            <form
              onSubmit={handleCreateRombel}
              className="p-4 bg-teal-50/50 border-b border-teal-100 flex-shrink-0 animate-fade-in space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-teal-900">Buat Rombel / Kelas Baru:</span>
                <button
                  type="button"
                  onClick={() => setIsCreatingRombel(false)}
                  className="text-xs text-teal-700 hover:underline"
                >
                  Batal
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-5 gap-2.5 text-xs">
                <div>
                  <label className="text-[10px] font-semibold text-slate-500 block mb-1">Nama Rombel</label>
                  <input
                    type="text"
                    required
                    placeholder="Contoh: Kelas 4-B"
                    value={newRombelName}
                    onChange={(e) => setNewRombelName(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-semibold text-slate-500 block mb-1">Jenjang</label>
                  <select
                    value={newRombelJenjang}
                    onChange={(e) => setNewRombelJenjang(e.target.value as any)}
                    className="w-full px-3 py-1.5 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="SD">SD</option>
                    <option value="SMP">SMP</option>
                    <option value="SMA">SMA</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-semibold text-slate-500 block mb-1">Tingkat Kelas</label>
                  <input
                    type="number"
                    min={1}
                    max={12}
                    value={newRombelKelas}
                    onChange={(e) => setNewRombelKelas(Number(e.target.value))}
                    className="w-full px-3 py-1.5 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-semibold text-slate-500 block mb-1">Wali Kelas</label>
                  <input
                    type="text"
                    placeholder="Nama Wali Kelas"
                    value={newRombelWali}
                    onChange={(e) => setNewRombelWali(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
                <div className="flex items-end">
                  <button
                    type="submit"
                    className="w-full py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs shadow-md shadow-teal-500/20"
                  >
                    Simpan Rombel
                  </button>
                </div>
              </div>
            </form>
          )}

          {/* Active Rombel Content */}
          {activeRombel ? (
            <div className="flex-1 overflow-y-auto p-6 space-y-5">
              {/* Rombel Summary & Action Bar */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 bg-slate-50 rounded-2xl border border-slate-100">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-bold text-slate-800 text-base">{activeRombel.nama_rombel}</h4>
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-teal-100 text-teal-700">
                      {activeRombel.jenjang} Kelas {activeRombel.tingkat_kelas}
                    </span>
                    <span className="text-xs text-slate-400">T.A {activeRombel.tahun_ajaran}</span>
                  </div>
                  <p className="text-xs text-slate-500">
                    Wali Kelas: <strong className="text-slate-700">{activeRombel.wali_kelas}</strong> · Total Siswa:{' '}
                    <strong className="text-slate-700">{activeRombel.students.length}</strong> (L: {countL}, P:{' '}
                    {countP})
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
                  <button
                    onClick={() => setIsUploadModalOpen(true)}
                    className="px-3.5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs shadow-sm flex items-center gap-1.5 transition-all"
                  >
                    <FileSpreadsheet className="w-3.5 h-3.5" />
                    <span>Upload Excel</span>
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        await apiClient.downloadStudentTemplate();
                      } catch (err: any) {
                        alert(err?.message || 'Gagal download template');
                      }
                    }}
                    className="px-3 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-100 text-slate-700 font-semibold text-xs flex items-center gap-1.5 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5 text-slate-500" />
                    <span>Template</span>
                  </button>
                  <button
                    onClick={() => setIsAddingStudent(!isAddingStudent)}
                    className="px-3 py-2 rounded-xl border border-teal-200 bg-teal-50 hover:bg-teal-100 text-teal-700 font-semibold text-xs flex items-center gap-1.5 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Tambah Siswa</span>
                  </button>
                </div>
              </div>

              {/* Add Student Manual Inline Form */}
              {isAddingStudent && (
                <form
                  onSubmit={handleAddManualStudent}
                  className="p-3.5 bg-slate-50/90 rounded-2xl border border-slate-200 animate-fade-in flex flex-col sm:flex-row items-end gap-2 text-xs"
                >
                  <div className="flex-1 w-full">
                    <label className="text-[10px] font-semibold text-slate-500 block mb-1">Nama Lengkap Siswa</label>
                    <input
                      type="text"
                      required
                      placeholder="Contoh: Muhammad Ilham"
                      value={manualName}
                      onChange={(e) => setManualName(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                  <div className="w-full sm:w-36">
                    <label className="text-[10px] font-semibold text-slate-500 block mb-1">NISN / NIS</label>
                    <input
                      type="text"
                      placeholder="Contoh: 0081234567"
                      value={manualNisn}
                      onChange={(e) => setManualNisn(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                  <div className="w-full sm:w-28">
                    <label className="text-[10px] font-semibold text-slate-500 block mb-1">Jenis Kelamin</label>
                    <select
                      value={manualGender}
                      onChange={(e) => setManualGender(e.target.value as any)}
                      className="w-full px-3 py-1.5 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                    >
                      <option value="L">L (Laki-laki)</option>
                      <option value="P">P (Perempuan)</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-1.5 w-full sm:w-auto">
                    <button
                      type="submit"
                      className="px-4 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs shadow-sm"
                    >
                      Simpan
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsAddingStudent(false)}
                      className="px-3 py-1.5 rounded-xl text-slate-500 hover:bg-slate-200 text-xs"
                    >
                      Batal
                    </button>
                  </div>
                </form>
              )}

              {/* Student Table */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-700">Daftar Peserta Didik:</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleSort('absen')}
                      className="px-2.5 py-1 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 text-[11px] font-medium flex items-center gap-1"
                    >
                      <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      Urut Absen
                    </button>
                    <button
                      onClick={() => handleSort('nama')}
                      className="px-2.5 py-1 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 text-[11px] font-medium flex items-center gap-1"
                    >
                      <ArrowUpDown className="w-3 h-3 text-slate-400" />
                      Urut Abjad
                    </button>
                  </div>
                </div>

                {activeRombel.students.length === 0 ? (
                  <div className="p-8 text-center bg-slate-50 rounded-2xl border border-slate-100">
                    <Users className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                    <p className="font-semibold text-slate-600 text-xs">Belum ada siswa di rombel ini</p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      Gunakan tombol "Upload Excel" untuk impor cepat, atau "Tambah Siswa" untuk input manual.
                    </p>
                  </div>
                ) : (
                  <div className="border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-slate-100/90 text-slate-700 font-semibold">
                        <tr>
                          <th className="px-3.5 py-2.5 w-14 text-center">No</th>
                          <th className="px-3.5 py-2.5 w-32">NISN</th>
                          <th className="px-3.5 py-2.5">Nama Lengkap</th>
                          <th className="px-3.5 py-2.5 w-20 text-center">L/P</th>
                          <th className="px-3.5 py-2.5 w-24 text-center">Aksi</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-slate-800">
                        {activeRombel.students.map((st) => (
                          <tr key={st.id} className="hover:bg-slate-50/70 transition-colors">
                            {editingStudentId === st.id ? (
                              <>
                                <td className="px-3.5 py-2 text-center text-slate-500 font-mono">
                                  {st.nomor_absen}
                                </td>
                                <td className="px-3.5 py-2">
                                  <input
                                    type="text"
                                    value={editNisn}
                                    onChange={(e) => setEditNisn(e.target.value)}
                                    className="w-full px-2 py-1 rounded border border-slate-300 font-mono text-xs"
                                  />
                                </td>
                                <td className="px-3.5 py-2">
                                  <input
                                    type="text"
                                    value={editName}
                                    onChange={(e) => setEditName(e.target.value)}
                                    className="w-full px-2 py-1 rounded border border-slate-300 text-xs font-medium"
                                  />
                                </td>
                                <td className="px-3.5 py-2 text-center">
                                  <select
                                    value={editGender}
                                    onChange={(e) => setEditGender(e.target.value as any)}
                                    className="px-1.5 py-1 rounded border border-slate-300 text-xs"
                                  >
                                    <option value="L">L</option>
                                    <option value="P">P</option>
                                  </select>
                                </td>
                                <td className="px-3.5 py-2 text-center">
                                  <div className="flex items-center justify-center gap-1">
                                    <button
                                      onClick={() => handleSaveEditStudent(st.id)}
                                      className="p-1 rounded text-teal-600 hover:bg-teal-50"
                                      title="Simpan"
                                    >
                                      <Check className="w-4 h-4" />
                                    </button>
                                    <button
                                      onClick={() => setEditingStudentId(null)}
                                      className="p-1 rounded text-slate-400 hover:bg-slate-100"
                                      title="Batal"
                                    >
                                      <X className="w-4 h-4" />
                                    </button>
                                  </div>
                                </td>
                              </>
                            ) : (
                              <>
                                <td className="px-3.5 py-2 text-center text-slate-500 font-mono">
                                  {st.nomor_absen}
                                </td>
                                <td className="px-3.5 py-2 font-mono text-slate-600">{st.nisn}</td>
                                <td className="px-3.5 py-2 font-medium">{st.nama_lengkap}</td>
                                <td className="px-3.5 py-2 text-center">
                                  <span
                                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                      st.jenis_kelamin === 'L'
                                        ? 'bg-sky-100 text-sky-700'
                                        : 'bg-pink-100 text-pink-700'
                                    }`}
                                  >
                                    {st.jenis_kelamin}
                                  </span>
                                </td>
                                <td className="px-3.5 py-2 text-center">
                                  <div className="flex items-center justify-center gap-1.5 text-slate-400">
                                    <button
                                      onClick={() => handleStartEditStudent(st)}
                                      className="p-1 rounded hover:text-teal-600 hover:bg-slate-100 transition-colors"
                                      title="Edit Siswa"
                                    >
                                      <Edit2 className="w-3.5 h-3.5" />
                                    </button>
                                    <button
                                      onClick={() => handleDeleteStudent(st.id)}
                                      className="p-1 rounded hover:text-rose-600 hover:bg-slate-100 transition-colors"
                                      title="Hapus Siswa"
                                    >
                                      <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                  </div>
                                </td>
                              </>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-slate-400 space-y-3">
              <Users className="w-12 h-12 mx-auto text-slate-300" />
              <p className="font-semibold text-slate-600 text-sm">Belum Ada Rombel yang Dibuat</p>
              <button
                onClick={() => setIsCreatingRombel(true)}
                className="px-5 py-2 rounded-2xl bg-teal-600 text-white font-semibold text-xs shadow-md shadow-teal-500/20"
              >
                + Buat Rombel Pertama
              </button>
            </div>
          )}

          {/* Footer Bar */}
          <div className="px-6 py-4 border-t border-slate-100 bg-slate-50/50 flex flex-wrap items-center justify-between gap-3 flex-shrink-0">
            <div className="flex items-center gap-2">
              {activeRombel && (
                <button
                  onClick={handleDeleteActiveRombel}
                  className="px-3.5 py-2 rounded-xl text-rose-600 hover:bg-rose-50 text-xs font-semibold inline-flex items-center gap-1.5 transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  Hapus Rombel Ini
                </button>
              )}
              <button
                onClick={handleClearAll}
                className="px-3 py-2 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-slate-100 text-[11px] font-medium transition-colors"
              >
                Bersihkan Semua Data
              </button>
            </div>

            <button
              onClick={onClose}
              className="px-6 py-2.5 rounded-2xl bg-slate-800 hover:bg-slate-900 text-white font-semibold text-xs shadow-md shadow-slate-900/10 transition-all"
            >
              Selesai & Tutup
            </button>
          </div>
        </div>
      </div>

      {/* Nested Upload Modal */}
      {activeRombel && (
        <ExcelUploadModal
          isOpen={isUploadModalOpen}
          classroomId={activeRombel.id}
          classroomName={activeRombel.nama_rombel}
          onClose={() => setIsUploadModalOpen(false)}
          onSuccess={() => {
            loadData();
            showNotice('Data siswa dari Excel berhasil diimpor!');
          }}
        />
      )}
    </>
  );
};
