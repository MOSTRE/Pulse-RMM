import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_shell_output(session_id: str, result: dict) -> None:
    payload = {
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "exit_code": result.get("exit_code"),
    }
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"shell_{session_id}",
        {
            "type": "terminal.output",
            "text": json.dumps(payload),
        },
    )
