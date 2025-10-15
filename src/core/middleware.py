# core/middleware.py
import uuid

from django.utils.deprecation import MiddlewareMixin


class RequestIDMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    def process_response(self, request, response):
        rid = getattr(request, "id", None)
        if rid:
            response["X-Request-ID"] = rid
        return response
