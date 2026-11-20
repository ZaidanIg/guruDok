import React, { useEffect, useRef, useState } from 'react';
import { BookOpen, UserCheck, LogIn, LogOut, ChevronDown, School, Users } from 'lucide-react';
import { AuthUser, TeacherProfile } from '../../types';

interface NavbarProps {
  teacher: TeacherProfile;
  authUser?: AuthUser | null;
  activeSection: 'home' | 'katalog' | 'generator' | 'riwayat';
  onNavigate: (section: 'home' | 'katalog' | 'generator' | 'riwayat') => void;
  onOpenProfileModal: () => void;
  onOpenClassroomModal?: () => void;
  onOpenLoginModal?: () => void;
  onLogout?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  teacher,
  authUser,
  activeSection,
  onNavigate,
  onOpenProfileModal,
  onOpenClassroomModal,
  onOpenLoginModal,
  onLogout,
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const displayName =
    authUser?.full_name || teacher.nama_guru || 'Akun & Profil';
  const displaySub =
    teacher.nama_sekolah || (authUser ? authUser.email : 'Atur KOP & Masuk');

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

        {/* Right Unified Profile Dropdown (KOP Sekolah + Sign In Biru + Logout Merah) */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setIsDropdownOpen((prev) => !prev)}
            className="clay-btn-white flex items-center gap-2.5 px-3 py-1.5 text-left"
            aria-expanded={isDropdownOpen}
            aria-haspopup="true"
          >
            {authUser?.avatar_url ? (
              <img
                src={authUser.avatar_url}
                alt={authUser.full_name}
                className="h-7 w-7 shrink-0 rounded-full object-cover"
              />
            ) : (
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-blue-50 text-blue-700">
                <UserCheck className="h-4 w-4" />
              </div>
            )}

            <div className="hidden max-w-[160px] pr-1 sm:block">
              <p className="truncate text-xs font-bold leading-tight text-slate-900">
                {displayName}
              </p>
              <p className="truncate text-[11px] font-medium text-slate-500">
                {displaySub}
              </p>
            </div>
            <span className="text-xs font-bold text-slate-700 sm:hidden">Profil</span>
            <ChevronDown
              className={`h-4 w-4 text-slate-500 transition-transform duration-200 ${
                isDropdownOpen ? 'rotate-180' : ''
              }`}
            />
          </button>

          {isDropdownOpen && (
            <div className="clay-card absolute right-0 z-50 mt-2 w-72 p-3 shadow-xl">
              {/* Header Status Akun Google */}
              <div className="border-b border-slate-100 pb-2.5">
                {authUser ? (
                  <div className="flex items-center gap-2.5">
                    {authUser.avatar_url ? (
                      <img
                        src={authUser.avatar_url}
                        alt={authUser.full_name}
                        className="h-9 w-9 rounded-full object-cover"
                      />
                    ) : (
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-700 text-xs font-bold text-white">
                        {authUser.full_name.slice(0, 1).toUpperCase()}
                      </div>
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-extrabold text-slate-900">
                        {authUser.full_name}
                      </p>
                      <p className="truncate text-[11px] font-medium text-slate-500">
                        {authUser.email}
                      </p>
                    </div>
                  </div>
                ) : (
                  <p className="text-[11px] font-semibold text-slate-500">
                    Belum masuk akun Google (opsional hingga unduh dokumen).
                  </p>
                )}
              </div>

              {/* Menu Item: Profil KOP Sekolah */}
              <div className="py-1">
                <button
                  type="button"
                  onClick={() => {
                    setIsDropdownOpen(false);
                    onOpenProfileModal();
                  }}
                  className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left transition hover:bg-slate-100"
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
                    <School className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-bold text-slate-800">
                      Profil KOP Sekolah
                    </p>
                    <p className="truncate text-[11px] font-medium text-slate-500">
                      {teacher.nama_sekolah
                        ? `${teacher.nama_guru || 'Guru'} • ${teacher.nama_sekolah}`
                        : 'Belum diisi (Opsional)'}
                    </p>
                  </div>
                </button>
              </div>

              {/* Menu Item: Data Kelas & Siswa */}
              <div className="py-1">
                <button
                  type="button"
                  onClick={() => {
                    setIsDropdownOpen(false);
                    if (onOpenClassroomModal) onOpenClassroomModal();
                  }}
                  className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left transition hover:bg-slate-100"
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-teal-50 text-teal-700">
                    <Users className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-bold text-slate-800">
                      Data Kelas & Siswa
                    </p>
                    <p className="truncate text-[11px] font-medium text-slate-500">
                      Kelola Rombel & Upload Excel
                    </p>
                  </div>
                </button>
              </div>

              {/* Tombol Sign In (Biru) & Logout (Merah) */}
              <div className="space-y-2 border-t border-slate-100 pt-2.5">
                {!authUser && onOpenLoginModal && (
                  <button
                    type="button"
                    onClick={() => {
                      setIsDropdownOpen(false);
                      onOpenLoginModal();
                    }}
                    className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-700 px-4 py-2.5 text-xs font-bold text-white shadow-sm transition hover:bg-blue-800"
                  >
                    <LogIn className="h-4 w-4" />
                    <span>Sign In dengan Google</span>
                  </button>
                )}

                {authUser && onLogout && (
                  <button
                    type="button"
                    onClick={() => {
                      setIsDropdownOpen(false);
                      onLogout();
                    }}
                    className="flex w-full items-center justify-center gap-2 rounded-xl bg-red-600 px-4 py-2.5 text-xs font-bold text-white shadow-sm transition hover:bg-red-700"
                  >
                    <LogOut className="h-4 w-4" />
                    <span>Logout</span>
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
