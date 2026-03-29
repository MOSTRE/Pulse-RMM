from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rmm import audit
from rmm.alerts import evaluate_rules_for_agent
from rmm.authentication import AgentTokenAuthentication
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
    generate_agent_secret,
)
from rmm.permissions import IsAgentUser, IsOperator
from rmm.serializers import (
    AgentEnrollmentSerializer,
    AgentSerializer,
    AlertEventSerializer,
    AlertRuleSerializer,
    AuditLogSerializer,
    HeartbeatSerializer,
    InventorySnapshotSerializer,
    JobCompleteSerializer,
    MetricSampleSerializer,
    NotificationChannelSerializer,
    RemoteJobAgentSerializer,
    RemoteJobSerializer,
    ScheduledTaskSerializer,
    ShellSessionSerializer,
)
from rmm.utils import broadcast_shell_output


class AgentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [IsOperator]


class RemoteJobViewSet(viewsets.ModelViewSet):
    queryset = RemoteJob.objects.select_related("agent", "created_by", "shell_session")
    serializer_class = RemoteJobSerializer
    permission_classes = [IsOperator]
    filterset_fields = ("agent", "kind", "status")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        job = serializer.instance
        audit.log_action(
            "job.create",
            agent=job.agent,
            actor=self.request.user,
            details={"job_id": str(job.id), "kind": job.kind},
        )


class ShellSessionViewSet(viewsets.ModelViewSet):
    queryset = ShellSession.objects.select_related("agent", "created_by")
    serializer_class = ShellSessionSerializer
    permission_classes = [IsOperator]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="input")
    def input_line(self, request, pk=None):
        session = self.get_object()
        line = request.data.get("line", "")
        job = RemoteJob.objects.create(
            agent=session.agent,
            kind=RemoteJob.Kind.SHELL_INPUT,
            payload={"line": line},
            shell_session=session,
            created_by=request.user,
        )
        audit.log_action(
            "shell.input",
            agent=session.agent,
            actor=request.user,
            details={"session_id": str(session.id), "job_id": str(job.id)},
        )
        return Response(RemoteJobSerializer(job).data, status=status.HTTP_201_CREATED)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("agent", "actor")
    serializer_class = AuditLogSerializer
    permission_classes = [IsOperator]
    filterset_fields = ("agent", "action")


class InventorySnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventorySnapshot.objects.select_related("agent")
    serializer_class = InventorySnapshotSerializer
    permission_classes = [IsOperator]
    filterset_fields = ("agent",)


class MetricSampleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MetricSample.objects.select_related("agent")
    serializer_class = MetricSampleSerializer
    permission_classes = [IsOperator]
    filterset_fields = ("agent", "key")


class NotificationChannelViewSet(viewsets.ModelViewSet):
    queryset = NotificationChannel.objects.all()
    serializer_class = NotificationChannelSerializer
    permission_classes = [IsOperator]


class AlertRuleViewSet(viewsets.ModelViewSet):
    queryset = AlertRule.objects.select_related("agent", "channel")
    serializer_class = AlertRuleSerializer
    permission_classes = [IsOperator]


class AlertEventViewSet(viewsets.ModelViewSet):
    queryset = AlertEvent.objects.select_related("rule", "agent")
    serializer_class = AlertEventSerializer
    permission_classes = [IsOperator]
    http_method_names = ["get", "head", "options", "patch", "put"]


class ScheduledTaskViewSet(viewsets.ModelViewSet):
    queryset = ScheduledTask.objects.select_related("agent")
    serializer_class = ScheduledTaskSerializer
    permission_classes = [IsOperator]


class EnrollAgentView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = AgentEnrollmentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        if data["enrollment_key"] != settings.RMM_ENROLLMENT_KEY:
            return Response({"detail": "Invalid enrollment key"}, status=status.HTTP_403_FORBIDDEN)
        if Agent.objects.filter(fingerprint=data["fingerprint"]).exists():
            return Response({"detail": "Fingerprint already enrolled"}, status=status.HTTP_409_CONFLICT)
        secret = generate_agent_secret()
        agent = Agent(
            name=data["name"],
            hostname=data["hostname"],
            fingerprint=data["fingerprint"],
            os_name=data.get("os_name") or "",
            os_version=data.get("os_version") or "",
        )
        agent.set_token(secret)
        agent.save()
        token = Agent.format_token(agent.id, secret)
        audit.log_action("agent.enroll", agent=agent, details={"hostname": agent.hostname})
        return Response(
            {
                "agent_id": str(agent.id),
                "token": token,
                "message": "Token is not returned again.",
            },
            status=status.HTTP_201_CREATED,
        )


