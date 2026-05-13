from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user, require_project_member
from app.models import ActivityLog, Issue, User
from app.schemas import ActivityLogOut

router = APIRouter(tags=["Activity Logs"])


@router.get("/projects/{project_id}/activity-logs", response_model=list[ActivityLogOut])
async def list_project_activity_logs(
    project_id: int,
    issue_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_member(db, project_id, current_user.id)

    query = (
        select(ActivityLog)
        .options(selectinload(ActivityLog.actor))
        .where(ActivityLog.project_id == project_id)
        .order_by(ActivityLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    if issue_id is not None:
        query = query.where(ActivityLog.issue_id == issue_id)

    if action is not None:
        query = query.where(ActivityLog.action == action)

    result = await db.execute(query)

    return result.scalars().all()


@router.get("/issues/{issue_id}/activity-logs", response_model=list[ActivityLogOut])
async def list_issue_activity_logs(
    issue_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    issue_result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = issue_result.scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    await require_project_member(db, issue.project_id, current_user.id)

    result = await db.execute(
        select(ActivityLog)
        .options(selectinload(ActivityLog.actor))
        .where(ActivityLog.issue_id == issue_id)
        .order_by(ActivityLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    return result.scalars().all()