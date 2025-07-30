import os
import stripe
import json
from typing import Optional, Dict, Any, Union

from tutorials.repositories.payment_log_repository import PaymentLogRepository


class StripeWebhookService:
    def __init__(self, payload: bytes, sig_header: str) -> None:
        self.payload: bytes = payload
        self.sig: str = sig_header
        self.secret: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
        self.repo: PaymentLogRepository = PaymentLogRepository()

    def verify_event(self) -> stripe.Event:
        return stripe.Webhook.construct_event(
            self.payload,
            self.sig,
            self.secret,
        )

    def process_event(self, event: stripe.Event) -> Dict[str, Union[bool, str]]:
        obj: Dict[str, Any] = event["data"]["object"]
        event_type: str = event["type"]

        status: Optional[str] = {
            "payment_intent.created": "2",
            "payment_intent.succeeded": "1",
            "payment_intent.payment_failed": "0",
        }.get(event_type)

        if status is None:
            return {"skip": True, "event_type": event_type}

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
