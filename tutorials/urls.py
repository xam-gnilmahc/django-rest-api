from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from tutorials.views.auth_views import login_view, register_view
from tutorials.views.user_payment_views import userPaymentGateway_list
from tutorials.views.webhook_views import github_webhook
from tutorials.views.stripe_webhook import stripe_webhook
from tutorials.cron.email import send_summary_email, GitHubCleanBranches

urlpatterns = [
    path("admin/", admin.site.urls),
    # Auth routes
    path("api/login", login_view, name="login"),
    path("api/register", register_view, name="register"),
    path("api/github/feed", github_webhook, name="github_Webhook"),
    path("api/stripe/feed", stripe_webhook, name="stripe_webhook"),
    path("api/email/send", send_summary_email, name="send_summary_email"),
    path("api/cron/github", GitHubCleanBranches, name="GitHubCleanBranches"),
    path("api/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    # Payment gateway routes
    path("api/paymentGateways", userPaymentGateway_list, name="payment_gateways"),
]
