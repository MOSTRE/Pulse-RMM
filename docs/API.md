# API reference

Base path: `/api/v1/`

## Auth

| Method | Path | Body | Notes |
|--------|------|------|--------|
| POST | `/auth/token/` | `username`, `password` | JWT access + refresh |
| POST | `/auth/token/refresh/` | `refresh` | New access token |
| POST | `/auth/enroll/` | `enrollment_key`, `name`, `hostname`, `fingerprint`, optional `os_name`, `os_version` | No JWT; returns `agent_id` and one-time `token` |

Operator requests (except enroll and health): header `Authorization: Bearer <access_jwt>`.

Agent requests: `Authorization: Bearer <agent_uuid>.<secret>`.

## Health

| Method | Path | Auth |
|--------|------|------|
| GET | `/health/` | None |

## Operator (JWT)

ViewSets are under the router; typical paths:

| Resource | Path prefix |
|----------|-------------|
| Agents | `/agents/` |
| Jobs | `/jobs/` |
| Shell sessions | `/shell-sessions/` |
| Audit logs | `/audit-logs/` |
| Inventory snapshots | `/inventory/` |
| Metrics | `/metrics/` |
| Notification channels | `/notification-channels/` |
| Alert rules | `/alert-rules/` |
| Alerts | `/alerts/` |
| Scheduled tasks | `/scheduled-tasks/` |

| Method | Path | Notes |
|--------|------|--------|
| GET | `/fleet/stats/` | Aggregate counts |

Shell input (after creating a session): `POST /shell-sessions/<uuid>/input/` with JSON `{"line": "..."}`.

## Agent (Bearer agent token)

| Method | Path | Notes |
|--------|------|--------|
| POST | `/agent/heartbeat/` | Metrics: `cpu_percent`, `memory_percent`, `disk_free_percent`, optional `metrics` object |
| GET | `/agent/jobs/pending/` | Pending jobs |
| POST | `/agent/jobs/<uuid>/start/` | Mark running |
| POST | `/agent/jobs/<uuid>/complete/` | JSON: `status` (`completed` \| `failed`), `result`, `error_message` |

## WebSocket

Browser shell stream (JWT in query string):

`ws://<host>/ws/shell/<shell_session_uuid>/?token=<access_jwt>`

Message payload is JSON text from server when the agent completes a `shell_input` job with `stdout` / `stderr` in `result`.
