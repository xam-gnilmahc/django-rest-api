from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    # Get default error response from DRF
    response = exception_handler(exc, context)

    if response is not None:
        # Ensure response data is always a dict and add status_code key
        if isinstance(response.data, dict):
            response.data["status_code"] = response.status_code
        else:
            # In case response.data is not a dict (rare), convert it
            response.data = {
                "detail": response.data,
                "status_code": response.status_code,
            }
    else:
        # For unhandled exceptions, return a generic JSON response with 500
        return Response(
            {"error": "Internal server error", "status_code": 500}, status=500
        )

    return response
