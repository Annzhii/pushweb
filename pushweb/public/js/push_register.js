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

  try {
    // 注册 service worker
    await navigator.serviceWorker.register('/assets/pushweb/service-worker.js');
    console.log('SW registered');

    // 等待 2 秒，让 SW 激活
    await new Promise(resolve => setTimeout(resolve, 2000));
    console.log('Waited 2 seconds, proceed to subscribe');

    // 获取 registration（确保 SW 已经注册）
    const registration = await navigator.serviceWorker.getRegistration('/assets/pushweb/service-worker.js');
    if (!registration) {
      throw new Error('Service Worker registration not found');
    }

    // 订阅 push
    const sub = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(key),
    });

    // 保存订阅
    await frappe.call({
      method: 'pushweb.api.push.save_push_subscription',
      args: { subscription: JSON.stringify(sub) },
    });

    frappe.show_alert({ message: 'Push notification enabled!', indicator: 'green' });

  } catch (err) {
    console.error('Push registration failed', err);
    frappe.msgprint('Push registration failed: ' + err.message);
  }
}
