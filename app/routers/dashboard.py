from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user, require_project_member
from app.models import ActivityLog, BoardColumn, Issue, ProjectMember, User
from app.schemas import (
    ActivityLogOut,
    DashboardAssigneeItemOut,
    DashboardPriorityItemOut,
    DashboardStatusItemOut,
    DashboardSummaryOut,
)

router = APIRouter(prefix="/projects/{project_id}/dashboard", tags=["Dashboard"])


def _done_column_condition():
    return or_(
        func.lower(BoardColumn.name) == "done",
        func.lower(BoardColumn.name) == "completed",
        func.lower(BoardColumn.name) == "complete",
    )


@router.get("/summary", response_model=DashboardSummaryOut)
async def dashboard_summary(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_member(db, project_id, current_user.id)

    now = datetime.now(timezone.utc)

    total_result = await db.execute(
        select(func.count(Issue.id)).where(Issue.project_id == project_id)
    )
    total_issues = total_result.scalar_one()

    done_result = await db.execute(
        select(func.count(Issue.id))
        .join(BoardColumn, BoardColumn.id == Issue.column_id)
        .where(
            Issue.project_id == project_id,
            _done_column_condition(),
        )
    )
    done_issues = done_result.scalar_one()

    overdue_result = await db.execute(
        select(func.count(Issue.id)).where(
            Issue.project_id == project_id,
            Issue.due_date.is_not(None),
            Issue.due_date < now,
        )
    )
    overdue_issues = overdue_result.scalar_one()

    unassigned_result = await db.execute(
        select(func.count(Issue.id)).where(
            Issue.project_id == project_id,
            Issue.assignee_id.is_(None),
        )
    )
    unassigned_issues = unassigned_result.scalar_one()

    members_result = await db.execute(
        select(func.count(ProjectMember.id)).where(
            ProjectMember.project_id == project_id
        )
    )
    total_members = members_result.scalar_one()

    in_progress_issues = max(total_issues - done_issues, 0)

    return DashboardSummaryOut(
        total_issues=total_issues,
        done_issues=done_issues,
        in_progress_issues=in_progress_issues,
        overdue_issues=overdue_issues,
        unassigned_issues=unassigned_issues,
        total_members=total_members,
    )


@router.get("/issues-by-status", response_model=list[DashboardStatusItemOut])
async def issues_by_status(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_member(db, project_id, current_user.id)

    result = await db.execute(
        select(
            BoardColumn.id.label("column_id"),
            BoardColumn.name.label("column_name"),
            func.count(Issue.id).label("total"),
        )
        .outerjoin(Issue, and_(Issue.column_id == BoardColumn.id, Issue.project_id == project_id))
        .where(BoardColumn.project_id == project_id)
        .group_by(BoardColumn.id, BoardColumn.name, BoardColumn.position)
        .order_by(BoardColumn.position.asc())
    )

    return [
        DashboardStatusItemOut(
            column_id=row.column_id,
            column_name=row.column_name,
            total=row.total,
        )
        for row in result.all()
    ]


@router.get("/issues-by-priority", response_model=list[DashboardPriorityItemOut])
async def issues_by_priority(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_member(db, project_id, current_user.id)

    result = await db.execute(
        select(
            Issue.priority.label("priority"),
            func.count(Issue.id).label("total"),
        )
        .where(Issue.project_id == project_id)
        .group_by(Issue.priority)
        .order_by(func.count(Issue.id).desc())
    )

    return [
        DashboardPriorityItemOut(
            priority=row.priority,
            total=row.total,
        )
        for row in result.all()
    ]


@router.get("/issues-by-assignee", response_model=list[DashboardAssigneeItemOut])
async def issues_by_assignee(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_member(db, project_id, current_user.id)

    result = await db.execute(
        select(
            Issue.assignee_id.label("assignee_id"),
            User.full_name.label("full_name"),
            User.email.label("email"),
            func.count(Issue.id).label("total"),
        )
        .outerjoin(User, User.id == Issue.assignee_id)
        .where(Issue.project_id == project_id)
        .group_by(Issue.assignee_id, User.full_name, User.email)
        .order_by(func.count(Issue.id).desc())
    )

    return [
        DashboardAssigneeItemOut(
            assignee_id=row.assignee_id,
            full_name=row.full_name,
            email=row.email,
            total=row.total,
        )
        for row in result.all()
    ]


@router.get("/recent-activity", response_model=list[ActivityLogOut])
async def dashboard_recent_activity(
    project_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_member(db, project_id, current_user.id)

    result = await db.execute(
        select(ActivityLog)
        .options(selectinload(ActivityLog.actor))
        .where(ActivityLog.project_id == project_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
    )

    return result.scalars().all()