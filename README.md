# Pulse RMM (server)

Django 6 project: dashboard UI, REST API for operators, agent enrollment and job queue, Channels WebSockets for shell output, scheduled task dispatcher.

## Requirements

- Python 3.11+
- Dependencies in `requirements.txt`

## Setup

```powershell
cd "path\to\github project"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

## Configuration

| Variable | Purpose |
|----------|---------|
| `DJANGO_SETTINGS_MODULE` | Default: `rmm_platform.settings` |
| `RMM_ENROLLMENT_KEY` | Shared secret for `POST /api/v1/auth/enroll/` (defaults in settings for dev only) |
| `SECRET_KEY` | Set in production (see `rmm_platform/settings.py`) |

Development uses SQLite and in-memory Channels. Use PostgreSQL + Redis channel layer for production multi-process deployments.

## Run

HTTP and WebSockets require ASGI (not `runserver` alone):

```powershell
python -m daphne -b 127.0.0.1 -p 8000 rmm_platform.asgi:application
```

- Dashboard: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`
- API: `http://127.0.0.1:8000/api/v1/` — [docs/API.md](docs/API.md), [docs/README.md](docs/README.md)

Operator auth: JWT via `POST /api/v1/auth/token/`. Agent auth: `Authorization: Bearer <agent_uuid>.<secret>` after enrollment.

## Scheduler

Cron-style rows in `ScheduledTask` are processed by:

```powershell
python manage.py run_scheduler
```

Run once per minute from the OS scheduler.

## Layout

| Path | Role |
|------|------|
| `rmm_platform/` | Settings, root URLs, ASGI/WSGI |
| `rmm/` | Models, API, WebSocket consumer, alerts, notifications |
| `dashboard/` | Django templates (UI shell) |
| `docs/` | API notes |

## License

Unspecified — add your own.
