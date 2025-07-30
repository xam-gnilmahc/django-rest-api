from typing import Any, Dict
from tutorials.models.payment_log import PaymentLog


class PaymentLogRepository:
    def create_log(self, data: Dict[str, Any]) -> PaymentLog:
        return PaymentLog.objects.create(payment_gateway_name="stripe", **data)
