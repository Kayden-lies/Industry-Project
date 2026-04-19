import hashlib
import json
import uuid
from datetime import UTC, datetime

from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, audit_repo: AuditRepository):
        self.audit_repo = audit_repo

    @staticmethod
    def _build_hash(
        execution_id: uuid.UUID,
        action: str,
        actor: str,
        timestamp: datetime,
        metadata: dict | None,
        previous_hash: str | None,
    ) -> str:
        payload = {
            "execution_id": str(execution_id),
            "action": action,
            "actor": actor,
            "timestamp": timestamp.isoformat(),
            "metadata": metadata or {},
            "previous_hash": previous_hash,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    async def append_audit_log(
        self,
        execution_id: uuid.UUID,
        action: str,
        actor: str,
        metadata: dict | None,
    ) -> None:
        last_log = await self.audit_repo.get_last_log(execution_id)
        previous_hash = last_log.current_hash if last_log else None
        timestamp = datetime.now(UTC)
        current_hash = self._build_hash(execution_id, action, actor, timestamp, metadata, previous_hash)

        await self.audit_repo.append_log(
            execution_id=execution_id,
            action=action,
            actor=actor,
            metadata=metadata,
            previous_hash=previous_hash,
            current_hash=current_hash,
        )
