# tutorials/serializers/auth_serializers.py

from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


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
