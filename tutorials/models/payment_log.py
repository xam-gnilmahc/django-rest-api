from django.contrib.auth.models import User
from django.db import models


class PaymentLog(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="payment_logs"
    )

    payment_gateway_name = models.CharField(max_length=255)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")

    STATUS_CHOICES = [("0", "Failed"), ("1", "Success"), ("2", "Pending")]
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="2")

    response_data = models.TextField(blank=True, null=True)  # full gateway response
    request_data = models.TextField(blank=True, null=True)   # request sent to gateway

    created_by = models.BigIntegerField(default=0)
    updated_by = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payment_logs"
        ordering = ["-created_at"]