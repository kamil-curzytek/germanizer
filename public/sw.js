// Lernbrot service worker: shows the daily reminder push notifications (sent by the
// send-push-reminders Edge Function) and opens the app when one is tapped. No offline caching.

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));

self.addEventListener('push', (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch {
    // not JSON: fall back to the generic reminder
  }
  event.waitUntil(
    self.registration.showNotification(data.title || 'Lernbrot', {
      body: data.body || 'Your German lesson is ready.',
      icon: 'icon-192.png',
      badge: 'badge-96.png',
      tag: data.tag || 'daily-reminder',
    }),
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const appUrl = self.registration.scope;
  event.waitUntil(
    (async () => {
      const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
      const open = windows.find((w) => w.url.startsWith(appUrl));
      if (open) return open.focus();
      return self.clients.openWindow(appUrl);
    })(),
  );
});
