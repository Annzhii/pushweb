import frappe, json
from frappe import _
from pywebpush import webpush, WebPushException

@frappe.whitelist()
def get_vapid_public_key():
    return frappe.get_site_config().get("vapid_public_key")

@frappe.whitelist()
def save_push_subscription(subscription):
    if isinstance(subscription, str):
        subscription = json.loads(subscription)
    endpoint = subscription.get('endpoint')
    keys = subscription.get('keys', {})
    if not endpoint:
        frappe.throw(_('Invalid subscription'))

    existing = frappe.db.exists("Push Subscription", {"endpoint": endpoint})
    if existing:
        frappe.db.set_value("Push Subscription", existing, "raw", json.dumps(subscription))
        return existing

    doc = frappe.get_doc({
        "doctype": "Push Subscription",
        "user": frappe.session.user,
        "endpoint": endpoint,
        "p256dh": keys.get('p256dh'),
        "auth": keys.get('auth'),
        "raw": json.dumps(subscription),
        "enabled": 1
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def send_push_to_user(user, title, body, url=None):
    subs = frappe.get_all("Push Subscription", filters={"user": user, "enabled": 1}, fields=["raw", "name"])
    vapid_priv = frappe.get_site_config().get("vapid_private_key")
    vapid_pub = frappe.get_site_config().get("vapid_public_key")
    vapid_claims = {"sub": "mailto:admin@yourdomain.com"}

    for s in subs:
        try:
            sub = json.loads(s["raw"])
            webpush(
                subscription_info=sub,
                data=json.dumps({"title": title, "body": body, "url": url}),
                vapid_private_key=vapid_priv,
                vapid_claims=vapid_claims
            )
        except WebPushException as e:
            frappe.db.set_value("Push Subscription", s["name"], "enabled", 0)
            frappe.log_error(f"Push failed for {user}: {e}")
