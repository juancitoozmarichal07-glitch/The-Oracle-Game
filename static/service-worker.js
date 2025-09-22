// service-worker.js (Versión Mínima y Segura)

self.addEventListener('install', (event) => {
  console.log('[Service Worker] Instalado');
  // No hacemos nada con la caché por ahora para mantenerlo simple.
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activado');
  // Tomamos el control de la página inmediatamente.
  return self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // No interceptamos ninguna petición, simplemente dejamos que la red
  // se encargue de todo. Esto evita problemas de conexión.
  // console.log('[Service Worker] Petición fetch interceptada para:', event.request.url);
  return; 
});
