# cron/email.py
import os
import requests
from django.http import JsonResponse
from tutorials.models.webhook import GithubPRLog
from dotenv import load_dotenv
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt

load_dotenv()

SERVICE_ID = os.getenv("EMAILJS_SERVICE_ID")
TEMPLATE_ID = os.getenv("EMAILJS_TEMPLATE_ID")
PUBLIC_KEY = os.getenv("EMAILJS_PUBLIC_KEY")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")


def generate_pr_table(entries):
    if not entries:
        return "<p>No pull requests for today.</p>"

    header = (
        "<table style='width:100%; border-collapse:collapse; font-family:sans-serif; font-size:14px; margin-top:10px;'>"
        "<thead><tr style='background:#f2f2f2;'>"
        "<th style='border:1px solid #ddd; padding:8px;'>PR Number</th>"
        "<th style='border:1px solid #ddd; padding:8px;'>Title</th>"
        "<th style='border:1px solid #ddd; padding:8px;'>User</th>"
        "<th style='border:1px solid #ddd; padding:8px;'>Action</th>"
        "<th style='border:1px solid #ddd; padding:8px;'>State</th>"
        "<th style='border:1px solid #ddd; padding:8px;'>URL</th>"
        "</tr></thead><tbody>"
    )
    rows = "".join(
        f"<tr>"
        f"<td style='border:1px solid #ddd; padding:8px;'>{e.pr_number}</td>"
        f"<td style='border:1px solid #ddd; padding:8px;'>{e.title}</td>"
        f"<td style='border:1px solid #ddd; padding:8px;'>{e.username}</td>"
        f"<td style='border:1px solid #ddd; padding:8px;'>{e.action}</td>"
        f"<td style='border:1px solid #ddd; padding:8px;'>{e.state}</td>"
        f"<td style='border:1px solid #ddd; padding:8px;'><a href='{e.url}'>View PR</a></td>"
        f"</tr>"
        for e in entries
    )
    footer = "</tbody></table>"
    return header + rows + footer


@csrf_exempt
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def send_summary_email(request):
    try:
        # Time range for yesterday
        today = datetime.now().date()
        start = make_aware(
            datetime.combine(today - timedelta(days=1), datetime.min.time())
        )
        end = make_aware(
            datetime.combine(today - timedelta(days=1), datetime.max.time())
        )

        pr_logs = GithubPRLog.objects.filter(created_at__range=(start, end))

        if not pr_logs.exists():
            return JsonResponse({"message": "No PR logs for yesterday."})

        pr_html = generate_pr_table(pr_logs)

        payload = {
            "service_id": SERVICE_ID,
            "template_id": TEMPLATE_ID,
            "user_id": PUBLIC_KEY,
            "template_params": {
                "email": ADMIN_EMAIL,
                "pr_table": pr_html,
            },
        }

        res = requests.post(
            "https://api.emailjs.com/api/v1.0/email/send",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if res.ok:
            return JsonResponse({"message": "✅ Email sent successfully."})
        return JsonResponse(
            {"message": "❌ Failed to send email.", "details": res.text}, status=500
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
