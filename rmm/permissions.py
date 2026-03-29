from rest_framework import permissions

from rmm.authentication import AgentPrincipal, is_agent_principal


class IsOperator(permissions.BasePermission):
    def has_permission(self, request, view):
        if is_agent_principal(request.user):
            return False
        return bool(request.user and request.user.is_authenticated)


class IsAgentUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.user, AgentPrincipal)
