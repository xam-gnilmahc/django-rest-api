from django.db.models import Sum, Count, Case, When, FloatField
from django.db.models.functions import TruncDate, TruncMonth, ExtractWeekDay, ExtractHour
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
        # Filter successful payments only
        success_payments = PaymentLog.objects.filter(status="1")

        # Calculate total earnings
        total_earned = success_payments.aggregate(total=Sum('amount'))['total'] or 0

        # Count total successful transactions
        total_transactions = success_payments.count()

        # Calculate average transaction value
        average_transaction = total_earned / total_transactions if total_transactions else 0

        # Calculate date 7 days ago for filtering
        seven_days_ago = now() - timedelta(days=7)

        # Calculate date 6 months ago for monthly stats
        six_months_ago = now() - timedelta(days=180)

        # Line chart: revenue per day for last 7 days
        line_chart = (
            success_payments
            .filter(created_at__gte=seven_days_ago)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(total=Sum('amount'))
            .order_by('day')
        )

        # Pie chart: revenue grouped by payment gateway (all time)
        pie_chart = (
            success_payments
            .values('payment_gateway_name')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )

        # Bar chart: transaction counts per day for last 7 days
        bar_chart = (
            success_payments
            .filter(created_at__gte=seven_days_ago)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        # Weekday stats: revenue and transactions by weekday
        weekday_stats = (
            success_payments
            .annotate(weekday=ExtractWeekDay('created_at'))  # Sunday=1 .. Saturday=7
            .values('weekday')
            .annotate(
                total_amount=Sum('amount'),
                transaction_count=Count('id'),
            )
            .order_by('weekday')
        )

        # Monthly revenue (last 6 months)
        monthly_revenue = (
            success_payments
            .filter(created_at__gte=six_months_ago)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )

        # Refunds and failed payments summary
        total_refunded = PaymentLog.objects.filter(status="3").aggregate(total=Sum('amount'))['total'] or 0
        failed_transactions = PaymentLog.objects.filter(status="3").count()
        total_attempts = total_transactions + failed_transactions
        success_ratio = (total_transactions / total_attempts) if total_attempts > 0 else 0

        # Payment gateway success rate
        gateway_stats = (
            PaymentLog.objects
            .values('payment_gateway_name')
            .annotate(
                total=Count('id'),
                success=Count(Case(When(status="1", then=1))),
                success_rate=100 * Count(Case(When(status="1", then=1))) / Count('id'),
            )
            .order_by('-success_rate')
        )

        # Hourly transaction distribution (last 7 days)
        hourly_transactions = (
            success_payments
            .filter(created_at__gte=seven_days_ago)
            .annotate(hour=ExtractHour('created_at'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
        )

        return success_response(
            message="Payment analytics fetched successfully",
            data={
                "stats": {
                    "total_earned": float(total_earned),
                    "total_transactions": total_transactions,
                    "average_transaction": float(average_transaction),
                    "total_refunded": float(total_refunded),
                    "failed_transactions": failed_transactions,
                    "success_ratio": round(success_ratio, 2),
                },
                "line_chart": list(line_chart),
                "pie_chart": list(pie_chart),
                "bar_chart": list(bar_chart),
                "weekday_stats": list(weekday_stats),
                "monthly_revenue": list(monthly_revenue),
                # "top_customers": list(top_customers),
                "gateway_stats": list(gateway_stats),
                "hourly_transactions": list(hourly_transactions),
            }
        )
    except Exception as e:
        return error_response(str(e))
