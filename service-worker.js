const CACHE_NAME = 'asie2026-v2';
const ASSETS = [
  'index.html',
  'manifest.json'
];

// Installation : mise en cache des ressources essentielles
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

// Activation : suppression des anciens caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch : cache en priorité, réseau en fallback
self.addEventListener('fetch', event => {
  // Laisser passer les requêtes API météo et Wikipedia/Commons (réseau uniquement)
  if (event.request.url.includes('open-meteo.com')) return;
  if (event.request.url.includes('wikipedia.org')) return;
  if (event.request.url.includes('wikimedia.org')) return;

  event.respondWith(
    caches.match(event.request).then(cached => {
      return cached || fetch(event.request).then(response => {
        // Mettre en cache les nouvelles ressources statiques
        if (response.ok && event.request.method === 'GET') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => caches.match('index.html'));
    })
  );
});
