import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_last_log(self, execution_id: uuid.UUID) -> AuditLog | None:
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.execution_id == execution_id)
            .order_by(AuditLog.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def append_log(
        self,
        execution_id: uuid.UUID,
        action: str,
        actor: str,
        metadata: dict | None,
        previous_hash: str | None,
        current_hash: str,
    ) -> AuditLog:
        log = AuditLog(
            execution_id=execution_id,
            action=action,
            actor=actor,
            metadata_json=metadata,
            previous_hash=previous_hash,
            current_hash=current_hash,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_for_execution(self, execution_id: uuid.UUID) -> list[AuditLog]:
        result = await self.session.execute(
            select(AuditLog).where(AuditLog.execution_id == execution_id).order_by(AuditLog.id.asc())
        )
        return list(result.scalars().all())
