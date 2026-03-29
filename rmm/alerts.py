from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from rmm.models import AlertEvent, AlertRule, MetricSample, NotificationChannel
from rmm.notify import send_channel_message


def _compare(op: str, left: float, right: float) -> bool:
    if op == "gt":
        return left > right
    if op == "gte":
        return left >= right
    if op == "lt":
        return left < right
    if op == "lte":
        return left <= right
    if op == "eq":
        return left == right
    return False


def evaluate_rules_for_agent(agent) -> None:
    now = timezone.now()
    rules = AlertRule.objects.filter(is_active=True).filter(
        Q(agent__isnull=True) | Q(agent=agent)
    )
    for rule in rules:
        if rule.last_triggered_at and (now - rule.last_triggered_at) < timedelta(minutes=5):
            continue
        sample = (
            MetricSample.objects.filter(agent=agent, key=rule.metric)
            .order_by("-recorded_at")
            .first()
        )
        if not sample:
            continue
        if not _compare(rule.operator, sample.value, rule.threshold):
            continue
        msg = (
            f"{rule.name}: {rule.metric}={sample.value} "
            f"{rule.operator} {rule.threshold} on {agent.hostname}"
        )
        ev = AlertEvent.objects.create(
            rule=rule,
            agent=agent,
            message=msg,
            severity="warning",
            payload={"metric": sample.key, "value": sample.value},
        )
        rule.last_triggered_at = now
        rule.save(update_fields=["last_triggered_at"])
        if rule.channel_id:
            ch = NotificationChannel.objects.filter(pk=rule.channel_id).first()
            if ch:
                send_channel_message(ch, rule.name, msg, {"alert_id": str(ev.id)})
