import json
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from rmm.models import ShellSession


@database_sync_to_async
def _get_shell_session(session_id):
    return ShellSession.objects.filter(pk=session_id).first()


class ShellBrowserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        qs = parse_qs(self.scope.get("query_string", b"").decode())
        token = (qs.get("token") or [None])[0]
        if not token:
            await self.close(code=4401)
            return
        try:
            access = AccessToken(token)
            uid = access["user_id"]
        except (InvalidToken, TokenError, KeyError):
            await self.close(code=4401)
            return

        User = get_user_model()
        try:
            user = await database_sync_to_async(User.objects.get)(pk=uid)
        except User.DoesNotExist:
            await self.close(code=4401)
            return

        session = await _get_shell_session(self.session_id)
        if not session:
            await self.close(code=4404)
            return

        allowed = user.is_staff or (
            session.created_by_id is not None and session.created_by_id == user.id
        )
        if not allowed:
            await self.close(code=4403)
            return

        self.group = f"shell_{self.session_id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def terminal_output(self, event):
        await self.send(text_data=event["text"])
