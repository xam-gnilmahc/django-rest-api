import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
import json
from tutorials.utils.response_helper import error_response, success_response


@api_view(["GET"])
@permission_classes([])
def get_book_info(request):
    isbn = request.GET.get("isbn")
    if not isbn:
        return error_response("ISBN parameter is required", status=400)

    try:
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        response = requests.get(url)
        data = response.json()

        if not data:
            return error_response("Book not found", status=404)

        # Debug: print JSON data
        print(json.dumps(data, indent=2))

        key = f"ISBN:{isbn}"
        book_data = data.get(key, {})

        if not book_data:
            return error_response("Book data not found for the given ISBN", status=404)

        result = {
            "title": book_data.get("title"),
            "authors": [author["name"] for author in book_data.get("authors", [])],
            "publish_date": book_data.get("publish_date"),
            "publishers": [pub["name"] for pub in book_data.get("publishers", [])],
            "number_of_pages": book_data.get("number_of_pages"),
        }

        return success_response(result)

    except Exception as e:
        print(e)
        return error_response("Internal server error", details=str(e), status=500)
