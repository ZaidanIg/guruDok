const CACHE_STORAGE_NAME = 'gurudok-static-v1';
const LOCAL_CACHE_ALLOWED_KEY = 'gurudok_cache_allowed_v1';
const SESSION_DISMISSED_KEY = 'gurudok_cache_prompt_dismissed_v1';

const HOME_STATIC_ASSETS = [
  '/favicon.ico',
  '/logo-brand.webp',
  '/apple-touch-icon.png',
  '/character2.webp',
  '/character2.png',
  '/icons/cp-icon.webp',
  '/icons/atp-icon.webp',
  '/icons/modul-icon.webp',
  '/icons/prota-icon.webp',
  '/icons/promes-icon.webp',
];

export function isLocalCacheAllowed(): boolean {
  try {
    return localStorage.getItem(LOCAL_CACHE_ALLOWED_KEY) === 'true';
  } catch {
    return false;
  }
}

export function markLocalCacheAllowed(allowed: boolean = true): void {
  try {
    if (allowed) {
      localStorage.setItem(LOCAL_CACHE_ALLOWED_KEY, 'true');
      sessionStorage.removeItem(SESSION_DISMISSED_KEY);
    } else {
      localStorage.removeItem(LOCAL_CACHE_ALLOWED_KEY);
    }
  } catch {
    // ignore storage quota errors
  }
}

export function isSessionCachePromptDismissed(): boolean {
  try {
    return sessionStorage.getItem(SESSION_DISMISSED_KEY) === 'true';
  } catch {
    return false;
  }
}

export function dismissSessionCachePrompt(): void {
  try {
    sessionStorage.setItem(SESSION_DISMISSED_KEY, 'true');
  } catch {
    // ignore
  }
}

/**
 * Registers the static-asset Service Worker and pre-warms Browser Cache Storage
 * so Home & Catalog icons load instantaneously with zero repeated downloads.
 */
export async function enableAndWarmAssetCache(): Promise<void> {
  markLocalCacheAllowed(true);

  try {
    if ('serviceWorker' in navigator) {
      await navigator.serviceWorker.register('/sw.js', { scope: '/' });
    }
  } catch {
    // Service worker optional in non-HTTPS local previews
  }

  try {
    if ('caches' in window) {
      const cache = await caches.open(CACHE_STORAGE_NAME);
      await Promise.allSettled(
        HOME_STATIC_ASSETS.map(async (url) => {
          const existing = await cache.match(url);
          if (!existing) {
            await cache.add(url);
          }
        })
      );
    }
  } catch {
    // Ignore cache API errors
  }
}
