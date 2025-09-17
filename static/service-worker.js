// service-worker.js para The Oracle Game (versión simple)

// Se activa cuando el SW se instala.
self.addEventListener('install', event => {
  console.log('Service Worker instalado.');
  self.skipWaiting(); // Activa el SW inmediatamente.
});

// Se activa cuando el SW toma el control.
self.addEventListener('activate', event => {
  console.log('Service Worker activado.');
});

// Listener 'fetch' vacío. Esencial para que el navegador ofrezca la opción de "Instalar".
self.addEventListener('fetch', event => {
  // No hacemos nada con la petición, solo la dejamos pasar.
  return;
});
