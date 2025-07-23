import os
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from tutorials.services.stripe_webhook_service import StripeWebhookService
from tutorials.utils.response_helper import success_response, error_response
from rest_framework import status


@csrf_exempt
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    service = StripeWebhookService(payload, sig_header)

    try:
        event = service.verify_event()
    except ValueError:
        return error_response(
            "Invalid payload", status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception:
        return error_response(
            "Invalid signature or internal error",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    result = service.process_event(event)

    if result.get("skip"):
        return success_response(
            "Event type ignored", {"event_type": result["event_type"]}
        )

    return success_response("Payment event processed successfully")
