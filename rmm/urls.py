from django.urls import include, path
from rest_framework.routers import DefaultRouter

from rmm import views

router = DefaultRouter()
router.register("agents", views.AgentViewSet, basename="agent")
router.register("jobs", views.RemoteJobViewSet, basename="job")
router.register("shell-sessions", views.ShellSessionViewSet, basename="shellsession")
router.register("audit-logs", views.AuditLogViewSet, basename="auditlog")
router.register("inventory", views.InventorySnapshotViewSet, basename="inventory")
router.register("metrics", views.MetricSampleViewSet, basename="metric")
router.register(
    "notification-channels",
    views.NotificationChannelViewSet,
    basename="notificationchannel",
)
router.register("alert-rules", views.AlertRuleViewSet, basename="alertrule")
router.register("alerts", views.AlertEventViewSet, basename="alertevent")
router.register("scheduled-tasks", views.ScheduledTaskViewSet, basename="scheduledtask")

urlpatterns = [
    path("", include(router.urls)),
    path("health/", views.health),
    path("fleet/stats/", views.fleet_stats),
    path("auth/enroll/", views.EnrollAgentView.as_view()),
    path("agent/heartbeat/", views.AgentHeartbeatView.as_view()),
    path("agent/jobs/pending/", views.AgentPendingJobsView.as_view()),
    path("agent/jobs/<uuid:job_id>/start/", views.AgentJobStartView.as_view()),
    path("agent/jobs/<uuid:job_id>/complete/", views.AgentJobCompleteView.as_view()),
]
