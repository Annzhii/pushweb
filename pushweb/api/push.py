import frappe, json
from frappe import _
from pywebpush import webpush, WebPushException

@frappe.whitelist()
def get_vapid_public_key():
    return frappe.get_site_config().get("vapid_public_key")

@frappe.whitelist()
def save_push_subscription(from_app, subscription):
    if isinstance(subscription, str):
        subscription = json.loads(subscription)
    endpoint = subscription.get('endpoint')
    keys = subscription.get('keys', {})
    if not endpoint:
        frappe.throw(_('Invalid subscription'))

    if from_app == 'erp':
        subscription_type = "Push Subscription"
    elif from_app == 'crm':
        subscription_type = "Push Subscription CRM"
    elif from_app == 'raven':
        subscription_type = "Push Subscription Raven"
    else:
        frappe.throw(_('Invalid app type: {0}').format(from_app))

    existing_for_user = frappe.db.exists(subscription_type, {
        "endpoint": endpoint,
        "user": frappe.session.user,
    })
    if existing_for_user:
        frappe.db.set_value(subscription_type, existing_for_user, {
            "raw": json.dumps(subscription),
            "enabled": 1
        })
        return existing_for_user

    doc = frappe.get_doc({
        "doctype": subscription_type,
        "user": frappe.session.user,
        "endpoint": endpoint,
        "p256dh": keys.get('p256dh'),
        "auth": keys.get('auth'),
        "raw": json.dumps(subscription),
        "enabled": 1
    })
    doc.insert(ignore_permissions=True)
    return doc.name

@frappe.whitelist()
def send_push_to_user(to_app, user, title, body, url=None):
    if to_app == 'erp':
        subscription_type = "Push Subscription"
    elif to_app == 'crm':
        subscription_type = "Push Subscription CRM"
        print(title)
    elif to_app == 'raven':
        subscription_type = "Push Subscription Raven"
    else:
        frappe.throw(_('Invalid app type: {0}').format(to_app))

    subs = frappe.get_all(subscription_type, filters={"user": user, "enabled": 1}, fields=["raw", "name", "user"])
    vapid_priv = frappe.get_site_config().get("vapid_private_key")
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
            frappe.db.set_value(subscription_type, s["name"], "enabled", 0)
