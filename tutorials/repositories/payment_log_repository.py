from tutorials.models.payment_log import PaymentLog
from django.utils.timezone import now

class PaymentLogRepository:
    def create_log(self, data: dict):
        return PaymentLog.objects.create(
            payment_gateway_name="stripe",
            transaction_id=data["transaction_id"],
            amount=data["amount"],
            currency=data["currency"],
            status=data["status"],
            request_data=data["request_data"],
            response_data=data["response_data"],
            created_at=now(),
            updated_at=now(),
        )
