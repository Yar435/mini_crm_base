import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="core.heartbeat")
def heartbeat():
    logger.info("heartbeat tick")
    return "ok"
