from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from tutorials.serializers.auth_serializers import (LoginSerializer,
                                                    RegisterSerializer)
from tutorials.utils.response_helper import error_response, success_response


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return error_response(
                "Invalid credentials.", status_code=status.HTTP_401_UNAUTHORIZED
            )

        user = authenticate(request, username=user_obj.username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return success_response(
                "Login successful.",
                data={
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                    "tokens": {
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                    },
                },
            )
        return error_response(
            "Invalid credentials.", status_code=status.HTTP_401_UNAUTHORIZED
        )

    return error_response("Validation failed.", errors=serializer.errors)


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            is_superuser=data.get("is_superuser", 1),
        )
        return success_response(
            "User registered successfully.",
            data={"id": user.id, "username": user.username, "email": user.email},
            status_code=status.HTTP_201_CREATED,
        )

    return error_response("Validation failed.", errors=serializer.errors)
