import logging

import requests

from rmm.models import NotificationChannel

logger = logging.getLogger(__name__)


def send_channel_message(
    channel: NotificationChannel,
    title: str,
    body: str,
    payload: dict | None = None,
) -> None:
    if not channel.is_active:
        return
    if channel.kind == NotificationChannel.Kind.WEBHOOK:
        url = channel.config.get("url")
        if not url:
            logger.warning("Webhook channel %s has no url", channel.id)
            return
        try:
            requests.post(
                url,
                json={"title": title, "body": body, "payload": payload or {}},
                timeout=15,
            )
        except requests.RequestException as exc:
            logger.exception("Webhook notify failed: %s", exc)
    elif channel.kind == NotificationChannel.Kind.EMAIL:
        logger.info("email %s: %s", title, body)
    elif channel.kind == NotificationChannel.Kind.SMS:
        logger.info("sms %s: %s", title, body)
