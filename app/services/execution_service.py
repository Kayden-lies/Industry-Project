import json
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution import ExecutionStatus
from app.repositories.audit_repository import AuditRepository
from app.repositories.execution_repository import ExecutionRepository
from app.schemas.execution import ExecutionCreate, ExecutionSummaryResponse, ExecutionUpdate
from app.services.audit_service import AuditService


class ExecutionService:
    VALID_TRANSITIONS: dict[ExecutionStatus, set[ExecutionStatus]] = {
        ExecutionStatus.PENDING: {ExecutionStatus.RUNNING},
        ExecutionStatus.RUNNING: {ExecutionStatus.COMPLETED, ExecutionStatus.FAILED},
        ExecutionStatus.COMPLETED: set(),
        ExecutionStatus.FAILED: set(),
    }

    SUMMARY_CACHE_KEY = "execution_summary_v1"
    SUMMARY_CACHE_TTL_SECONDS = 60

    def __init__(self, session: AsyncSession, redis_client: Redis):
        self.session = session
        self.execution_repo = ExecutionRepository(session)
        self.audit_service = AuditService(AuditRepository(session))
        self.audit_repo = AuditRepository(session)
        self.redis_client = redis_client

    async def create_execution(self, payload: ExecutionCreate, actor: str):
        execution = await self.execution_repo.create(
            job_name=payload.job_name,
            user=actor,
            inputs=payload.inputs,
        )

        await self.audit_service.append_audit_log(
            execution_id=execution.id,
            action="EXECUTION_CREATED",
            actor=actor,
            metadata={"status": execution.status.value},
        )
        await self.session.commit()
        await self.session.refresh(execution)
        await self._invalidate_summary_cache()
        return execution

    async def update_execution(self, execution_id: uuid.UUID, payload: ExecutionUpdate, actor: str):
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")

        if payload.status not in self.VALID_TRANSITIONS[execution.status]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid state transition from {execution.status.value} to {payload.status.value}"
                ),
            )

        now = datetime.now(UTC)
        if payload.status == ExecutionStatus.RUNNING and execution.started_at is None:
            execution.started_at = now

        execution.status = payload.status
        execution.outputs = payload.outputs if payload.outputs is not None else execution.outputs
        execution.error_details = (
            payload.error_details if payload.error_details is not None else execution.error_details
        )

        if payload.status in {ExecutionStatus.COMPLETED, ExecutionStatus.FAILED}:
            execution.completed_at = now
            if execution.started_at:
                execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()

        await self.audit_service.append_audit_log(
            execution_id=execution.id,
            action="EXECUTION_STATUS_UPDATED",
            actor=actor,
            metadata={
                "new_status": payload.status.value,
                "outputs": payload.outputs,
                "error_details": payload.error_details,
            },
        )
        await self.session.commit()
        await self.session.refresh(execution)
        await self._invalidate_summary_cache()
        return execution

    async def list_executions(
        self,
        page: int,
        page_size: int,
        job_name: str | None,
        status: ExecutionStatus | None,
        user: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ):
        return await self.execution_repo.list_filtered(
            page=page,
            page_size=page_size,
            job_name=job_name,
            status=status,
            user=user,
            date_from=date_from,
            date_to=date_to,
        )

    async def get_audit_logs(self, execution_id: uuid.UUID):
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
        return await self.audit_repo.list_for_execution(execution_id)

    async def get_summary(self) -> ExecutionSummaryResponse:
        cached = await self.redis_client.get(self.SUMMARY_CACHE_KEY)
        if cached:
            parsed = json.loads(cached)
            return ExecutionSummaryResponse(**parsed)

        total, failures, avg_duration = await self.execution_repo.get_summary_metrics()
        success_count = max(total - failures, 0)
        success_rate = (success_count / total * 100.0) if total > 0 else 0.0

        summary = ExecutionSummaryResponse(
            success_rate=round(success_rate, 2),
            failure_count=failures,
            avg_duration_seconds=round(avg_duration, 2),
        )
        await self.redis_client.setex(
            self.SUMMARY_CACHE_KEY,
            self.SUMMARY_CACHE_TTL_SECONDS,
            summary.model_dump_json(),
        )
        return summary

    async def _invalidate_summary_cache(self) -> None:
        await self.redis_client.delete(self.SUMMARY_CACHE_KEY)
