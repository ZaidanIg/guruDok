import React, { useState, useEffect } from 'react';
import { UserCheck, ShieldCheck, X, ArrowRight, AlertCircle } from 'lucide-react';
import { PaperSize, TeacherProfile } from '../../types';

interface SchoolProfileModalProps {
  isOpen: boolean;
  initialProfile: TeacherProfile;
  onClose: () => void;
  onSave: (profile: TeacherProfile) => Promise<void>;
}

export const SchoolProfileModal: React.FC<SchoolProfileModalProps> = ({
  isOpen,
  initialProfile,
  onClose,
  onSave,
}) => {
  const [form, setForm] = useState<TeacherProfile>(initialProfile);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setForm(initialProfile);
    setError(null);
  }, [initialProfile, isOpen]);

  if (!isOpen) return null;

  const validateAndSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Client-side Zero-Trust Pre-Validation
    if (/<[^>]+>/.test(form.nama_guru) || /<[^>]+>/.test(form.nama_sekolah)) {
      setError('Tag HTML atau script tidak diizinkan pada kolom formulir.');
      return;
    }

    const cleanNipGuru = form.nip_guru.trim().replace(/[\s.]/g, '') || '-';
    if (!/^(\d{18}|\d{16}|-)$/.test(cleanNipGuru)) {
      setError("NIP Guru harus 18 digit angka, NUPTK 16 digit, atau isi tanda '-' untuk honorer/swasta.");
      return;
    }

    const cleanNipKasek = form.nip_kepala_sekolah.trim().replace(/[\s.]/g, '') || '-';
    if (!/^(\d{18}|\d{16}|-)$/.test(cleanNipKasek)) {
      setError("NIP Kepala Sekolah harus 18 digit angka, 16 digit, atau isi tanda '-'.");
      return;
    }

    const cleanPhone = form.no_whatsapp.trim().replace(/[\s\-()]/g, '');
    if (!/^(\+62|62|0)8[1-9][0-9]{7,11}$/.test(cleanPhone)) {
      setError('Format Nomor WhatsApp tidak valid. Gunakan format 081234567890.');
      return;
    }

    setIsSaving(true);
    try {
      await onSave({
        ...form,
        nip_guru: cleanNipGuru,
        nip_kepala_sekolah: cleanNipKasek,
        no_whatsapp: cleanPhone,
      });
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Gagal menyimpan profil guru.';
      setError(msg);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-md">
      <div className="clay-card relative max-h-[92vh] w-full max-w-xl overflow-y-auto p-6 sm:p-8">
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Tutup Modal"
          className="clay-btn-white absolute right-5 top-5 flex h-8 w-8 items-center justify-center rounded-full"
        >
          <X className="h-4 w-4 text-slate-600" />
        </button>

        {/* Modal Header */}
        <div className="flex items-start gap-3.5 pr-8">
          <div className="clay-icon-blue flex h-11 w-11 shrink-0 items-center justify-center rounded-full">
            <UserCheck className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-extrabold text-slate-900 sm:text-xl">
              Lengkapi Profil Sekolah Anda
            </h3>
            <p className="mt-0.5 text-xs font-medium text-slate-500">
              Data ini otomatis mengisi{' '}
              <span className="font-extrabold text-slate-800">KOP SURAT</span> dan{' '}
              <span className="font-extrabold text-slate-800">LEMBAR PENGESAHAN</span> pada
              semua dokumen.
            </p>
          </div>
        </div>

        {error && (
          <div className="mt-4 flex items-center gap-2.5 rounded-2xl border border-red-200 bg-red-50 px-4 py-2.5 text-xs font-bold text-red-700">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
            <span>{error}</span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={validateAndSubmit} className="mt-5 space-y-3.5">
          {/* 1. Nama Lengkap Guru */}
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">
              Nama Lengkap Guru (dengan Gelar) <span className="text-blue-600">*</span>
            </label>
            <input
              type="text"
              required
              value={form.nama_guru}
              onChange={(e) => setForm({ ...form, nama_guru: e.target.value })}
              placeholder="Contoh: Siti Aminah, S.Pd."
              className="clay-input w-full px-4 py-2.5 text-sm font-semibold text-slate-800"
            />
          </div>

          {/* 2. NIP / NUPTK & No WhatsApp */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">
                NIP / NUPTK Guru{' '}
                <span className="font-normal text-slate-400">(Isi '-' jika honorer)</span>{' '}
                <span className="text-blue-600">*</span>
              </label>
              <input
                type="text"
                required
                value={form.nip_guru}
                onChange={(e) => setForm({ ...form, nip_guru: e.target.value })}
                placeholder="198805122014022003 atau -"
                className="clay-input w-full px-4 py-2.5 text-sm font-semibold text-slate-800"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">
                No. WhatsApp Aktif <span className="text-blue-600">*</span>
              </label>
              <input
                type="tel"
                required
                value={form.no_whatsapp}
                onChange={(e) => setForm({ ...form, no_whatsapp: e.target.value })}
                placeholder="081234567890"
                className="clay-input w-full px-4 py-2.5 text-sm font-semibold text-slate-800"
              />
            </div>
          </div>

          {/* 3. Nama Sekolah & NPSN */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-12">
            <div className="sm:col-span-8">
              <label className="mb-1 block text-xs font-bold text-slate-700">
                Nama Sekolah / Madrasah <span className="text-blue-600">*</span>
              </label>
              <input
                type="text"
                required
                value={form.nama_sekolah}
                onChange={(e) => setForm({ ...form, nama_sekolah: e.target.value })}
                placeholder="SMP Negeri 1 Surabaya"
                className="clay-input w-full px-4 py-2.5 text-sm font-semibold text-slate-800"
              />
            </div>

            <div className="sm:col-span-4">
              <label className="mb-1 block text-xs font-bold text-slate-700">
                NPSN <span className="font-normal text-slate-400">(Opsional)</span>
              </label>
              <input
                type="text"
                value={form.npsn || ''}
                onChange={(e) => setForm({ ...form, npsn: e.target.value })}
                placeholder="20531234"
                className="clay-input w-full px-4 py-2.5 text-sm font-semibold text-slate-800"
              />
            </div>
          </div>

          {/* 4. Kabupaten/Kota & Provinsi */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">
                Kabupaten / Kota <span className="text-blue-600">*</span>
              </label>
              <input
                type="text"
                required
                value={form.kabupaten_kota}
                onChange={(e) => setForm({ ...form, kabupaten_kota: e.target.value })}
                placeholder="Kota Surabaya"
                className="clay-input w-full px-4 py-2.5 text-sm font-semibold text-slate-800"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">
                Provinsi <span className="text-blue-600">*</span>
              </label>
              <input
                type="text"
                required
                value={form.provinsi}
                onChange={(e) => setForm({ ...form, provinsi: e.target.value })}
                placeholder="Jawa Timur"
                className="clay-input w-full px-4 py-2.5 text-sm font-semibold text-slate-800"
              />
            </div>
          </div>

          {/* 5. Nama Kepala Sekolah */}
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">
              Nama Kepala Sekolah (dengan Gelar) <span className="text-blue-600">*</span>
            </label>
            <input
              type="text"
              required
              value={form.nama_kepala_sekolah}
              onChange={(e) => setForm({ ...form, nama_kepala_sekolah: e.target.value })}
              placeholder="Drs. H. Bambang Irawan, M.Pd."
              className="clay-input w-full px-4 py-2.5 text-sm font-semibold text-slate-800"
            />
          </div>

          {/* 6. NIP Kepala Sekolah & Ukuran Kertas Cetak */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">
                NIP Kepala Sekolah <span className="text-blue-600">*</span>
              </label>
              <input
                type="text"
                required
                value={form.nip_kepala_sekolah}
                onChange={(e) =>
                  setForm({ ...form, nip_kepala_sekolah: e.target.value })
                }
                placeholder="196904151995121002 atau -"
                className="clay-input w-full px-4 py-2.5 text-sm font-semibold text-slate-800"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">
                Ukuran Kertas Cetak <span className="text-blue-600">*</span>
              </label>
              <div className="clay-input grid grid-cols-2 gap-1.5 p-1">
                {(['F4', 'A4'] as PaperSize[]).map((sz) => {
                  const active = form.ukuran_kertas_default === sz;
                  return (
                    <button
                      key={sz}
                      type="button"
                      onClick={() => setForm({ ...form, ukuran_kertas_default: sz })}
                      className={`flex items-center justify-center gap-1.5 rounded-xl py-1.5 text-xs font-extrabold transition-all ${
                        active ? 'clay-btn-primary' : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      <span
                        className={`h-2 w-2 rounded-full ${
                          active ? 'bg-white' : 'border border-slate-400'
                        }`}
                      />
                      <span>{sz === 'F4' ? 'F4/Folio' : 'A4'}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Safety Green Banner */}
          <div className="flex items-center gap-2.5 rounded-2xl border border-emerald-200/80 bg-emerald-50/90 px-4 py-2.5 text-xs font-bold text-emerald-800">
            <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-600" />
            <span>
              Tenang, data sekolah Anda tersimpan aman dan tidak perlu diketik ulang.
            </span>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={onClose}
              className="clay-btn-white px-6 py-2.5 text-xs font-extrabold text-slate-700 sm:text-sm"
            >
              Batal
            </button>

            <button
              type="submit"
              disabled={isSaving}
              className="clay-btn-primary inline-flex items-center gap-2 px-6 py-2.5 text-xs font-extrabold sm:text-sm"
            >
              <span>{isSaving ? 'Menyimpan...' : 'Simpan Profil Guru'}</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
