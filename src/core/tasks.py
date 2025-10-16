import logging
from typing import Literal

from celery import shared_task
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

HEARTBEAT_KEY = "celery:heartbeat:beat"
HEARTBEAT_TTL = 5 * 60  # 5 минут


@shared_task
def heartbeat() -> Literal["ok"]:
    """
    Легковесная задача проверки жизнеспособности, вызываемая
    сервисом Celery beat.
    Используется для смоук-тестов и предупреждений.
    ---
    Lightweight liveness task executed by Celery beat.
    Used for smoke-checks and alert wiring.
    """
    now = timezone.now().isoformat()
    cache.set(HEARTBEAT_KEY, now, timeout=HEARTBEAT_TTL)
    logger.info("heartbeat tick at %s", now)
    return "ok"
