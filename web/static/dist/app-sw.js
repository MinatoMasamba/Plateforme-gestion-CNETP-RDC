// Service worker CNETP — app shell offline + réseau prioritaire pour l'API
const CACHE_NAME = 'cnetp-shell-v2';
const APP_SHELL = [
  '/app/',
  '/static/img/android-chrome-192x192.png',
  '/static/img/android-chrome-512x512.png',
  '/static/img/favicon-32x32.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((k) => k.startsWith('cnetp-shell-') && k !== CACHE_NAME).map((k) => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Données API/Django : toujours le réseau (jamais de données périmées en cache)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(request).catch(() => new Response(JSON.stringify({ detail: 'Hors ligne' }), {
      status: 503, headers: { 'Content-Type': 'application/json' },
    })));
    return;
  }

  // Une navigation doit recevoir le HTML courant, notamment le code des modules.
  // Le cache reste disponible lorsque le serveur n'est pas joignable.
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request, {cache: 'no-cache'}).then((response) => {
      if (response.ok) {
        const copy = response.clone();
        event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.put(request, copy)));
      }
      return response;
    }).catch(async () => (await caches.match(request)) || Response.error()));
    return;
  }

  // Ressources versionnées : cache d'abord, réseau en secours.
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
