import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { PaperSize } from '../../types';
import { getPaperMetrics, PageOrientation } from './paperDimensions';

export type ZoomSetting = 'fit' | number;

interface WordPagePaginatorProps {
  paperSize: PaperSize;
  orientation: PageOrientation;
  zoom: ZoomSetting;
  contentKey: string;
  onPageCountChange?: (count: number) => void;
  children: React.ReactNode;
}

type FlowToken =
  | { type: 'break' }
  | { type: 'table'; tableEl: HTMLTableElement; wrapperClass: string; marginTop: number; marginBottom: number }
  | { type: 'atom'; el: HTMLElement; keepWithNext: boolean; height: number };

function getOuterHeight(el: HTMLElement): number {
  const style = window.getComputedStyle(el);
  const mt = parseFloat(style.marginTop) || 0;
  const mb = parseFloat(style.marginBottom) || 0;
  return el.getBoundingClientRect().height + mt + mb;
}

function getMargins(el: HTMLElement): { mt: number; mb: number } {
  const style = window.getComputedStyle(el);
  return {
    mt: parseFloat(style.marginTop) || 0,
    mb: parseFloat(style.marginBottom) || 0,
  };
}

function collectFlowTokens(container: HTMLElement, maxPageHeight: number): FlowToken[] {
  const tokens: FlowToken[] = [];

  const walk = (parent: HTMLElement) => {
    const children = Array.from(parent.children) as HTMLElement[];
    for (const child of children) {
      if (child.getAttribute('data-page-break') === 'before') {
        tokens.push({ type: 'break' });
      }

      const tag = child.tagName;
      const keepTogether = child.getAttribute('data-keep-together') === 'true';
      const keepWithNext =
        child.getAttribute('data-keep-with-next') === 'true' ||
        tag === 'H2' ||
        tag === 'H3' ||
        tag === 'H4';

      // Direct table or table container
      if (tag === 'TABLE') {
        const { mt, mb } = getMargins(child);
        tokens.push({
          type: 'table',
          tableEl: child as HTMLTableElement,
          wrapperClass: '',
          marginTop: mt,
          marginBottom: mb,
        });
        continue;
      }

      if (
        child.classList.contains('paper-table-container') ||
        child.getAttribute('data-splittable-table') === 'true'
      ) {
        const innerTable = child.querySelector(':scope > table') as HTMLTableElement | null;
        if (innerTable) {
          const { mt, mb } = getMargins(child);
          tokens.push({
            type: 'table',
            tableEl: innerTable,
            wrapperClass: child.className,
            marginTop: mt,
            marginBottom: mb,
          });
          continue;
        }
      }

      if (keepTogether) {
        tokens.push({
          type: 'atom',
          el: child,
          keepWithNext: false,
          height: getOuterHeight(child),
        });
        continue;
      }

      if (keepWithNext) {
        tokens.push({
          type: 'atom',
          el: child,
          keepWithNext: true,
          height: getOuterHeight(child),
        });
        continue;
      }

      // Check if container should be descended into for granular page breaks
      const hasElementChildren = child.children.length > 0;
      const isGridOrFlexRow =
        child.classList.contains('grid') ||
        (child.classList.contains('flex') && !child.classList.contains('flex-col'));

      if (
        hasElementChildren &&
        !isGridOrFlexRow &&
        (tag === 'DIV' || tag === 'SECTION' || tag === 'ARTICLE')
      ) {
        walk(child);
        continue;
      }

      // Leaf or indivisible block (p, ul, ol, grid, etc.)
      const h = getOuterHeight(child);
      if (h > maxPageHeight && hasElementChildren && (tag === 'OL' || tag === 'UL')) {
        // Large list that exceeds a full page: split by list items
        const items = Array.from(child.children) as HTMLElement[];
        for (const li of items) {
          tokens.push({
            type: 'atom',
            el: li,
            keepWithNext: false,
            height: getOuterHeight(li),
          });
        }
        continue;
      }

      tokens.push({
        type: 'atom',
        el: child,
        keepWithNext: false,
        height: h,
      });
    }
  };

  walk(container);
  return tokens;
}

function buildTableSliceHtml(
  tableEl: HTMLTableElement,
  wrapperClass: string,
  theadHtml: string,
  bodyRowsHtml: string[],
  tfootHtml: string
): string {
  const tableClass = tableEl.className || 'paper-table';
  const inner = `<table class="${tableClass}">${theadHtml}<tbody>${bodyRowsHtml.join('')}</tbody>${tfootHtml}</table>`;
  if (wrapperClass) {
    return `<div class="${wrapperClass}">${inner}</div>`;
  }
  return inner;
}

