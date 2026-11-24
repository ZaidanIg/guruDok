import React, { useEffect, useRef, useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import pdfWorkerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import { Loader2, RefreshCw } from 'lucide-react';
import { PaperSize } from '../../types';
import { getPaperMetrics, PageOrientation } from './paperDimensions';
import { ZoomSetting } from './WordPagePaginator';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorkerUrl;

interface PdfCanvasPreviewProps {
  pdfBuffer: ArrayBuffer | null;
  isLoading: boolean;
  errorMsg: string | null;
  paperSize: PaperSize;
  orientation: PageOrientation;
  zoom: ZoomSetting;
  onRetry: () => void;
  onPageCountChange?: (count: number) => void;
}

interface RenderedPageData {
  pageNumber: number;
  width: number;
  height: number;
  dataUrl: string;
}

export const PdfCanvasPreview: React.FC<PdfCanvasPreviewProps> = ({
  pdfBuffer,
  isLoading,
  errorMsg,
  paperSize,
  orientation,
  zoom,
  onRetry,
  onPageCountChange,
}) => {
  const metrics = getPaperMetrics(paperSize, orientation);
  const canvasContainerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState<number>(640);
  const [renderedPages, setRenderedPages] = useState<RenderedPageData[]>([]);
  const [isRenderingCanvas, setIsRenderingCanvas] = useState(false);

  useEffect(() => {
    const el = canvasContainerRef.current;
    if (!el) return;
    const updateWidth = () => {
      if (el.clientWidth > 0) setContainerWidth(el.clientWidth);
    };
    updateWidth();
    const observer = new ResizeObserver(updateWidth);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!pdfBuffer) {
      setRenderedPages([]);
      return;
    }

    let cancelled = false;
    setIsRenderingCanvas(true);

    const renderPdf = async () => {
      try {
        const loadingTask = pdfjsLib.getDocument({ data: pdfBuffer.slice(0) });
        const pdf = await loadingTask.promise;
        if (cancelled) return;

        onPageCountChange?.(pdf.numPages);
        const pages: RenderedPageData[] = [];
        const renderScale = Math.min(2, window.devicePixelRatio || 1.5);

        for (let num = 1; num <= pdf.numPages; num++) {
          const page = await pdf.getPage(num);
          const baseViewport = page.getViewport({ scale: 96 / 72 });
          const hiResViewport = page.getViewport({ scale: (96 / 72) * renderScale });

          const offscreenCanvas = document.createElement('canvas');
          offscreenCanvas.width = Math.round(hiResViewport.width);
          offscreenCanvas.height = Math.round(hiResViewport.height);
          const ctx = offscreenCanvas.getContext('2d');
          if (!ctx) continue;

          await page.render({ canvasContext: ctx, viewport: hiResViewport, canvas: offscreenCanvas }).promise;
          if (cancelled) return;

          pages.push({
            pageNumber: num,
            width: Math.round(baseViewport.width),
            height: Math.round(baseViewport.height),
            dataUrl: offscreenCanvas.toDataURL('image/png'),
          });
        }

        if (!cancelled) {
          setRenderedPages(pages);
        }
      } catch {
        if (!cancelled) {
          setRenderedPages([]);
        }
      } finally {
        if (!cancelled) {
          setIsRenderingCanvas(false);
        }
      }
    };

    renderPdf();
    return () => {
      cancelled = true;
    };
  }, [pdfBuffer, onPageCountChange]);

  const availableWidth = Math.max(280, containerWidth - 32);

  return (
    <div
      ref={canvasContainerRef}
      onCopy={(e) => e.preventDefault()}
      onCut={(e) => e.preventDefault()}
      onContextMenu={(e) => e.preventDefault()}
      onDragStart={(e) => e.preventDefault()}
      className="word-canvas preview-protected w-full select-none"
    >
      {(isLoading || isRenderingCanvas) && (
        <div className="flex flex-col items-center justify-center py-20 text-slate-600">
          <Loader2 className="h-7 w-7 animate-spin text-blue-600" />
          <p className="mt-2.5 text-xs font-semibold">Memuat pratinjau PDF...</p>
        </div>
      )}

      {!isLoading && !isRenderingCanvas && errorMsg && (
        <div className="my-10 rounded-xl border border-red-200 bg-white px-5 py-4 text-center shadow-sm">
          <p className="text-xs font-semibold text-red-700">{errorMsg}</p>
          <button
            type="button"
            onClick={onRetry}
            className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-blue-700"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Muat Ulang
          </button>
        </div>
      )}

      {!isLoading &&
        !isRenderingCanvas &&
        !errorMsg &&
        renderedPages.map((pg) => {
          const fitScale = Math.min(1, Math.max(0.28, availableWidth / pg.width));
          const activeScale = zoom === 'fit' ? fitScale : zoom;
          const scaledW = Math.round(pg.width * activeScale);
          const scaledH = Math.round(pg.height * activeScale);

          return (
            <div key={pg.pageNumber} className="word-page-wrapper" style={{ width: `${scaledW}px` }}>
              <div className="word-page-outer-label">
                <span>
                  Halaman {pg.pageNumber} dari {renderedPages.length}
                </span>
                <span>{metrics.label}</span>
              </div>

              <div
                className="word-page-scale-box bg-white shadow-md border border-slate-300"
                style={{
                  width: `${scaledW}px`,
                  height: `${scaledH}px`,
                }}
              >
                <img
                  src={pg.dataUrl}
                  alt={`Halaman ${pg.pageNumber}`}
                  draggable={false}
                  className="pointer-events-none block h-full w-full select-none"
                />
              </div>
            </div>
          );
        })}
    </div>
  );
};
