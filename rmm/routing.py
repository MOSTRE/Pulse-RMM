from django.urls import re_path

from rmm.consumers import ShellBrowserConsumer

websocket_urlpatterns = [
    re_path(r"ws/shell/(?P<session_id>[0-9a-f-]+)/$", ShellBrowserConsumer.as_asgi()),
]