class AgentHeartbeatView(APIView):
    authentication_classes = [AgentTokenAuthentication]
    permission_classes = [IsAgentUser]

    def post(self, request):
        agent = request.user.agent
        ser = HeartbeatSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        now = timezone.now()
        agent.last_seen_at = now
        agent.is_online = True
        agent.save(update_fields=["last_seen_at", "is_online"])

        for key, val in (
            ("cpu_percent", d.get("cpu_percent")),
            ("memory_percent", d.get("memory_percent")),
            ("disk_free_percent", d.get("disk_free_percent")),
        ):
            if val is not None:
                MetricSample.objects.create(agent=agent, key=key, value=float(val))
        extra = d.get("metrics") or {}
        for k, v in extra.items():
            try:
                MetricSample.objects.create(agent=agent, key=str(k)[:64], value=float(v))
            except (TypeError, ValueError):
                continue

        evaluate_rules_for_agent(agent)
        return Response({"ok": True, "server_time": now.isoformat()})


class AgentPendingJobsView(APIView):
    authentication_classes = [AgentTokenAuthentication]
    permission_classes = [IsAgentUser]

    def get(self, request):
        agent = request.user.agent
        jobs = RemoteJob.objects.filter(
            agent=agent, status=RemoteJob.Status.PENDING
        ).order_by("created_at")[:25]
        return Response(RemoteJobAgentSerializer(jobs, many=True).data)


class AgentJobStartView(APIView):
    authentication_classes = [AgentTokenAuthentication]
    permission_classes = [IsAgentUser]

    def post(self, request, job_id):
        agent = request.user.agent
        with transaction.atomic():
            job = (
                RemoteJob.objects.select_for_update()
                .filter(id=job_id, agent=agent)
                .first()
            )
            if not job:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if job.status != RemoteJob.Status.PENDING:
                return Response(
                    {"detail": "Job not pending"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            job.status = RemoteJob.Status.RUNNING
            job.started_at = timezone.now()
            job.save(update_fields=["status", "started_at"])
        return Response(RemoteJobAgentSerializer(job).data)


class AgentJobCompleteView(APIView):
    authentication_classes = [AgentTokenAuthentication]
    permission_classes = [IsAgentUser]

    def post(self, request, job_id):
        agent = request.user.agent
        ser = JobCompleteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        with transaction.atomic():
            job = (
                RemoteJob.objects.select_for_update()
                .filter(id=job_id, agent=agent)
                .first()
            )
            if not job:
                return Response(status=status.HTTP_404_NOT_FOUND)
            job.status = data["status"]
            job.result = data.get("result")
            job.error_message = data.get("error_message") or ""
            job.completed_at = timezone.now()
            job.save(
                update_fields=["status", "result", "error_message", "completed_at"]
            )

        if (
            job.kind == RemoteJob.Kind.SHELL_INPUT
            and job.shell_session_id
            and job.result
        ):
            broadcast_shell_output(str(job.shell_session_id), job.result)

        if job.kind == RemoteJob.Kind.INVENTORY and job.result:
            InventorySnapshot.objects.create(
                agent=agent,
                hardware=job.result.get("hardware") or {},
                software=job.result.get("software") or [],
            )

        audit.log_action(
            "job.complete",
            agent=agent,
            details={"job_id": str(job.id), "status": job.status},
        )
        return Response({"ok": True})


@api_view(["GET"])
@permission_classes([AllowAny])
def health(_request):
    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([IsOperator])
def fleet_stats(request):
    agents = Agent.objects.count()
    online = Agent.objects.filter(is_online=True).count()
    pending = RemoteJob.objects.filter(status=RemoteJob.Status.PENDING).count()
    alerts_open = AlertEvent.objects.filter(acknowledged_at__isnull=True).count()
    return Response(
        {
            "agents_total": agents,
            "agents_online": online,
            "jobs_pending": pending,
            "alerts_open": alerts_open,
        }
    )