function paginateDom(stagingEl: HTMLElement, contentHeightPx: number): string[] {
  const tokens = collectFlowTokens(stagingEl, contentHeightPx);
  const pages: string[][] = [[]];
  let currentHeight = 0;

  const pushNewPage = () => {
    if (pages[pages.length - 1].length > 0) {
      pages.push([]);
      currentHeight = 0;
    }
  };

  const BLOCK_GAP = 6; // consistent spacing buffer between stacked blocks

  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i];

    if (token.type === 'break') {
      pushNewPage();
      continue;
    }

    if (token.type === 'atom') {
      let neededHeight = token.height;
      // Keep-with-next: avoid orphan headings at the bottom of a page
      if (token.keepWithNext && i + 1 < tokens.length) {
        const next = tokens[i + 1];
        if (next.type === 'atom') {
          neededHeight += Math.min(next.height, 140);
        } else if (next.type === 'table') {
          const thead = next.tableEl.querySelector('thead');
          const firstRow = next.tableEl.querySelector('tbody > tr');
          const thH = thead ? thead.getBoundingClientRect().height : 0;
          const frH = firstRow ? firstRow.getBoundingClientRect().height : 36;
          neededHeight += thH + frH + 12;
        }
      }

      if (currentHeight > 0 && currentHeight + neededHeight > contentHeightPx) {
        pushNewPage();
      }

      const clone = token.el.cloneNode(true) as HTMLElement;
      clone.removeAttribute('data-page-break');
      pages[pages.length - 1].push(clone.outerHTML);
      currentHeight += token.height + BLOCK_GAP;
      continue;
    }

    if (token.type === 'table') {
      const tableEl = token.tableEl;
      const thead = tableEl.querySelector('thead');
      const tbody = tableEl.querySelector('tbody');
      const tfoot = tableEl.querySelector('tfoot');

      const theadHtml = thead ? thead.outerHTML : '';
      const theadHeight = thead ? thead.getBoundingClientRect().height : 0;
      const tfootHtml = tfoot ? tfoot.outerHTML : '';
      const tfootHeight = tfoot ? tfoot.getBoundingClientRect().height : 0;

      const bodyRows = tbody
        ? (Array.from(tbody.querySelectorAll(':scope > tr')) as HTMLTableRowElement[])
        : (Array.from(tableEl.querySelectorAll(':scope > tr')) as HTMLTableRowElement[]);

      if (bodyRows.length === 0) {
        const fullH = tableEl.getBoundingClientRect().height + token.marginTop + token.marginBottom;
        if (currentHeight > 0 && currentHeight + fullH > contentHeightPx) {
          pushNewPage();
        }
        pages[pages.length - 1].push(
          token.wrapperClass ? `<div class="${token.wrapperClass}">${tableEl.outerHTML}</div>` : tableEl.outerHTML
        );
        currentHeight += fullH + BLOCK_GAP;
        continue;
      }

      let rowIdx = 0;
      while (rowIdx < bodyRows.length) {
        const firstRowH = bodyRows[rowIdx].getBoundingClientRect().height || 24;
        const minSliceHeight = theadHeight + firstRowH + token.marginTop + 8;

        if (currentHeight > 0 && currentHeight + minSliceHeight > contentHeightPx) {
          pushNewPage();
        }

        const sliceRows: string[] = [];
        let sliceHeight = theadHeight + token.marginTop;

        while (rowIdx < bodyRows.length) {
          const r = bodyRows[rowIdx];
          const rH = r.getBoundingClientRect().height || 24;
          const isLastRow = rowIdx === bodyRows.length - 1;
          const extraFoot = isLastRow ? tfootHeight + token.marginBottom : 0;

          if (sliceRows.length > 0 && currentHeight + sliceHeight + rH + extraFoot > contentHeightPx) {
            break;
          }

          sliceRows.push(r.outerHTML);
          sliceHeight += rH;
          rowIdx++;
        }

        const includeFoot = rowIdx >= bodyRows.length ? tfootHtml : '';
        const sliceHtml = buildTableSliceHtml(
          tableEl,
          token.wrapperClass,
          theadHtml,
          sliceRows,
          includeFoot
        );

        pages[pages.length - 1].push(sliceHtml);
        currentHeight += sliceHeight + (includeFoot ? tfootHeight + token.marginBottom : 0) + BLOCK_GAP;

        if (rowIdx < bodyRows.length) {
          pushNewPage();
        }
      }
    }
  }

  const nonEmpty = pages.filter((p) => p.length > 0).map((p) => p.join(''));
  return nonEmpty.length > 0 ? nonEmpty : [''];
}

