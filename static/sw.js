const CACHE_NAME = 'medstock-v1';
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/live_stock',              // or whatever your live page route is
  // add your css/js if you extract them later
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
});