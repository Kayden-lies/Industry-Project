from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_execution_service
from app.core.security import Role, TokenPayload, get_current_user, require_roles
from app.models.execution import ExecutionStatus
from app.schemas.audit_log import AuditLogListResponse, AuditLogResponse
from app.schemas.execution import (
    ExecutionCreate,
    ExecutionListResponse,
    ExecutionResponse,
    ExecutionSummaryResponse,
    ExecutionUpdate,
)
if TYPE_CHECKING:
    from app.services.execution_service import ExecutionService


router = APIRouter(prefix="/executions", tags=["executions"])


@router.post(
    "",
    response_model=ExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.ANALYST))],
)
async def create_execution(
    payload: ExecutionCreate,
    service: Annotated[ExecutionService, Depends(get_execution_service)],
    user: Annotated[TokenPayload, Depends(get_current_user)],
):
    return await service.create_execution(payload, actor=user.sub)


@router.patch(
    "/{execution_id}",
    response_model=ExecutionResponse,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.ANALYST))],
)
async def update_execution(
    execution_id: uuid.UUID,
    payload: ExecutionUpdate,
    service: Annotated[ExecutionService, Depends(get_execution_service)],
    user: Annotated[TokenPayload, Depends(get_current_user)],
):
    return await service.update_execution(execution_id=execution_id, payload=payload, actor=user.sub)


@router.get(
    "",
    response_model=ExecutionListResponse,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.ANALYST, Role.VIEWER))],
)
async def list_executions(
    service: Annotated[ExecutionService, Depends(get_execution_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    job_name: str | None = Query(default=None),
    status: ExecutionStatus | None = Query(default=None),
    user: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
):
    items, total = await service.list_executions(
        page=page,
        page_size=page_size,
        job_name=job_name,
        status=status,
        user=user,
        date_from=date_from,
        date_to=date_to,
    )
    return ExecutionListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/summary",
    response_model=ExecutionSummaryResponse,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.ANALYST, Role.VIEWER))],
)
async def execution_summary(service: Annotated[ExecutionService, Depends(get_execution_service)]):
    return await service.get_summary()


@router.get(
    "/{execution_id}/audit",
    response_model=AuditLogListResponse,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.ANALYST, Role.VIEWER))],
)
async def get_execution_audit(
    execution_id: uuid.UUID,
    service: Annotated[ExecutionService, Depends(get_execution_service)],
):
    logs = await service.get_audit_logs(execution_id)
    return AuditLogListResponse(
        execution_id=str(execution_id),
        logs=[
            AuditLogResponse(
                action=log.action,
                actor=log.actor,
                timestamp=log.created_at,
                metadata=log.metadata_json,
                previous_hash=log.previous_hash,
                current_hash=log.current_hash,
            )
            for log in logs
        ],
    )
