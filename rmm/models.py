import hashlib
import secrets
import uuid

from django.conf import settings
from django.db import models


def _hash_secret(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class Agent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    hostname = models.CharField(max_length=255, db_index=True)
    os_name = models.CharField(max_length=255, blank=True)
    os_version = models.CharField(max_length=255, blank=True)
    fingerprint = models.CharField(max_length=255, unique=True, db_index=True)
    token_hash = models.CharField(max_length=64, editable=False)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)

    class Meta:
        ordering = ["hostname"]

    def set_token(self, raw_secret: str) -> None:
        self.token_hash = _hash_secret(raw_secret)

    def verify_token(self, raw_secret: str) -> bool:
        return self.token_hash == _hash_secret(raw_secret)

    @staticmethod
    def format_token(agent_id: uuid.UUID, raw_secret: str) -> str:
        return f"{agent_id}.{raw_secret}"


class ShellSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="shell_sessions")
    working_directory = models.CharField(max_length=1024, blank=True)
    interpreter = models.CharField(max_length=64, default="powershell")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shell_sessions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class RemoteJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    class Kind(models.TextChoices):
        SHELL_INPUT = "shell_input", "Shell input"
        COMMAND = "command", "Command"
        FILE_LIST = "file_list", "File list"
        FILE_UPLOAD = "file_upload", "File upload"
        FILE_DOWNLOAD = "file_download", "File download"
        REGISTRY_GET = "registry_get", "Registry get"
        REGISTRY_SET = "registry_set", "Registry set"
        SERVICE_ACTION = "service_action", "Service action"
        PATCH_SCAN = "patch_scan", "Patch scan"
        PATCH_INSTALL = "patch_install", "Patch install"
        CHOCO_INSTALL = "choco_install", "Chocolatey install"
        SCRIPT_RUN = "script_run", "Script run"
        EVENT_LOG_QUERY = "event_log_query", "Event log query"
        INVENTORY = "inventory", "Inventory"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="jobs")
    kind = models.CharField(max_length=32, choices=Kind.choices)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    payload = models.JSONField(default=dict, blank=True)
    result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_jobs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    shell_session = models.ForeignKey(
        ShellSession,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="jobs",
    )

    class Meta:
        ordering = ["-created_at"]


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=128, db_index=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class InventorySnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="inventory_snapshots")
    hardware = models.JSONField(default=dict, blank=True)
    software = models.JSONField(default=list, blank=True)
    collected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-collected_at"]


class MetricSample(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="metrics")
    key = models.CharField(max_length=64, db_index=True)
    value = models.FloatField()
    meta = models.JSONField(default=dict, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["agent", "key", "-recorded_at"]),
        ]


class NotificationChannel(models.Model):
    class Kind(models.TextChoices):
        EMAIL = "email", "Email"
        WEBHOOK = "webhook", "Webhook"
        SMS = "sms", "SMS"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.kind})"


class AlertRule(models.Model):
    class Metric(models.TextChoices):
        CPU = "cpu_percent", "CPU %"
        MEMORY = "memory_percent", "Memory %"
        DISK_FREE = "disk_free_percent", "Disk free %"
        SERVICE = "service_running", "Service running"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    metric = models.CharField(max_length=64, choices=Metric.choices)
    operator = models.CharField(max_length=8)
    threshold = models.FloatField()
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="alert_rules",
    )
    channel = models.ForeignKey(
        NotificationChannel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class AlertEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name="events")
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="alerts")
    message = models.TextField()
    severity = models.CharField(max_length=16, default="warning")
    payload = models.JSONField(default=dict, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ScheduledTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="scheduled_tasks",
    )
    interpreter = models.CharField(max_length=32, default="powershell")
    script_body = models.TextField()
    cron = models.CharField(max_length=128, default="*/15 * * * *")
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]


def generate_agent_secret() -> str:
    return secrets.token_urlsafe(32)
