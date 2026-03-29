from typing import Optional

from django.contrib.auth.models import User

from rmm.models import Agent, AuditLog


def log_action(
    action: str,
    *,
    agent: Optional[Agent] = None,
    actor: Optional[User] = None,
    details: Optional[dict] = None,
) -> None:
    AuditLog.objects.create(
        agent=agent,
        actor=actor,
        action=action,
        details=details or {},
    )
