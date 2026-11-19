import React from 'react';
import { BookOpen, UserCheck, LogOut } from 'lucide-react';
import { AuthUser, TeacherProfile } from '../../types';

interface NavbarProps {
  teacher: TeacherProfile;
  authUser?: AuthUser | null;
  activeSection: 'home' | 'katalog' | 'generator' | 'riwayat';
  onNavigate: (section: 'home' | 'katalog' | 'generator' | 'riwayat') => void;
  onOpenProfileModal: () => void;
  onOpenLoginModal?: () => void;
  onLogout?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  teacher,
  authUser,
  activeSection,
  onNavigate,
  onOpenProfileModal,
  onOpenLoginModal,
  onLogout,
}) => {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        {/* Brand Logo */}
        <button
          type="button"
          onClick={() => onNavigate('home')}
          className="flex items-center gap-2.5 text-left focus:outline-none"
        >
          <div className="clay-icon-blue flex h-9 w-9 items-center justify-center rounded-lg">
            <BookOpen className="h-4 w-4 text-white" />
          </div>
          <div>
            <span className="text-lg font-extrabold tracking-tight text-slate-900">
              GuruDok<span className="text-blue-700">.id</span>
            </span>
            <span className="ml-2 hidden rounded bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-600 lg:inline-block">
              BSKAP 046/2025
            </span>
          </div>
        </button>

        {/* Center 3-Page Navigation (Desktop & Tablet) */}
        <nav className="hidden items-center gap-1 rounded-xl bg-slate-100 p-1 md:flex">
          <button
            type="button"
            onClick={() => onNavigate('home')}
            className={`rounded-lg px-4 py-1.5 text-sm font-semibold transition-all ${
              activeSection === 'home'
                ? 'bg-white text-blue-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Home
          </button>
          <button
            type="button"
            onClick={() => onNavigate('katalog')}
            className={`rounded-lg px-4 py-1.5 text-sm font-semibold transition-all ${
              activeSection === 'katalog' || activeSection === 'generator'
                ? 'bg-white text-blue-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Katalog Layanan
          </button>
          <button
            type="button"
            onClick={() => onNavigate('riwayat')}
            className={`rounded-lg px-4 py-1.5 text-sm font-semibold transition-all ${
              activeSection === 'riwayat'
                ? 'bg-white text-blue-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Riwayat Dokumen
          </button>
        </nav>

        {/* Right Teacher Profile Button */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onOpenProfileModal}
            title="Ubah KOP Sekolah & Profil Guru"
            className="clay-btn-white flex items-center gap-2.5 px-3 py-1.5 text-left"
          >
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-blue-50 text-blue-700">
              <UserCheck className="h-4 w-4" />
            </div>
            <div className="hidden pr-1 sm:block">
              <p className="text-xs font-bold leading-tight text-slate-900">
                {teacher.nama_guru || 'Lengkapi Profil Guru'}
              </p>
              <p className="text-[11px] font-medium text-slate-500">
                {teacher.nama_sekolah || 'Klik untuk isi KOP Sekolah'}
              </p>
            </div>
            <span className="text-xs font-bold text-slate-700 sm:hidden">
              Profil KOP
            </span>
          </button>

          {authUser ? (
            <div className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 py-1 pl-2 pr-1.5">
              {authUser.avatar_url ? (
                <img
                  src={authUser.avatar_url}
                  alt={authUser.full_name}
                  className="h-6 w-6 rounded-full object-cover"
                />
              ) : (
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-700 text-[10px] font-bold text-white">
                  {authUser.full_name.slice(0, 1).toUpperCase()}
                </div>
              )}
              <span className="hidden max-w-[110px] truncate text-xs font-bold text-slate-700 lg:inline">
                {authUser.full_name}
              </span>
              {onLogout && (
                <button
                  type="button"
                  onClick={onLogout}
                  title="Keluar akun Google"
                  className="rounded-full p-1 text-slate-500 transition hover:bg-slate-200 hover:text-slate-800"
                >
                  <LogOut className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          ) : (
            onOpenLoginModal && (
              <button
                type="button"
                onClick={onOpenLoginModal}
                className="clay-btn-primary px-3 py-1.5 text-xs font-bold"
              >
                Masuk Google
              </button>
            )
          )}
        </div>
      </div>
    </header>
  );
};
