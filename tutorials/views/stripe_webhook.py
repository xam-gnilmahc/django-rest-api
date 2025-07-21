import os
import stripe
import json
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from tutorials.models.payment_log import PaymentLog
from tutorials.utils.response_helper import error_response, success_response

# Set Stripe secret key from environment
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
# Stripe webhook signing secret from environment
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

@csrf_exempt
@api_view(["POST"])
@authentication_classes([])  # Disable authentication for webhook endpoint
@permission_classes([AllowAny])  # Allow any permission
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    # Verify webhook signature and parse event
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        # Invalid payload data
        return error_response("Invalid payload", status_code=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature header
        return error_response("Invalid signature", status_code=400)
    except Exception:
        # Other errors
        return error_response("Internal Server Error", status_code=500)

    data = event['data']['object']
    transaction_id = data.get("id")
    amount = data.get("amount_received", 0) / 100  # Convert cents to dollars
    currency = data.get("currency", "usd")
    request_data = payload.decode()
    response_data = json.dumps(data)

    # Map Stripe event types to internal status codes
    if event['type'] == 'payment_intent.created':
        status = "2"  # Created but not completed
    elif event['type'] == 'payment_intent.succeeded':
        status = "1"  # Success
    elif event['type'] == 'payment_intent.payment_failed':
        status = "0"  # Failed
    else:
        # Ignore other event types
        return success_response("Event type ignored", {"event_type": event['type']})

    # Save payment log to the database
    PaymentLog.objects.create(
        payment_gateway_name="stripe",
        transaction_id=transaction_id,
        amount=amount,
        currency=currency,
        status=status,
        request_data=request_data,
        response_data=response_data,
        created_at=now(),
        updated_at=now(),
    )

    return success_response("Payment event processed successfully")
