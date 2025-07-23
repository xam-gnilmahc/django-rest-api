import logging
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny

from tutorials.services.github_webhook_service import GithubWebhookService
from tutorials.utils.response_helper import success_response, error_response

logger = logging.getLogger(__name__)
secret = b"7reb9d$g$mhgw0_)@y%+jh=$bnj9f*)v4zz1b4b-p+^^=zd8(d"


@csrf_exempt
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def github_webhook(request):
    svc = GithubWebhookService(request, secret)
    if not svc.validate_signature():
        return HttpResponseForbidden("Invalid signature")
    if svc.is_duplicate():
        return success_response("Duplicate")
    try:
        return success_response(svc.process())
    except Exception as e:
        logger.exception("Webhook error")
        return error_response(str(e))
