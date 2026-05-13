from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityLog


async def create_activity_log(
    db: AsyncSession,
    *,
    project_id: int,
    issue_id: Optional[int],
    actor_id: Optional[int],
    action: str,
    message: str,
    old_value: Optional[dict[str, Any]] = None,
    new_value: Optional[dict[str, Any]] = None,
) -> ActivityLog:
    log = ActivityLog(
        project_id=project_id,
        issue_id=issue_id,
        actor_id=actor_id,
        action=action,
        message=message,
        old_value=old_value,
        new_value=new_value,
    )

    db.add(log)
    await db.flush()

    return log