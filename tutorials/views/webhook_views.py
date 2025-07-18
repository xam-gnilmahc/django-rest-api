import json
import urllib.parse
import logging
import hmac
import hashlib
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny

from tutorials.models import GithubPRLog  # Import your model here

logger = logging.getLogger(__name__)
handler = logging.FileHandler("github_webhook.log")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


@csrf_exempt
@api_view(["POST"])
@authentication_classes([])  # Disable authentication for webhook
@permission_classes([AllowAny])
def github_webhook(request):
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        logger.warning("Missing signature")
        return HttpResponseForbidden("Missing signature")

    secret = b"7reb9d$g$mhgw0_)@y%+jh=$bnj9f*)v4zz1b4b-p+^^=zd8(d"  # Your actual secret here (as bytes)
    body = request.body
    expected_signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_signature, signature):
        logger.warning("Invalid signature")
        return HttpResponseForbidden("Invalid signature")

    try:
        body_str = body.decode("utf-8")
        logger.info(f"Raw request body: {body_str!r}")

        if body_str.startswith("payload="):
            # parse URL-encoded form data
            parsed = urllib.parse.parse_qs(body_str)
            payload_str = parsed.get("payload", [None])[0]
            if payload_str is None:
                raise ValueError("No 'payload' field in body")

            payload = json.loads(payload_str)
        else:
            # parse as raw JSON
            payload = json.loads(body_str)

        pretty_payload = json.dumps(payload, indent=2)
        logger.info(f"Parsed payload: {pretty_payload}")

        pr_number = payload["number"]
        pr = payload["pull_request"]
        title = pr["title"]
        pr_body = pr["body"]
        pr_url = pr["html_url"]
        username = pr["user"]["login"]
        action = payload["action"]
        state = pr["state"]

        GithubPRLog.objects.create(
            pr_number=pr_number,
            title=title,
            body=pr_body,
            pr_url=pr_url,
            username=username,
            action=action,
            state=state,
        )

        return JsonResponse({"status": "logged"})

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JsonResponse({"error": str(e)}, status=400)
