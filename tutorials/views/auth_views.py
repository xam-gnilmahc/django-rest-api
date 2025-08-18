import requests
from typing import Optional, Dict, Any

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpRequest
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import redirect
from tutorials.utils.response_helper import error_response, success_response
from urllib.parse import urlencode

# Google OAuth endpoints
GOOGLE_AUTH_URI = settings.GOOGLE_AUTH_URI
GOOGLE_TOKEN_URI = settings.GOOGLE_TOKEN_URI
GOOGLE_USERINFO_URI = settings.GOOGLE_USERINFO_URI
FRONTEND_REDIRECT_URL = settings.FRONTEND_REDIRECT_URL


@api_view(["GET"])
@permission_classes([AllowAny])
def google_redirect_view(request: HttpRequest) -> Response:
    """
    Redirects user to Google's OAuth2 consent screen.
    """
    params: Dict[str, str] = {
        "client_id": settings.GOOGLE_CLIENT_ID.strip(),
        "redirect_uri": settings.GOOGLE_REDIRECT_URL.strip(),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }

    url: str = f"{GOOGLE_AUTH_URI}?{urlencode(params)}"
    return redirect(url)


@api_view(["GET"])
@permission_classes([AllowAny])
def google_callback_view(request: HttpRequest) -> Response:
    """
    Handles Google's OAuth2 callback: gets token, fetches user info, logs in existing user.
    """
    code: Optional[str] = request.GET.get("code")
    if not code:
        params = urlencode({"message": "Missing authorization code"})
        return redirect(f"{FRONTEND_REDIRECT_URL}/login?{params}")

    token_data: Dict[str, str] = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID.strip(),
        "client_secret": settings.GOOGLE_CLIENT_SECRET.strip(),
        "redirect_uri": settings.GOOGLE_REDIRECT_URL.strip(),
        "grant_type": "authorization_code",
    }

    token_res: requests.Response = requests.post(GOOGLE_TOKEN_URI, data=token_data)
    if not token_res.ok:
        return error_response("Failed to get access token from Google", status_code=400)

    token_json: Dict[str, Any] = token_res.json()
    access_token: Optional[str] = token_json.get("access_token")
    if not access_token:
        return error_response("No access token returned by Google", status_code=400)

    user_res: requests.Response = requests.get(
        GOOGLE_USERINFO_URI, headers={"Authorization": f"Bearer {access_token}"}
    )
    if not user_res.ok:
        return error_response("Failed to fetch user info from Google", status_code=400)

    user_info: Dict[str, Any] = user_res.json()
    email: Optional[str] = user_info.get("email")

    if not email:
        #return error_response("Email not available in Google response", status_code=400)
        params = urlencode({"message": "Email not available from Google"})
        return redirect(f"{FRONTEND_REDIRECT_URL}/login?{params}")

    try:
        user: User = User.objects.get(email=email)
    except User.DoesNotExist:
        # return error_response(
        #     "No account associated with this Google email. Contact your admin.",
        #     status_code=403,
        # )
        params = urlencode({"message": "No account associated with this Google email"})
        return redirect(f"{FRONTEND_REDIRECT_URL}/login?{params}")

    refresh: RefreshToken = RefreshToken.for_user(user)
    # return success_response(
    #     "Login successful via Google.",
    #     data={
    #         "accessToken": {
    #             "access": str(refresh.access_token),
    #             "refresh": str(refresh),
    #         },
    #     },
    # )
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    # ✅ Redirect back to React app with tokens in query params
    query_params = urlencode(
        {
            "access": access_token,
            "refresh": refresh_token,
        }
    )
    print(FRONTEND_REDIRECT_URL)
    return redirect(f"{FRONTEND_REDIRECT_URL}/verify?{query_params}")
