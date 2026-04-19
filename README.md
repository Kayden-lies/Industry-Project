# Execution Tracking and Audit Service (RS-BE-01)

Production-grade FastAPI backend for execution tracking, immutable hash-chained audit logs, query APIs, and analytics.

## 1) Folder Structure

```text
.
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 20260419_0001_init.py
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/routes/executions.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── audit_log.py
│   │   └── execution.py
│   ├── repositories/
│   │   ├── audit_repository.py
│   │   └── execution_repository.py
│   ├── schemas/
│   │   ├── audit_log.py
│   │   └── execution.py
│   ├── services/
│   │   ├── audit_service.py
│   │   └── execution_service.py
│   └── main.py
├── .env.example
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## 2) Implemented API Contract

- `POST   /api/v1/executions`
- `PATCH  /api/v1/executions/{id}`
- `GET    /api/v1/executions`
- `GET    /api/v1/executions/{id}/audit`
- `GET    /api/v1/executions/summary`

All endpoints are JWT protected and RBAC enforced (`ADMIN`, `ANALYST`, `VIEWER`).

## 3) Core Capabilities

- Execution lifecycle tracking with persisted status + timing.
- FSM enforcement: `PENDING -> RUNNING -> COMPLETED|FAILED` only.
- Append-only audit logs with SHA-256 hash chaining.
- Query filtering by `job_name`, `status`, `date range`, `user` + pagination.
- Cached summary analytics in Redis (`60s` TTL).

## 4) Run Locally (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Service will be available at: `http://localhost:8000`

## 5) Run Without Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## 6) JWT Token Notes

Expected JWT payload:

```json
{
  "sub": "alice",
  "role": "ADMIN"
}
```

Signed with `JWT_SECRET_KEY` and `JWT_ALGORITHM` from `.env`.

## 7) Design Notes for Performance

- DB indexes on key filter columns: `job_name`, `status`, `user`, and audit lookup keys.
- Async SQLAlchemy + asyncpg for non-blocking I/O.
- Redis summary caching reduces repeated aggregate query cost.
- Layered architecture isolates routing, business logic, persistence, and core concerns.
