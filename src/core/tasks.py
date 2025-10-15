import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def heartbeat():
    logger.info("heartbeat tick")
    return "ok"
