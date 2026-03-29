from datetime import datetime

from croniter import croniter
from django.core.management.base import BaseCommand
from django.utils import timezone

from rmm.models import Agent, RemoteJob, ScheduledTask


class Command(BaseCommand):
    help = "Dispatch due ScheduledTask rows as SCRIPT_RUN jobs (run every minute from the OS scheduler)."

    def handle(self, *args, **options):
        now = timezone.now()
        dispatched = 0
        for task in ScheduledTask.objects.filter(is_active=True):
            if task.next_run_at is None:
                itr = croniter(task.cron, now)
                n = itr.get_next(datetime)
                if timezone.is_naive(n):
                    n = timezone.make_aware(n, timezone.get_current_timezone())
                ScheduledTask.objects.filter(pk=task.pk).update(next_run_at=n)
                continue
            if task.next_run_at > now:
                continue

            agents = (
                [task.agent]
                if task.agent
                else list(Agent.objects.filter(is_online=True))
            )
            for ag in agents:
                RemoteJob.objects.create(
                    agent=ag,
                    kind=RemoteJob.Kind.SCRIPT_RUN,
                    payload={
                        "script": task.script_body,
                        "interpreter": task.interpreter,
                        "scheduled_task_id": str(task.id),
                    },
                    created_by=None,
                )
                dispatched += 1

            itr = croniter(task.cron, now)
            n = itr.get_next(datetime)
            if timezone.is_naive(n):
                n = timezone.make_aware(n, timezone.get_current_timezone())
            task.last_run_at = now
            task.next_run_at = n
            task.save(update_fields=["last_run_at", "next_run_at"])
            self.stdout.write(self.style.SUCCESS(f"Dispatched: {task.name}"))

        if dispatched:
            self.stdout.write(self.style.NOTICE(f"Total jobs created: {dispatched}"))
