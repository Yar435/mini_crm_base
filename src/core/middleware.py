import uuid

from django.utils.deprecation import MiddlewareMixin
from .request_id import set_request_id, get_request_id


REQUEST_ID_HEADER_IN  = "HTTP_X_REQUEST_ID"     # входящее имя у Django (с HTTP_)
REQUEST_ID_HEADER_OUT = "X-Request-ID"          # что отдадим наружу


class RequestIDMiddleware(MiddlewareMixin):
    def process_request(self, request):
        rid = request.META.get(REQUEST_ID_HEADER_IN) or uuid.uuid4().hex
        set_request_id(rid)

    def process_response(self, request, response):
        rid = get_request_id()
        if rid and REQUEST_ID_HEADER_OUT not in response:
            response[REQUEST_ID_HEADER_OUT] = rid
        # очистка не обязательна (contextvar «перепишется»), но аккуратнее:
        set_request_id(None)
        return response
