const CACHE_NAME = 'secure-exam-v1';
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // If we found a cached version, return it. Wait, for dynamic Django pages, caching / is bad.
        // It's better to fetch from network, fallback to cache.
        return fetch(event.request).catch(
            () => response || new Response('Offline: Please check your internet connection.', {
                headers: { 'Content-Type': 'text/plain' }
            })
        );
      })
  );
});
