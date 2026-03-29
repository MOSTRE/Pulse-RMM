import uuid

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from rmm.models import Agent


class AgentPrincipal:
    is_authenticated = True

    def __init__(self, agent: Agent):
        self.agent = agent
        self.pk = agent.pk

    def __str__(self) -> str:
        return f"agent:{self.agent.hostname}"


class AgentTokenAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = request.META.get("HTTP_AUTHORIZATION")
        if not header or not header.startswith(f"{self.keyword} "):
            return None
        raw = header[len(self.keyword) + 1 :].strip()
        parts = raw.split(".", 1)
        if len(parts) != 2:
            return None
        aid, secret = parts
        try:
            uuid.UUID(aid)
        except ValueError as exc:
            raise AuthenticationFailed("Invalid agent token") from exc
        agent = Agent.objects.filter(id=aid).first()
        if not agent or not agent.verify_token(secret):
            raise AuthenticationFailed("Invalid agent credentials")
        return (AgentPrincipal(agent), None)


def is_agent_principal(user) -> bool:
    return isinstance(user, AgentPrincipal)