export const WordPagePaginator: React.FC<WordPagePaginatorProps> = ({
  paperSize,
  orientation,
  zoom,
  contentKey,
  onPageCountChange,
  children,
}) => {
  const metrics = getPaperMetrics(paperSize, orientation);
  const canvasRef = useRef<HTMLDivElement>(null);
  const stagingRef = useRef<HTMLDivElement>(null);

  const [containerWidth, setContainerWidth] = useState<number>(640);
  const [pagesHtml, setPagesHtml] = useState<string[]>(['']);

  // Track viewport width for Auto Fit-to-Width
  useEffect(() => {
    const el = canvasRef.current;
    if (!el) return;
    const updateWidth = () => {
      if (el.clientWidth > 0) {
        setContainerWidth(el.clientWidth);
      }
    };
    updateWidth();
    const observer = new ResizeObserver(updateWidth);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Re-paginate whenever content, paper size, or orientation changes
  useLayoutEffect(() => {
    const staging = stagingRef.current;
    if (!staging) return;

    const rafId = window.requestAnimationFrame(() => {
      const computedPages = paginateDom(staging, metrics.contentHeightPx);
      setPagesHtml(computedPages);
      onPageCountChange?.(computedPages.length);
    });

    return () => window.cancelAnimationFrame(rafId);
  }, [contentKey, paperSize, orientation, metrics.contentHeightPx, metrics.contentWidthPx, onPageCountChange]);

  const availableWidth = Math.max(280, containerWidth - 32);
  const fitScale = Math.min(1, Math.max(0.28, availableWidth / metrics.widthPx));
  const activeScale = zoom === 'fit' ? fitScale : zoom;

  const scaledW = Math.round(metrics.widthPx * activeScale);
  const scaledH = Math.round(metrics.heightPx * activeScale);

  return (
    <div
      ref={canvasRef}
      onCopy={(e) => e.preventDefault()}
      onCut={(e) => e.preventDefault()}
      onContextMenu={(e) => e.preventDefault()}
      onDragStart={(e) => e.preventDefault()}
      className="word-canvas preview-protected w-full select-none"
    >
      {/* Hidden Off-Screen Staging Container at Exact Physical Content Width */}
      <div
        ref={stagingRef}
        aria-hidden="true"
        className="word-content-flow"
        style={{
          position: 'fixed',
          left: '-99999px',
          top: 0,
          width: `${metrics.contentWidthPx}px`,
          visibility: 'hidden',
          pointerEvents: 'none',
        }}
      >
        {children}
      </div>

      {/* Rendered Separated Physical Pages */}
      {pagesHtml.map((html, idx) => (
        <div
          key={`${paperSize}-${orientation}-${idx}`}
          className="word-page-wrapper"
          style={{ width: `${scaledW}px` }}
        >
          <div className="word-page-outer-label">
            <span>
              Halaman {idx + 1} dari {pagesHtml.length}
            </span>
            <span>{metrics.label}</span>
          </div>

          <div
            className="word-page-scale-box"
            style={{
              width: `${scaledW}px`,
              height: `${scaledH}px`,
            }}
          >
            <div
              className="word-page-sheet"
              style={{
                width: `${metrics.widthPx}px`,
                height: `${metrics.heightPx}px`,
                paddingTop: `${metrics.marginTopPx}px`,
                paddingRight: `${metrics.marginRightPx}px`,
                paddingBottom: `${metrics.marginBottomPx}px`,
                paddingLeft: `${metrics.marginLeftPx}px`,
                transform: `scale(${activeScale})`,
                transformOrigin: 'top left',
              }}
            >
              {/* Subtle Diagonal Preview Watermark */}
              <div
                aria-hidden="true"
                className="pointer-events-none absolute inset-0 z-20 flex items-center justify-center overflow-hidden opacity-[0.045]"
              >
                <span className="-rotate-30 whitespace-nowrap text-5xl font-black tracking-[0.25em] text-slate-900">
                  PREVIEW DOKUMEN
                </span>
              </div>

              {/* Paginated Page Content */}
              <div
                className="word-content-flow pointer-events-none relative z-10"
                style={{
                  width: `${metrics.contentWidthPx}px`,
                  height: `${metrics.contentHeightPx}px`,
                  overflow: 'hidden',
                }}
                dangerouslySetInnerHTML={{ __html: html }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
