from django.db.models import Sum, Count, Case, When, FloatField
from django.db.models.functions import TruncDate, TruncMonth, ExtractHour
from django.utils.timezone import now
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from tutorials.utils.response_helper import error_response, success_response
from tutorials.models.payment_log import PaymentLog


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_analytics(request):
    try:
        today = now()
        # Get days from request, default 30
        days = int(request.GET.get("days", 30))
        start_date = today - timedelta(days=days)

        # Filter all logs to only this period
        logs = PaymentLog.objects.filter(created_at__range=(start_date, today))

        # Aggregates
        aggregates = logs.aggregate(
            total_earned=Sum(
                Case(
                    When(status="1", then="amount"),
                    default=0,
                    output_field=FloatField(),
                )
            ),
            total_refunded=Sum(
                Case(
                    When(status="3", then="amount"),
                    default=0,
                    output_field=FloatField(),
                )
            ),
            total_transactions=Count(Case(When(status="1", then=1))),
            failed_transactions=Count(Case(When(status="3", then=1))),
        )

        total_transactions = aggregates["total_transactions"]
        failed_transactions = aggregates["failed_transactions"]
        total_attempts = total_transactions + failed_transactions
        success_ratio = (total_transactions / total_attempts) if total_attempts else 0
        average_transaction = (
            aggregates["total_earned"] / total_transactions if total_transactions else 0
        )

        # Successful transactions only
        successful_logs = logs.filter(status="1")

        # Line chart: revenue per day
        line_chart = (
            successful_logs.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Sum("amount"))
            .order_by("day")
        )

        # Monthly revenue
        monthly_stats = (
            successful_logs.annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total_amount=Sum("amount"), transaction_count=Count("id"))
            .order_by("month")
        )

        # Hourly transactions
        hourly_transactions = (
            successful_logs.annotate(hour=ExtractHour("created_at"))
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )

        # Pie chart: revenue by payment gateway
        pie_chart = (
            successful_logs.values("payment_gateway_name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

        # Payment gateway stats
        gateway_stats = (
            logs.values("payment_gateway_name")
            .annotate(
                total=Count("id"),
                success=Count(Case(When(status="1", then=1))),
                success_rate=100 * Count(Case(When(status="1", then=1))) / Count("id"),
            )
            .order_by("-success_rate")
        )

        return success_response(
            message="Payment analytics fetched successfully",
            data={
                "stats": {
                    "total_earned": float(aggregates["total_earned"] or 0),
                    "total_transactions": total_transactions,
                    "average_transaction": float(average_transaction or 0),
                    "total_refunded": float(aggregates["total_refunded"] or 0),
                    "failed_transactions": failed_transactions,
                    "success_ratio": round(success_ratio, 2),
                },
                "line_chart": list(line_chart),
                "monthly_revenue": list(monthly_stats),
                "pie_chart": list(pie_chart),
                "gateway_stats": list(gateway_stats),
                "hourly_transactions": list(hourly_transactions),
            },
        )

    except Exception as e:
        return error_response(str(e))
