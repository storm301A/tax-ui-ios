const CACHE = 'tax-ui-v27';

const ASSETS = [
  './',
  './index.html',
  './css/app.css?v=27',
  './js/main.js?v=27',
  './manifest.json',
  './img/hero-card.png?v=27',
  './img/special-card.png?v=27',
  './img/banner.png?v=27',
  './img/bell.png?v=27',
  './img/avatar.png',
  './img/profile-page.png?v=27',
  './img/icon-qmark.png?v=27',
  './img/icon-svc1.png?v=27',
  './img/icon-svc2.png?v=27',
  './img/icon-svc3.png?v=27',
  './img/icon-svc4.png?v=27',
  './img/icon-family.png',
  './img/icon-job.png',
  './img/icon-bank.png',
  './img/tab-home-on.png',
  './img/tab-home-off.png',
  './img/tab-todo.png',
  './img/tab-work.png',
  './img/tab-msg.png',
  './img/tab-profile-on.png',
  './img/tab-profile-off.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => Promise.allSettled(ASSETS.map((url) => cache.add(url))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

// 全部资源网络优先：联网时永远拿到最新，断网时回落到缓存
self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;
  if (!request.url.startsWith(self.location.origin)) return;

  event.respondWith((async () => {
    const cache = await caches.open(CACHE);

    try {
      const response = await fetch(request);
      if (response && response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    } catch (err) {
      const cached = await cache.match(request, { ignoreSearch: true });
      if (cached) return cached;

      if (request.mode === 'navigate') {
        const shell = await cache.match('./index.html');
        if (shell) return shell;
      }

      return new Response('当前离线，请联网后重新打开', {
        status: 503,
        headers: { 'Content-Type': 'text/plain; charset=utf-8' }
      });
    }
  })());
});
