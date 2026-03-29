from django.contrib import admin

from rmm.models import (
    Agent,
    AlertEvent,
    AlertRule,
    AuditLog,
    InventorySnapshot,
    MetricSample,
    NotificationChannel,
    RemoteJob,
    ScheduledTask,
    ShellSession,
)


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("hostname", "name", "os_name", "is_online", "last_seen_at")
    search_fields = ("hostname", "name", "fingerprint")


@admin.register(RemoteJob)
class RemoteJobAdmin(admin.ModelAdmin):
    list_display = ("id", "agent", "kind", "status", "created_at")
    list_filter = ("status", "kind")


@admin.register(ShellSession)
class ShellSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "agent", "interpreter", "is_active", "created_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "agent", "actor")
    list_filter = ("action",)


@admin.register(InventorySnapshot)
class InventorySnapshotAdmin(admin.ModelAdmin):
    list_display = ("agent", "collected_at")


@admin.register(MetricSample)
class MetricSampleAdmin(admin.ModelAdmin):
    list_display = ("agent", "key", "value", "recorded_at")


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "is_active")


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "metric", "operator", "threshold", "is_active")


@admin.register(AlertEvent)
class AlertEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "rule", "agent", "severity", "acknowledged_at")


@admin.register(ScheduledTask)
class ScheduledTaskAdmin(admin.ModelAdmin):
    list_display = ("name", "cron", "is_active", "next_run_at", "last_run_at")
