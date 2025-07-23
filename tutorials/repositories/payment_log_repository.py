from tutorials.models.payment_log import PaymentLog


class PaymentLogRepository:
    def create_log(self, data: dict):
        return PaymentLog.objects.create(payment_gateway_name="stripe", **data)
