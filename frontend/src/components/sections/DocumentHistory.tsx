import React, { useEffect, useState } from 'react';
import {
  FileText,
  FileSpreadsheet,
  Download,
  Search,
  PlusCircle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { HistoryDocumentItem } from '../../types';

interface DocumentHistoryProps {
  history: HistoryDocumentItem[];
  onRedownload: (item: HistoryDocumentItem) => void;
  onOpenCatalog: () => void;
}

const ITEMS_PER_PAGE = 10;

export const DocumentHistory: React.FC<DocumentHistoryProps> = ({
  history,
  onRedownload,
  onOpenCatalog,
}) => {
  const [filterJenjang, setFilterJenjang] = useState<string>('ALL');
  const [filterFormat, setFilterFormat] = useState<string>('ALL');
  const [searchFile, setSearchFile] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);

  const filteredItems = history.filter((item) => {
    if (
      filterJenjang !== 'ALL' &&
      item.parameters?.jenjang &&
      item.parameters.jenjang !== filterJenjang
    ) {
      return false;
    }
    if (filterFormat !== 'ALL' && item.file_format.toUpperCase() !== filterFormat) {
      return false;
    }
    if (searchFile.trim()) {
      const q = searchFile.toLowerCase();
      return (
        item.filename.toLowerCase().includes(q) ||
        item.service_name.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const totalPages = Math.max(1, Math.ceil(filteredItems.length / ITEMS_PER_PAGE));
  const safePage = Math.min(currentPage, totalPages);
  const startIndex = (safePage - 1) * ITEMS_PER_PAGE;
  const endIndex = Math.min(startIndex + ITEMS_PER_PAGE, filteredItems.length);
  const paginatedItems = filteredItems.slice(startIndex, endIndex);

  useEffect(() => {
    setCurrentPage(1);
  }, [filterJenjang, filterFormat, searchFile]);

  const formatTimestamp = (ts: string) => {
    if (!ts) return '-';
    if (ts.includes('Nov') || ts.includes(',')) return ts;
    try {
      const d = new Date(ts);
      return d.toLocaleDateString('id-ID', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return ts;
    }
  };

  return (
    <section id="riwayat-section" className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-blue-700">
            Arsip Unduhan
          </p>
          <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl">
            Riwayat Dokumen Administrasi Saya
          </h1>
          <p className="mt-1 text-xs font-medium text-slate-500 sm:text-sm">
            Daftar berkas Word (.docx), Excel (.xlsx), dan PDF (.pdf) yang telah Anda susun.
          </p>
        </div>

        <button
          type="button"
          onClick={onOpenCatalog}
          className="clay-btn-primary inline-flex items-center gap-2 px-4 py-2.5 text-xs font-bold sm:text-sm"
        >
          <PlusCircle className="h-4 w-4" />
          <span>Buat Dokumen Baru</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="clay-card mt-5 p-4">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div className="flex flex-wrap items-center gap-2.5">
            <select
              aria-label="Filter Riwayat Berdasarkan Jenjang"
              value={filterJenjang}
              onChange={(e) => setFilterJenjang(e.target.value)}
              className="clay-input px-3.5 py-2 text-xs font-bold text-slate-700"
            >
              <option value="ALL">Semua Jenjang</option>
              <option value="SD">SD / MI</option>
              <option value="SMP">SMP / MTs</option>
              <option value="SMA">SMA / MA</option>
            </select>

            <select
              aria-label="Filter Riwayat Berdasarkan Format"
              value={filterFormat}
              onChange={(e) => setFilterFormat(e.target.value)}
              className="clay-input px-3.5 py-2 text-xs font-bold text-slate-700"
            >
              <option value="ALL">Semua Format</option>
              <option value="DOCX">Word (.DOCX)</option>
              <option value="XLSX">Excel (.XLSX)</option>
              <option value="PDF">PDF (.PDF)</option>
            </select>
          </div>

          <div className="relative w-full sm:w-72">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchFile}
              onChange={(e) => setSearchFile(e.target.value)}
              placeholder="Cari nama berkas..."
              className="clay-input w-full py-2 pl-9 pr-4 text-xs font-semibold text-slate-700"
            />
          </div>
        </div>
      </div>

      {/* Table / Cards Container */}
      <div className="clay-card mt-5 overflow-hidden p-4 sm:p-6">
        {filteredItems.length === 0 ? (
          <div className="py-10 text-center">
            <p className="text-sm font-bold text-slate-700">
              Belum ada riwayat dokumen yang sesuai.
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Buat dokumen baru melalui Katalog Layanan untuk menyimpannya di sini.
            </p>
          </div>
        ) : (
          <>
            {/* Desktop & Tablet Table */}
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full border-collapse text-left">
                <thead>
                  <tr className="border-b border-slate-200 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    <th className="px-4 py-3">Nama Berkas</th>
                    <th className="px-4 py-3">Layanan</th>
                    <th className="px-4 py-3">Waktu Pembuatan</th>
                    <th className="px-4 py-3">Format</th>
                    <th className="px-4 py-3">Ukuran</th>
                    <th className="px-4 py-3 text-right">Aksi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {paginatedItems.map((item) => {
                    const isExcel = item.file_format === 'xlsx';
                    const isPdf = item.file_format === 'pdf';
                    return (
                      <tr key={item.id} className="hover:bg-slate-50">
                        <td className="px-4 py-3.5">
                          <div className="flex items-center gap-3">
                            <div
                              className={`${
                                isExcel
                                  ? 'clay-icon-green'
                                  : isPdf
                                  ? 'clay-icon-amber'
                                  : 'clay-icon-blue'
                              } flex h-8 w-8 shrink-0 items-center justify-center rounded-lg`}
                            >
                              {isExcel ? (
                                <FileSpreadsheet className="h-4 w-4 text-white" />
                              ) : (
                                <FileText className="h-4 w-4 text-white" />
                              )}
                            </div>
                            <span className="text-xs font-bold text-slate-900 sm:text-sm">
                              {item.filename}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3.5 text-xs font-semibold text-slate-600">
                          {item.service_name}
                        </td>
                        <td className="px-4 py-3.5 text-xs font-medium text-slate-500">
                          {formatTimestamp(item.created_at)}
                        </td>
                        <td className="px-4 py-3.5">
                          <span
                            className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                              isExcel
                                ? 'border border-emerald-200 bg-emerald-50 text-emerald-800'
                                : isPdf
                                ? 'border border-amber-200 bg-amber-50 text-amber-800'
                                : 'border border-blue-200 bg-blue-50 text-blue-800'
                            }`}
                          >
                            {item.file_format.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 text-xs font-semibold text-slate-600">
                          {item.file_size_human}
                        </td>
                        <td className="px-4 py-3.5 text-right">
                          <button
                            type="button"
                            onClick={() => onRedownload(item)}
                            className="clay-btn-white inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-slate-700"
                          >
                            <Download className="h-3.5 w-3.5 text-blue-700" />
                            <span>Unduh</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Mobile 1-Column Stacked Cards */}
            <div className="grid grid-cols-1 gap-3 md:hidden">
              {paginatedItems.map((item) => {
                const isExcel = item.file_format === 'xlsx';
                const isPdf = item.file_format === 'pdf';
                return (
                  <div key={item.id} className="clay-subcard p-4">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-3">
                        <div
                          className={`${
                            isExcel
                              ? 'clay-icon-green'
                              : isPdf
                              ? 'clay-icon-amber'
                              : 'clay-icon-blue'
                          } flex h-9 w-9 shrink-0 items-center justify-center rounded-lg`}
                        >
                          {isExcel ? (
                            <FileSpreadsheet className="h-4 w-4 text-white" />
                          ) : (
                            <FileText className="h-4 w-4 text-white" />
                          )}
                        </div>
                        <div>
                          <p className="break-all text-xs font-bold text-slate-900">
                            {item.filename}
                          </p>
                          <p className="mt-0.5 text-[11px] font-medium text-slate-500">
                            {item.service_name} • {item.file_size_human} •{' '}
                            {formatTimestamp(item.created_at)}
                          </p>
                        </div>
                      </div>

                      <span
                        className={`shrink-0 rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                          isExcel
                            ? 'border border-emerald-200 bg-emerald-50 text-emerald-800'
                            : isPdf
                            ? 'border border-amber-200 bg-amber-50 text-amber-800'
                            : 'border border-blue-200 bg-blue-50 text-blue-800'
                        }`}
                      >
                        {item.file_format.toUpperCase()}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => onRedownload(item)}
                      className="clay-btn-white mt-3 flex w-full items-center justify-center gap-1.5 py-2 text-xs font-bold text-slate-700"
                    >
                      <Download className="h-3.5 w-3.5 text-blue-700" />
                      <span>Unduh Berkas</span>
                    </button>
                  </div>
                );
              })}
            </div>
          </>
        )}

        {/* Footer Info & Pagination Controls (10 Items per Page) */}
        <div className="mt-5 flex flex-col items-center justify-between gap-3 border-t border-slate-200 pt-4 sm:flex-row">
          <p className="text-xs font-medium text-slate-500">
            {filteredItems.length === 0
              ? 'Menampilkan 0 dokumen.'
              : `Menampilkan ${startIndex + 1}–${endIndex} dari ${filteredItems.length} dokumen (Halaman ${safePage} dari ${totalPages})`}
          </p>

          {totalPages > 1 && (
            <div className="flex flex-wrap items-center justify-center gap-1.5">
              <button
                type="button"
                disabled={safePage <= 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                className="clay-btn-white inline-flex items-center gap-1 px-3 py-1.5 text-xs font-bold text-slate-700 disabled:cursor-not-allowed disabled:opacity-45"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                <span>Sebelumnya</span>
              </button>

              {Array.from({ length: totalPages }, (_, idx) => idx + 1).map((pageNum) => (
                <button
                  key={pageNum}
                  type="button"
                  onClick={() => setCurrentPage(pageNum)}
                  className={`min-w-[32px] px-2.5 py-1.5 text-xs font-bold ${
                    pageNum === safePage
                      ? 'clay-btn-primary'
                      : 'clay-btn-white text-slate-700'
                  }`}
                >
                  {pageNum}
                </button>
              ))}

              <button
                type="button"
                disabled={safePage >= totalPages}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                className="clay-btn-white inline-flex items-center gap-1 px-3 py-1.5 text-xs font-bold text-slate-700 disabled:cursor-not-allowed disabled:opacity-45"
              >
                <span>Berikutnya</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
