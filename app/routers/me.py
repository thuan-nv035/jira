from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models import ChecklistItem, Issue, IssueAttachment, Project, ProjectMember, User
from app.schemas import IssueOut

router = APIRouter(prefix="/me", tags=["Me"])


def _set_issue_counts(
    issue: Issue,
    attachment_count: int = 0,
    checklist_total: int = 0,
    checklist_done: int = 0,
) -> Issue:
    issue.attachment_count = attachment_count
    issue.checklist_total = checklist_total
    issue.checklist_done = checklist_done
    return issue


@router.get("/issues", response_model=list[IssueOut])
async def my_issues(
    project_id: int | None = Query(default=None),
    priority: str | None = Query(default=None),
    issue_type: str | None = Query(default=None),
    overdue: bool | None = Query(default=None),
    due_soon: bool | None = Query(default=None),
    sort_by: str = Query(default="updated_at"),
    order: str = Query(default="desc"),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    soon = now + timedelta(days=3)

    attachment_count_subq = (
        select(
            IssueAttachment.issue_id.label("issue_id"),
            func.count(IssueAttachment.id).label("attachment_count"),
        )
        .group_by(IssueAttachment.issue_id)
        .subquery()
    )

    checklist_count_subq = (
        select(
            ChecklistItem.issue_id.label("issue_id"),
            func.count(ChecklistItem.id).label("checklist_total"),
            func.count(ChecklistItem.id)
            .filter(ChecklistItem.is_done.is_(True))
            .label("checklist_done"),
        )
        .group_by(ChecklistItem.issue_id)
        .subquery()
    )

    query = (
        select(
            Issue,
            func.coalesce(attachment_count_subq.c.attachment_count, 0).label("attachment_count"),
            func.coalesce(checklist_count_subq.c.checklist_total, 0).label("checklist_total"),
            func.coalesce(checklist_count_subq.c.checklist_done, 0).label("checklist_done"),
        )
        .options(selectinload(Issue.labels))
        .join(ProjectMember, ProjectMember.project_id == Issue.project_id)
        .where(
            ProjectMember.user_id == current_user.id,
            Issue.assignee_id == current_user.id,
        )
        .outerjoin(attachment_count_subq, attachment_count_subq.c.issue_id == Issue.id)
        .outerjoin(checklist_count_subq, checklist_count_subq.c.issue_id == Issue.id)
    )

    if project_id is not None:
        query = query.where(Issue.project_id == project_id)

    if priority:
        query = query.where(Issue.priority == priority.upper())

    if issue_type:
        query = query.where(Issue.issue_type == issue_type.upper())

    if overdue is True:
        query = query.where(
            Issue.due_date.is_not(None),
            Issue.due_date < now,
        )

    if overdue is False:
        query = query.where(
            or_(
                Issue.due_date.is_(None),
                Issue.due_date >= now,
            )
        )

    if due_soon is True:
        query = query.where(
            Issue.due_date.is_not(None),
            Issue.due_date >= now,
            Issue.due_date <= soon,
        )

    sort_columns = {
        "created_at": Issue.created_at,
        "updated_at": Issue.updated_at,
        "due_date": Issue.due_date,
        "priority": Issue.priority,
        "title": Issue.title,
    }

    sort_column = sort_columns.get(sort_by, Issue.updated_at)

    if order.lower() == "asc":
        query = query.order_by(sort_column.asc().nullslast())
    else:
        query = query.order_by(sort_column.desc().nullslast())

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)

    issues = []

    for issue, attachment_count, checklist_total, checklist_done in result.all():
        issues.append(
            _set_issue_counts(
                issue,
                attachment_count=attachment_count,
                checklist_total=checklist_total,
                checklist_done=checklist_done,
            )
        )

    return issues