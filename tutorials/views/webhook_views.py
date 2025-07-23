import json
import urllib.parse
import logging
import hmac
import hashlib
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny
from tutorials.utils.response_helper import error_response, success_response
from tutorials.models.webhook import GithubPRLog  # Import your model here

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

    secret = b"7reb9d$g$mhgw0_)@y%+jh=$bnj9f*)v4zz1b4b-p+^^=zd8(d"
    body = request.body
    expected_signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_signature, signature):
        logger.warning("Invalid signature")
        return HttpResponseForbidden("Invalid signature")
    
    delivery_id = request.headers.get("X-GitHub-Delivery")
    if GithubPRLog.objects.filter(delivery_id=delivery_id).exists():
        return success_response("Duplicate webhook ignored")

    try:
        body_str = body.decode("utf-8")
        logger.info(f"Raw request body: {body_str!r}")

        if body_str.startswith("payload="):
            parsed = urllib.parse.parse_qs(body_str)
            payload_str = parsed.get("payload", [None])[0]
            if payload_str is None:
                raise ValueError("No 'payload' field in body")
            payload = json.loads(payload_str)
        else:
            payload = json.loads(body_str)

        pr_number = payload["number"]
        pr = payload["pull_request"]
        title = pr["title"]
        pr_body = pr["body"]
        pr_url = pr["html_url"]
        username = pr["user"]["login"]
        action = payload["action"]
        state = pr["state"]
        url = pr["html_url"]

        GithubPRLog.objects.create(
            delivery_id=delivery_id,
            pr_number=pr_number,
            title=title,
            body=pr_body,
            pr_url=pr_url,
            username=username,
            action=action,
            state=state,
            url=url,
        )
        return success_response("Pull request data logged")

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return error_response(str(e))
