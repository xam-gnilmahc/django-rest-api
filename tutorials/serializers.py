import json

from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from tutorials.models import UserPaymentGateway


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=True,
        min_length=4,
        max_length=30,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(), message="Username is already taken."
            )
        ],
    )
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(), message="Email is already registered."
            )
        ],
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        max_length=128,
        style={"input_type": "password"},
    )
    first_name = serializers.CharField(required=True, max_length=50)
    last_name = serializers.CharField(required=True, max_length=50)

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name")


class LoginSerializer(serializers.ModelSerializer):

    def validate_email_exists(value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email not found.")
        return value

    email = serializers.EmailField(required=True, validators=[validate_email_exists])
    password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        max_length=128,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ["email", "password"]


class UserPaymentGatewaySerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=True)
    payment_gateway_id = serializers.IntegerField(required=True)
    payment_gateway_name = serializers.CharField(required=True, max_length=255)
    credentials = serializers.JSONField(
        required=True
    )  # required=True ensures it must be present

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
