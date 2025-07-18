from django.contrib import admin
from django.utils.html import format_html

from .models import UserPaymentGateway, GithubPRLog

# Admin branding
admin.site.site_header = "Max Chamling"
admin.site.site_title = "My Admin Portal"
admin.site.index_title = "Welcome to the Admin Panel"


@admin.register(UserPaymentGateway)
class UserPaymentGatewayAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_id",
        "short_credentials",
        "payment_gateway_name",
        "status",
        "is_live_mode",
        "has_apple_pay",
        "has_google_pay",
        "has_card_pay",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "is_live_mode",
        "has_card_pay",
        "has_apple_pay",
        "has_google_pay",
        "payment_gateway_name",
        "created_at",
    )

    search_fields = ("payment_gateway_name", "credentials", "user_id")

    def short_credentials(self, obj):
        content = obj.credentials or ""
        return format_html('<span title="{}">{}...</span>', content, content[:50])

    short_credentials.short_description = "Credentials"


@admin.register(GithubPRLog)
class GithubPRLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "pr_number",
        "title",
        "body",
        "username",
        "action",
        "state",
        "created_at",
        "url",
    )
    list_filter = ("action", "state", "username", "created_at")
    search_fields = ("pr_number", "title", "username", "pr_url", "body")
