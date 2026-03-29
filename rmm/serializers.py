from rest_framework import serializers

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


class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = (
            "id",
            "name",
            "hostname",
            "os_name",
            "os_version",
            "fingerprint",
            "enrolled_at",
            "last_seen_at",
            "is_online",
        )
        read_only_fields = fields


class AgentEnrollmentSerializer(serializers.Serializer):
    enrollment_key = serializers.CharField(write_only=True)
    name = serializers.CharField(max_length=255)
    hostname = serializers.CharField(max_length=255)
    fingerprint = serializers.CharField(max_length=255)
    os_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    os_version = serializers.CharField(max_length=255, required=False, allow_blank=True)


class HeartbeatSerializer(serializers.Serializer):
    cpu_percent = serializers.FloatField(required=False, allow_null=True)
    memory_percent = serializers.FloatField(required=False, allow_null=True)
    disk_free_percent = serializers.FloatField(required=False, allow_null=True)
    metrics = serializers.JSONField(required=False, default=dict)


class RemoteJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemoteJob
        fields = (
            "id",
            "agent",
            "kind",
            "status",
            "payload",
            "result",
            "error_message",
            "created_by",
            "created_at",
            "started_at",
            "completed_at",
            "shell_session",
        )
        read_only_fields = (
            "status",
            "result",
            "error_message",
            "created_at",
            "started_at",
            "completed_at",
            "created_by",
        )


class RemoteJobAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemoteJob
        fields = (
            "id",
            "kind",
            "status",
            "payload",
            "result",
            "error_message",
            "created_at",
            "shell_session",
        )


class ShellSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShellSession
        fields = (
            "id",
            "agent",
            "working_directory",
            "interpreter",
            "is_active",
            "created_at",
            "closed_at",
            "created_by",
        )
        read_only_fields = ("created_at", "closed_at", "created_by")


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ("id", "agent", "actor", "action", "details", "created_at")
        read_only_fields = fields


class InventorySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventorySnapshot
        fields = ("id", "agent", "hardware", "software", "collected_at")
        read_only_fields = fields


class MetricSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetricSample
        fields = ("id", "agent", "key", "value", "meta", "recorded_at")
        read_only_fields = fields


class NotificationChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationChannel
        fields = ("id", "name", "kind", "config", "is_active")


class AlertRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertRule
        fields = (
            "id",
            "name",
            "metric",
            "operator",
            "threshold",
            "agent",
            "channel",
            "is_active",
            "last_triggered_at",
        )


class AlertEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertEvent
        fields = (
            "id",
            "rule",
            "agent",
            "message",
            "severity",
            "payload",
            "acknowledged_at",
            "created_at",
        )
        read_only_fields = (
            "id",
            "rule",
            "agent",
            "message",
            "severity",
            "payload",
            "created_at",
        )


class ScheduledTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledTask
        fields = (
            "id",
            "name",
            "agent",
            "interpreter",
            "script_body",
            "cron",
            "is_active",
            "last_run_at",
            "next_run_at",
            "created_at",
        )
        read_only_fields = ("last_run_at", "next_run_at", "created_at")


class JobCompleteSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=RemoteJob.Status.choices)
    result = serializers.JSONField(required=False, allow_null=True)
    error_message = serializers.CharField(required=False, allow_blank=True)
