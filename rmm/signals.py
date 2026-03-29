from datetime import datetime

from croniter import croniter
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from rmm.models import ScheduledTask


@receiver(post_save, sender=ScheduledTask)
def set_initial_next_run(sender, instance: ScheduledTask, **_kwargs):
    if instance.next_run_at is not None:
        return
    now = timezone.now()
    itr = croniter(instance.cron, now)
    n = itr.get_next(datetime)
    if timezone.is_naive(n):
        n = timezone.make_aware(n, timezone.get_current_timezone())
    ScheduledTask.objects.filter(pk=instance.pk).update(next_run_at=n)
