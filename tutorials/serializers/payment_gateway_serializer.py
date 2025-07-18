# tutorials/serializers/payment_gateway_serializer.py

import json

from rest_framework import serializers

from tutorials.models.user_payment_gateway import UserPaymentGateway


class UserPaymentGatewaySerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=True)
    payment_gateway_id = serializers.IntegerField(required=True)
    payment_gateway_name = serializers.CharField(required=True, max_length=255)
    credentials = serializers.JSONField(required=True)

    class Meta:
        model = UserPaymentGateway
        fields = [
            "id",
            "user_id",
            "payment_gateway_id",
            "payment_gateway_name",
            "credentials",
            "status",
            "is_live_mode",
            "has_apple_pay",
            "has_google_pay",
            "has_card_pay",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        """Ensure credentials are returned as a JSON object"""
        ret = super().to_representation(instance)
        try:
            ret["credentials"] = json.loads(instance.credentials)
        except Exception:
            pass
        return ret

    def to_internal_value(self, data):
        """Convert credentials dict to JSON string before saving"""
        if "credentials" in data and isinstance(data["credentials"], dict):
            data["credentials"] = json.dumps(data["credentials"])
        return super().to_internal_value(data)

    def validate_credentials(self, value):
        required_keys = ["publishable_key", "secret_key"]
        for key in required_keys:
            if key not in value:
                raise serializers.ValidationError(
                    f"'{key}' is required in credentials."
                )
        return value
