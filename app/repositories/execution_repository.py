import uuid
from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution import Execution, ExecutionStatus


class ExecutionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, job_name: str, user: str, inputs: dict | None) -> Execution:
        execution = Execution(job_name=job_name, user=user, inputs=inputs, status=ExecutionStatus.PENDING)
        self.session.add(execution)
        await self.session.flush()
        return execution

    async def get_by_id(self, execution_id: uuid.UUID) -> Execution | None:
        result = await self.session.execute(select(Execution).where(Execution.id == execution_id))
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        page: int,
        page_size: int,
        job_name: str | None,
        status: ExecutionStatus | None,
        user: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> tuple[list[Execution], int]:
        filters = []
        if job_name:
            filters.append(Execution.job_name == job_name)
        if status:
            filters.append(Execution.status == status)
        if user:
            filters.append(Execution.user == user)
        if date_from:
            filters.append(Execution.created_at >= date_from)
        if date_to:
            filters.append(Execution.created_at <= date_to)

        where_clause = and_(*filters) if filters else None

        base_query = select(Execution)
        count_query = select(func.count(Execution.id))
        if where_clause is not None:
            base_query = base_query.where(where_clause)
            count_query = count_query.where(where_clause)

        base_query = base_query.order_by(Execution.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(base_query)
        count_result = await self.session.execute(count_query)

        return list(result.scalars().all()), int(count_result.scalar_one())

    async def get_summary_metrics(self) -> tuple[int, int, float]:
        total_result = await self.session.execute(select(func.count(Execution.id)))
        failure_result = await self.session.execute(
            select(func.count(Execution.id)).where(Execution.status == ExecutionStatus.FAILED)
        )
        avg_duration_result = await self.session.execute(
            select(func.coalesce(func.avg(Execution.duration_seconds), 0.0)).where(
                Execution.status.in_([ExecutionStatus.COMPLETED, ExecutionStatus.FAILED])
            )
        )

        total = int(total_result.scalar_one())
        failures = int(failure_result.scalar_one())
        avg_duration = float(avg_duration_result.scalar_one())
        return total, failures, avg_duration
