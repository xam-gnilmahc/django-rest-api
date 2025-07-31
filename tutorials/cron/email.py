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
        "<thead>"
        "<tr style='background:#e5e7eb; text-align:left; font-weight:normal;'>"
        "<th style='padding:10px 12px;'>PR Number</th>"
        "<th style='padding:10px 12px;'>Title</th>"
        "<th style='padding:10px 12px;'>User</th>"
        "<th style='padding:10px 12px;'>Action</th>"
        "<th style='padding:10px 12px;'>State</th>"
        "<th style='padding:10px 12px;'>URL</th>"
        "</tr>"
        "</thead>"
        "<tbody>"
    )

    rows = "".join(
        f"<tr style='background:#fff; transition:background-color 0.3s;' "
        f"onmouseover=\"this.style.backgroundColor='#f9fafb';\" "
        f"onmouseout=\"this.style.backgroundColor='#fff';\">"
        f"<td style='padding:10px 12px; color:#444;'>{e.pr_number}</td>"
        f"<td style='padding:10px 12px; color:#444;'>{e.title}</td>"
        f"<td style='padding:10px 12px; color:#444;'>{e.username}</td>"
        f"<td style='padding:10px 12px; color:#444;'>{e.action}</td>"
        f"<td style='padding:10px 12px; color:#444;'>{e.state}</td>"
        f"<td style='padding:10px 12px;'><a href='{e.url}' "
        f"style='color:#1a73e8; text-decoration:none;' target='_blank'>View PR</a></td>"
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

        pr_logs = GithubPRLog.objects.filter(
            created_at__range=(start, end), action="opened"
        )

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
