import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.execution import ExecutionStatus


class ExecutionCreate(BaseModel):
    job_name: str = Field(min_length=1, max_length=255)
    inputs: dict | None = None


class ExecutionUpdate(BaseModel):
    status: ExecutionStatus
    outputs: dict | None = None
    error_details: str | None = None


class ExecutionResponse(BaseModel):
    id: uuid.UUID
    job_name: str
    user: str
    status: ExecutionStatus
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: float | None
    inputs: dict | None
    outputs: dict | None
    error_details: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExecutionListResponse(BaseModel):
    items: list[ExecutionResponse]
    total: int
    page: int
    page_size: int


class ExecutionSummaryResponse(BaseModel):
    success_rate: float
    failure_count: int
    avg_duration_seconds: float
