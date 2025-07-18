from django.contrib.auth.models import User
from django.db import models


class UserPaymentGateway(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="payment_gateways"
    )

    payment_gateway_id = models.BigIntegerField()
    payment_gateway_name = models.CharField(max_length=255)
    credentials = models.TextField()

    STATUS_CHOICES = [("0", "Inactive"), ("1", "Active")]
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="1")
    is_live_mode = models.CharField(max_length=1, choices=STATUS_CHOICES, default="1")
    has_apple_pay = models.CharField(max_length=1, choices=STATUS_CHOICES, default="0")
    has_google_pay = models.CharField(max_length=1, choices=STATUS_CHOICES, default="0")
    has_card_pay = models.CharField(max_length=1, choices=STATUS_CHOICES, default="1")

    created_by = models.BigIntegerField(default=0)
    updated_by = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_payment_gateway"
