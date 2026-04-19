from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    action: str
    actor: str
    timestamp: datetime
    metadata: dict | None
    previous_hash: str | None
    current_hash: str


class AuditLogListResponse(BaseModel):
    execution_id: str
    logs: list[AuditLogResponse]
