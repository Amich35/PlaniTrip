const CACHE_NAME = 'planitrip-v9';
const ASSETS = [
  'index.html',
  'manifest.json',
  'vendor/xlsx.full.min.js',
  'vendor/mammoth.browser.min.js',
  'vendor/pdf.min.js',
  'vendor/pdf.worker.min.js',
  'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.js',
  'https://cdn.jsdelivr.net/npm/lucide@0.383.0/dist/umd/lucide.js',
  'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js'
];

// Installation : mise en cache des ressources essentielles (pour le mode hors-ligne)
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

// Fetch : réseau en priorité (pour toujours avoir la dernière version quand il y a internet),
// cache uniquement en secours si hors-ligne ou requête impossible.
self.addEventListener('fetch', event => {
  // Laisser passer les requêtes API météo, Wikipedia/Commons, Anthropic et Supabase (réseau uniquement, jamais mises en cache)
  if (event.request.url.includes('open-meteo.com')) return;
  if (event.request.url.includes('wikipedia.org')) return;
  if (event.request.url.includes('wikimedia.org')) return;
  if (event.request.url.includes('api.anthropic.com')) return;
  if (event.request.url.includes('supabase.co')) return;

  event.respondWith(
    fetch(event.request).then(response => {
      if (response.ok && event.request.method === 'GET') {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
      }
      return response;
    }).catch(() =>
      caches.match(event.request).then(cached => cached || caches.match('index.html'))
    )
  );
});
