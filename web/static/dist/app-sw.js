// Service worker CNETP — app shell offline + réseau prioritaire pour l'API
const CACHE_NAME = 'cnetp-shell-v1';
const APP_SHELL = [
  '/app/',
  '/static/dist/icons/icon-192.png',
  '/static/dist/icons/icon-512.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Données API/Django : toujours le réseau (jamais de données périmées en cache)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(request).catch(() => new Response(JSON.stringify({ detail: 'Hors ligne' }), {
      status: 503, headers: { 'Content-Type': 'application/json' },
    })));
    return;
  }

  // App shell : cache d'abord, réseau en secours + mise à jour du cache
  event.respondWith(
    caches.match(request).then((cached) => {
      const network = fetch(request).then((response) => {
        if (response && response.ok) {
          caches.open(CACHE_NAME).then((cache) => cache.put(request, response.clone()));
        }
        return response;
      }).catch(() => cached);
      return cached || network;
    })
  );
});
