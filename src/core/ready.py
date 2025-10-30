import os

import redis
from django.db import connections
from django.http import JsonResponse


def ready(request):
    # Database connectivity check
    connections["default"].cursor().execute("SELECT 1;")

    # Redis connectivity check
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    client = redis.from_url(redis_url)
    client.ping()

    return JsonResponse({"ready": True})
