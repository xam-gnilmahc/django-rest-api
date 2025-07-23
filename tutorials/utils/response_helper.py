# utils/response_helper.py

from rest_framework.response import Response
from rest_framework import status


def success_response(message, data=None, status_code=status.HTTP_200_OK):
    return Response(
        {"status": True, "message": message, "data": data}, status=status_code
    )


def error_response(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response(
        {"status": False, "message": message, "errors": errors}, status=status_code
    )
