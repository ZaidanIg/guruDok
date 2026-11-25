import { PaperSize } from '../../types';

export type PageOrientation = 'portrait' | 'landscape';

export interface PaperMetrics {
  paperSize: PaperSize;
  orientation: PageOrientation;
  widthMm: number;
  heightMm: number;
  widthPx: number;
  heightPx: number;
  marginTopPx: number;
  marginRightPx: number;
  marginBottomPx: number;
  marginLeftPx: number;
  contentWidthPx: number;
  contentHeightPx: number;
  label: string;
}

// 96 DPI: 1 mm = 3.779527559 px (mirrors backend DocumentEngine constants)
const PX_PER_MM = 96 / 25.4;

const MARGIN_TOP_MM = 25;
const MARGIN_BOTTOM_MM = 25;
const MARGIN_LEFT_MM = 30;
const MARGIN_RIGHT_MM = 20;

export const LANDSCAPE_SERVICE_IDS = new Set<string>([
  '06_promes',
  '13_presensi',
  '14_jurnal_mengajar',
  '15_daftar_nilai',
  '16_deskripsi_rapor',
  '17_rekap_rapor',
]);

export function getServiceOrientation(serviceId: string): PageOrientation {
  return LANDSCAPE_SERVICE_IDS.has(serviceId) ? 'landscape' : 'portrait';
}

export function getPaperMetrics(
  paperSize: PaperSize,
  orientation: PageOrientation = 'portrait'
): PaperMetrics {
  const baseW = paperSize === 'A4' ? 210 : 215;
  const baseH = paperSize === 'A4' ? 297 : 330;

  const widthMm = orientation === 'landscape' ? baseH : baseW;
  const heightMm = orientation === 'landscape' ? baseW : baseH;

  const widthPx = Math.round(widthMm * PX_PER_MM);
  const heightPx = Math.round(heightMm * PX_PER_MM);

  const marginTopPx = Math.round(MARGIN_TOP_MM * PX_PER_MM);
  const marginBottomPx = Math.round(MARGIN_BOTTOM_MM * PX_PER_MM);
  const marginLeftPx = Math.round(MARGIN_LEFT_MM * PX_PER_MM);
  const marginRightPx = Math.round(MARGIN_RIGHT_MM * PX_PER_MM);

  return {
    paperSize,
    orientation,
    widthMm,
    heightMm,
    widthPx,
    heightPx,
    marginTopPx,
    marginRightPx,
    marginBottomPx,
    marginLeftPx,
    contentWidthPx: widthPx - marginLeftPx - marginRightPx,
    contentHeightPx: heightPx - marginTopPx - marginBottomPx,
    label: `${paperSize} (${widthMm} × ${heightMm} mm)`,
  };
}
