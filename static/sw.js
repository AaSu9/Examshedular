self.addEventListener('install', (e) => {
    console.log('[Service Worker] Install');
});

self.addEventListener('fetch', (e) => {
    // Basic fetch pass-through to ensure it works offline-capable in future
    e.respondWith(fetch(e.request));
});
