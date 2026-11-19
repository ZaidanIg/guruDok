import React from 'react';
import { Home, LayoutGrid, History } from 'lucide-react';

interface BottomNavProps {
  activeSection: 'home' | 'katalog' | 'generator' | 'riwayat';
  onNavigate: (section: 'home' | 'katalog' | 'generator' | 'riwayat') => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({ activeSection, onNavigate }) => {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-slate-200 bg-white/95 px-4 py-2 backdrop-blur md:hidden">
      <div className="mx-auto grid max-w-md grid-cols-3 gap-2">
        <button
          type="button"
          onClick={() => onNavigate('home')}
          className={`flex flex-col items-center justify-center gap-1 rounded-lg py-2 text-xs font-bold transition-all ${
            activeSection === 'home'
              ? 'bg-blue-700 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <Home className="h-4 w-4" />
          <span>Home</span>
        </button>

        <button
          type="button"
          onClick={() => onNavigate('katalog')}
          className={`flex flex-col items-center justify-center gap-1 rounded-lg py-2 text-xs font-bold transition-all ${
            activeSection === 'katalog' || activeSection === 'generator'
              ? 'bg-blue-700 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <LayoutGrid className="h-4 w-4" />
          <span>Katalog</span>
        </button>

        <button
          type="button"
          onClick={() => onNavigate('riwayat')}
          className={`flex flex-col items-center justify-center gap-1 rounded-lg py-2 text-xs font-bold transition-all ${
            activeSection === 'riwayat'
              ? 'bg-blue-700 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <History className="h-4 w-4" />
          <span>Riwayat</span>
        </button>
      </div>
    </div>
  );
};
