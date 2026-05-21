from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user, require_project_member
from app.models import ChecklistItem, Issue, IssueAttachment, Sprint, User
from app.schemas import IssueOut

router = APIRouter(tags=["Backlog"])


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


def _issue_count_subqueries():
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

    return attachment_count_subq, checklist_count_subq


async def _issue_list_query(
    db: AsyncSession,
    *,
    project_id: int,
    sprint_id: int | None,
    limit: int,
    offset: int,
):
    attachment_count_subq, checklist_count_subq = _issue_count_subqueries()

    query = (
        select(
            Issue,
            func.coalesce(attachment_count_subq.c.attachment_count, 0).label("attachment_count"),
            func.coalesce(checklist_count_subq.c.checklist_total, 0).label("checklist_total"),
            func.coalesce(checklist_count_subq.c.checklist_done, 0).label("checklist_done"),
        )
        .options(selectinload(Issue.labels))
        .outerjoin(attachment_count_subq, attachment_count_subq.c.issue_id == Issue.id)
        .outerjoin(checklist_count_subq, checklist_count_subq.c.issue_id == Issue.id)
        .where(Issue.project_id == project_id)
        .order_by(Issue.position.asc(), Issue.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )

    if sprint_id is None:
        query = query.where(Issue.sprint_id.is_(None))
    else:
        query = query.where(Issue.sprint_id == sprint_id)

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


@router.get("/projects/{project_id}/backlog", response_model=list[IssueOut])
async def list_backlog_issues(
    project_id: int,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_member(db, project_id, current_user.id)

    return await _issue_list_query(
        db,
        project_id=project_id,
        sprint_id=None,
        limit=limit,
        offset=offset,
    )


@router.get("/projects/{project_id}/sprints/{sprint_id}/issues", response_model=list[IssueOut])
async def list_sprint_issues(
    project_id: int,
    sprint_id: int,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_member(db, project_id, current_user.id)

    sprint_result = await db.execute(
        select(Sprint).where(
            Sprint.id == sprint_id,
            Sprint.project_id == project_id,
        )
    )
    sprint = sprint_result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    return await _issue_list_query(
        db,
        project_id=project_id,
        sprint_id=sprint_id,
        limit=limit,
        offset=offset,
    )