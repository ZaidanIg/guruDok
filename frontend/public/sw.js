const CACHE_NAME = 'gurudok-static-v1';
const STATIC_ASSET_PATTERN = /\/(icons\/.*\.(webp|png)|character2\.(webp|png)|logo-brand\.webp|apple-touch-icon\.png|favicon\.ico|doc-(word|excel|pdf)-clay\.png)$/i;

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (!STATIC_ASSET_PATTERN.test(url.pathname)) return;

  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const cached = await cache.match(request);
      if (cached) return cached;

      const networkResponse = await fetch(request);
      if (networkResponse && networkResponse.ok) {
        cache.put(request, networkResponse.clone());
      }
      return networkResponse;
    })
  );
});
