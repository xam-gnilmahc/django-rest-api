import json
import hmac
import hashlib
import logging
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view

# Setup logger
logger = logging.getLogger(__name__)
handler = logging.FileHandler("github_webhook.log")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@csrf_exempt
@api_view(["POST"])
def github_webhook(request):
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        logger.warning("Missing signature")
        return HttpResponseForbidden("Missing signature")

    # Calculate HMAC SHA-256 hash
    secret = "7reb9d$g$mhgw0_)@y%+jh=$bnj9f*)v4zz1b4b-p+^^=zd8(d"
    body = request.body
    expected_signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        logger.warning("Invalid signature")
        return HttpResponseForbidden("Invalid signature")

    try:
        payload = json.loads(body)
        event = request.headers.get("X-GitHub-Event", "unknown")

        # Log the event name and full payload
        logger.info(f"Received GitHub Event: {event}")
        logger.info(json.dumps(payload, indent=2))  # Pretty-printed payload

        return JsonResponse({"status": "logged", "event": event})
    except Exception as e:
        logger.error(f"Error parsing webhook payload: {e}")
        return JsonResponse({"error": str(e)}, status=400)
