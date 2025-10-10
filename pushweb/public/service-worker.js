self.addEventListener('push', function(event) {
  console.log('[Service Worker] Push Received.');
  let data = {};
  try {
    data = event.data.json();
  } catch (e) {
    data = { title: 'New notification', body: 'You have a message' };
  }

  const title = data.title || 'Notification';
  const options = {
    body: data.body,
    icon: data.icon || '/assets/pushweb/images/notification-icon.png',
    data: data,
    requireInteraction: true
  };

  event.waitUntil(
    self.registration.showNotification(title, options).then(() => {
      console.log('[SW] showNotification executed');
    }).catch(err => {
      console.error('[SW] showNotification failed:', err);
    })
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const url = event.notification.data?.url || '/app';
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(windowClients => {
      for (let client of windowClients) {
        if (client.url.includes(url) && 'focus' in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});