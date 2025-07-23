import os, stripe, json
from tutorials.repositories.payment_log_repository import PaymentLogRepository


class StripeWebhookService:
    def __init__(self, payload: bytes, sig_header: str):
        self.payload = payload
        self.sig = sig_header
        self.secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        self.repo = PaymentLogRepository()

    def verify_event(self):
        return stripe.Webhook.construct_event(self.payload, self.sig, self.secret)

    def process_event(self, event):
        obj, t = event["data"]["object"], event["type"]
        status = {
            "payment_intent.created": "2",
            "payment_intent.succeeded": "1",
            "payment_intent.payment_failed": "0",
        }.get(t)
        if status is None:
            return {"skip": True, "event_type": t}

        self.repo.create_log(
            {
                "transaction_id": obj.get("id"),
                "amount": obj.get("amount_received", 0) / 100,
                "currency": obj.get("currency", "usd"),
                "status": status,
                "request_data": self.payload.decode(),
                "response_data": json.dumps(obj),
            }
        )
        return {"success": True}
