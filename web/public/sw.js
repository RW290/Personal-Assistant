// The service worker is what makes the app installable and quick to open.
// It caches only the app's own files under /app/ (HTML, scripts, styles, icons).
// It never touches /api, so my data is always fetched fresh and never stored on the phone.
const CACHE = "assistant-app-v1";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  const isAppFile =
    event.request.method === "GET" && url.origin === self.location.origin && url.pathname.startsWith("/app/");
  if (!isAppFile) return; // let the browser handle it normally, with no caching

  // Network first, so updates show up right away; the cached copy is only for when offline.
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(CACHE).then((cache) => cache.put(event.request, copy));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
