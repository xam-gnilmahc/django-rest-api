# cron/email.py

import os
import requests
from typing import List, Dict, Optional, Any, Union
from django.http import JsonResponse, HttpRequest, HttpResponse
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

SERVICE_ID: Optional[str] = os.getenv("EMAILJS_SERVICE_ID")
TEMPLATE_ID: Optional[str] = os.getenv("EMAILJS_TEMPLATE_ID")
PUBLIC_KEY: Optional[str] = os.getenv("EMAILJS_PUBLIC_KEY")
ADMIN_EMAIL: Optional[str] = os.getenv("ADMIN_EMAIL")
ORG_NAME: Optional[str] = os.getenv("ORG_NAME")
GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")

HEADERS: Dict[str, str] = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

SKIP_REPOS: List[str] = ["test-11", "cron"]
KEEP_BRANCHES: List[str] = ["production", "main", "staging", "development"]


def generate_pr_table(entries: List[GithubPRLog]) -> str:
    if not entries:
        return "<p style='font-family:sans-serif; color:#374151;'>No pull requests for today.</p>"

    header = (
        "<table style='width:100%; border-collapse:collapse; "
        "font-family:ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont; "
        "font-size:14px; margin-top:12px; border:1px solid #e5e7eb;'>"
        "<thead>"
        "<tr style='background-color:#f3f4f6; color:#111827;'>"
        "<th style='padding:10px 12px; border-bottom:1px solid #e5e7eb;'>PR #</th>"
        "<th style='padding:10px 12px; border-bottom:1px solid #e5e7eb;'>Title</th>"
        "<th style='padding:10px 12px; border-bottom:1px solid #e5e7eb;'>User</th>"
        "<th style='padding:10px 12px; border-bottom:1px solid #e5e7eb;'>Action</th>"
        "<th style='padding:10px 12px; border-bottom:1px solid #e5e7eb;'>State</th>"
        "<th style='padding:10px 12px; border-bottom:1px solid #e5e7eb;'>Link</th>"
        "</tr>"
        "</thead><tbody>"
    )

    rows = ""
    for i, e in enumerate(entries):
        bg = "#ffffff" if i % 2 == 0 else "#f9fafb"  # zebra rows

        rows += (
            f"<tr style='background-color:{bg}; color:#374151;'>"
            f"<td style='padding:10px 12px; border-bottom:1px solid #e5e7eb;'>{e.pr_number}</td>"
            f"<td style='padding:10px 12px; border-bottom:1px solid #e5e7eb;'>{e.title}</td>"
            f"<td style='padding:10px 12px; border-bottom:1px solid #e5e7eb;'>{e.username}</td>"
            f"<td style='padding:10px 12px; border-bottom:1px solid #e5e7eb;'>{e.action}</td>"
            f"<td style='padding:10px 12px; border-bottom:1px solid #e5e7eb;'>{e.state}</td>"
            f"<td style='padding:10px 12px; border-bottom:1px solid #e5e7eb;'>"
            f"<a href='{e.url}' "
            f"style='color:#2563eb; text-decoration:none; font-weight:500;' "
            f"target='_blank'>View PR</a></td>"
            f"</tr>"
        )

    footer = "</tbody></table>"
    return header + rows + footer


@csrf_exempt
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def send_summary_email(request: HttpRequest) -> HttpResponse:
    try:
        today = datetime.now().date()
        start = make_aware(
            datetime.combine(today - timedelta(days=1), datetime.min.time())
        )
        end = make_aware(
            datetime.combine(today - timedelta(days=1), datetime.max.time())
        )

        pr_logs = GithubPRLog.objects.filter(
            action="opened"
        )

        if not pr_logs.exists():
            return JsonResponse({"message": "No PR logs for yesterday."})

        pr_html: str = generate_pr_table(list(pr_logs))

        payload: Dict[str, Union[str, Dict[str, str]]] = {
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


@csrf_exempt
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def GitHubCleanBranches(request: HttpRequest) -> HttpResponse:
    try:
        repos_url: str = f"https://api.github.com/orgs/{ORG_NAME}/repos?per_page=100"
        repos_res = requests.get(repos_url, headers=HEADERS)
        repos: List[Dict[str, Any]] = repos_res.json()

        deleted_branches: Dict[str, List[str]] = {}

        for repo in repos:
            repo_name: str = repo["name"]
            if repo_name in SKIP_REPOS or repo.get("archived"):
                continue

            branches_url: str = (
                f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/branches"
            )
            branches_res = requests.get(branches_url, headers=HEADERS)
            branches: List[Dict[str, Any]] = branches_res.json()

            for branch in branches:
                branch_name: str = branch["name"]
                if branch_name in KEEP_BRANCHES:
                    continue

                if branch.get("protected"):
                    protection_url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/branches/{branch_name}/protection"
                    requests.delete(protection_url, headers=HEADERS)

                ref_url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/git/refs/heads/{branch_name}"
                delete_res = requests.delete(ref_url, headers=HEADERS)

                if delete_res.status_code == 204:
                    deleted_branches.setdefault(repo_name, []).append(branch_name)

        return JsonResponse(
            {"message": "Branches deleted successfully", "deleted": deleted_branches},
            status=200,
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
