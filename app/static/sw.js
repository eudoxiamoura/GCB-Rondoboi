const CACHE_NAME = "bovinos-static-v1";
const STATIC_ASSETS = [
  "/static/css/style.css",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
      )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;

  if (request.method !== "GET") return;

  const url = new URL(request.url);

  // Arquivos estáticos: cache primeiro, rede como reforço.
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(caches.match(request).then((cached) => cached || fetch(request)));
    return;
  }

  // Páginas com dados: sempre busca da rede (os números têm que estar
  // atualizados). Só mostra um aviso simples se estiver realmente offline.
  event.respondWith(
    fetch(request).catch(
      () =>
        new Response(
          "<!doctype html><html lang=\"pt-br\"><body style=\"font-family:sans-serif;text-align:center;padding:40px;\">" +
            "<h1>Sem conexão</h1><p>Verifique sua internet e tente novamente.</p></body></html>",
          { headers: { "Content-Type": "text/html; charset=utf-8" } }
        )
    )
  );
});
