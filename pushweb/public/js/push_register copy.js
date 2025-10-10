function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
}

async function registerPush() {
  const vapidKey = await frappe.call('pushweb.api.push.get_vapid_public_key');
  const key = vapidKey.message;

  const permission = await Notification.requestPermission();
  if (permission !== 'granted') {
    frappe.msgprint('You need to allow notifications');
    return;
  }

  const reg = await navigator.serviceWorker.register(
    '/assets/pushweb/service-worker.js',
  );
  const sub = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(key),
  });

  await frappe.call({
    method: 'pushweb.api.push.save_push_subscription',
    args: { subscription: JSON.stringify(sub) },
  });

  frappe.show_alert({ message: 'Push notification enabled!', indicator: 'green' });
}