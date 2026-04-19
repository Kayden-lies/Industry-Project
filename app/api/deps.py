from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, get_redis
from app.services.execution_service import ExecutionService


async def get_execution_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    redis_client: Annotated[Redis, Depends(get_redis)],
) -> ExecutionService:
    return ExecutionService(session=db, redis_client=redis_client)
