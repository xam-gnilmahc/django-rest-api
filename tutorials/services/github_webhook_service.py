import json
import urllib.parse
import hmac
import hashlib
import logging

from django.http import HttpRequest
from tutorials.repositories.github_pr_log_repository import GithubPRLogRepository

logger = logging.getLogger(__name__)


class GithubWebhookService:
    def __init__(self, request: HttpRequest, secret: bytes):
        self.request = request
        self.secret = secret
        self.repo = GithubPRLogRepository()

    def validate_signature(self) -> bool:
        signature = self.request.headers.get("X-Hub-Signature-256")
        if not signature:
            logger.warning("Missing signature")
            return False

        body = self.request.body
        expected = "sha256=" + hmac.new(self.secret, body, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected, signature):
            logger.warning("Invalid signature")
            return False
        return True

    def is_duplicate(self) -> bool:
        delivery_id = self.request.headers.get("X-GitHub-Delivery")
        return self.repo.exists_by_delivery_id(delivery_id)

    def extract_payload(self) -> dict:
        body = self.request.body
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

        return payload

    def process(self) -> str:
        delivery_id = self.request.headers.get("X-GitHub-Delivery")
        payload = self.extract_payload()
        pr = payload["pull_request"]

        data = {
            "delivery_id": delivery_id,
            "pr_number": payload["number"],
            "title": pr["title"],
            "body": pr["body"],
            "pr_url": pr["html_url"],
            "username": pr["user"]["login"],
            "action": payload["action"],
            "state": pr["state"],
            "url": pr["html_url"],
        }

        self.repo.create_log(data)
        return "Pull request data logged"
