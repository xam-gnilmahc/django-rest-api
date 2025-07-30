import json
import urllib.parse
import hmac
import hashlib
import logging
from typing import Optional, Any, Dict

from django.http import HttpRequest
from tutorials.repositories.github_pr_log_repository import GithubPRLogRepository

logger = logging.getLogger(__name__)


class GithubWebhookService:
    def __init__(self, request: HttpRequest, secret: bytes) -> None:
        self.req: HttpRequest = request
        self.secret: bytes = secret
        self.repo: GithubPRLogRepository = GithubPRLogRepository()

    def validate_signature(self) -> bool:
        sig: Optional[str] = self.req.headers.get("X-Hub-Signature-256")
        if not sig:
            return False
        expected: str = (
            "sha256=" + hmac.new(self.secret, self.req.body, hashlib.sha256).hexdigest()
        )
        return hmac.compare_digest(expected, sig)

    def is_duplicate(self) -> bool:
        delivery_id: Optional[str] = self.req.headers.get("X-GitHub-Delivery")
        return self.repo.exists_by_delivery_id(delivery_id)

    def extract_payload(self) -> Dict[str, Any]:
        raw: str = self.req.body.decode("utf-8")
        logger.info(f"Raw request body: {raw!r}")
        if raw.startswith("payload="):
            parsed_payload: str = urllib.parse.parse_qs(raw).get("payload", ["{}"])[0]
            return json.loads(parsed_payload)
        return json.loads(raw)

    def process(self) -> str:
        payload: Dict[str, Any] = self.extract_payload()
        pr: Dict[str, Any] = payload.get("pull_request", {})
        self.repo.create_log(
            {
                "delivery_id": self.req.headers.get("X-GitHub-Delivery"),
                "pr_number": payload.get("number"),
                "title": pr.get("title"),
                "body": pr.get("body"),
                "pr_url": pr.get("html_url"),
                "username": pr.get("user", {}).get("login"),
                "action": payload.get("action"),
                "state": pr.get("state"),
                "url": pr.get("html_url"),
            }
        )
        return "Pull request data logged"
