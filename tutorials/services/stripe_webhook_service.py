import os
import stripe
import json
from tutorials.repositories.payment_log_repository import PaymentLogRepository


class StripeWebhookService:
    def __init__(self, payload: bytes, sig_header: str):
        self.payload = payload
        self.sig_header = sig_header
        self.endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        self.repo = PaymentLogRepository()

    def verify_event(self):
        return stripe.Webhook.construct_event(
            self.payload, self.sig_header, self.endpoint_secret
        )

    def process_event(self, event):
        data = event["data"]["object"]
        event_type = event["type"]

        # Map event type to status
        if event_type == "payment_intent.created":
            status = "2"
        elif event_type == "payment_intent.succeeded":
            status = "1"
        elif event_type == "payment_intent.payment_failed":
            status = "0"
        else:
            return {"skip": True, "event_type": event_type}

        log_data = {
            "transaction_id": data.get("id"),
            "amount": data.get("amount_received", 0) / 100,
            "currency": data.get("currency", "usd"),
            "status": status,
            "request_data": self.payload.decode(),
            "response_data": json.dumps(data),
        }

        self.repo.create_log(log_data)
        return {"success": True}
