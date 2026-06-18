CACHE = "podcast-v1"
urls = ["./", "./index.html", "./manifest.json", "./icon.svg"]
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(urls))); self.skipWaiting(); });
self.addEventListener("activate", e => { self.clients.claim(); });
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (url.pathname.endsWith(".wav") || url.pathname.endsWith(".mp3") || url.pathname.endsWith(".m4a")){
    return; // 音频走网络，不缓存
  }
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
