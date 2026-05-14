from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.services.activity_logs import create_activity_log
from app.database import get_db
from app.deps import get_current_user, require_project_editor, require_project_member
from app.models import BoardColumn, ChecklistItem, Issue, IssueAttachment, Project, ProjectMember, User, issue_labels_table
from app.schemas import IssueCreate, IssueMove, IssueOut, IssueUpdate
from app.services.notifications import notify_project_members
from app.websocket_manager import manager
from datetime import datetime, timezone
router = APIRouter(prefix="/projects/{project_id}/issues", tags=["Issues"])


async def _check_column(db: AsyncSession, project_id: int, column_id: int) -> BoardColumn:
    result = await db.execute(
        select(BoardColumn).where(BoardColumn.id == column_id, BoardColumn.project_id == project_id)
    )
    column = result.scalar_one_or_none()
    if not column:
        raise HTTPException(status_code=400, detail="Column does not belong to this project")
    return column


async def _check_assignee(db: AsyncSession, project_id: int, assignee_id: int | None) -> None:
    if assignee_id is None:
        return
    result = await db.execute(
        select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == assignee_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Assignee must be a project member")

async def _attach_attachment_count(db: AsyncSession, issue: Issue) -> Issue:
    count_result = await db.execute(
        select(func.count(IssueAttachment.id)).where(IssueAttachment.issue_id == issue.id)
    )
    issue.attachment_count = count_result.scalar_one()
    return issue


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

def _issue_activity_snapshot(issue: Issue) -> dict:
    return {
        "id": issue.id,
        "code": issue.code,
        "title": issue.title,
        "description": issue.description,
        "issue_type": issue.issue_type,
        "priority": issue.priority,
        "column_id": issue.column_id,
        "assignee_id": issue.assignee_id,
        "position": issue.position,
        "due_date": issue.due_date.isoformat() if issue.due_date else None,
    }


def _get_changed_values(before: dict, after: dict) -> tuple[dict, dict]:
    old_value = {}
    new_value = {}

    for key, before_value in before.items():
        after_value = after.get(key)

        if before_value != after_value:
            old_value[key] = before_value
            new_value[key] = after_value

    return old_value, new_value

async def _attach_issue_counts(db: AsyncSession, issue: Issue) -> Issue:
    attachment_result = await db.execute(
        select(func.count(IssueAttachment.id)).where(IssueAttachment.issue_id == issue.id)
    )

    checklist_result = await db.execute(
        select(
            func.count(ChecklistItem.id),
            func.count(ChecklistItem.id).filter(ChecklistItem.is_done.is_(True)),
        ).where(ChecklistItem.issue_id == issue.id)
    )

    attachment_count = attachment_result.scalar_one()
    checklist_total, checklist_done = checklist_result.one()

    issue.attachment_count = attachment_count
    issue.checklist_total = checklist_total
    issue.checklist_done = checklist_done

    return issue

async def _reload_issue_with_labels(db: AsyncSession, issue_id: int) -> Issue:
    result = await db.execute(
        select(Issue)
        .options(selectinload(Issue.labels))
        .where(Issue.id == issue_id)
    )

    issue = result.scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    return issue

@router.get("", response_model=list[IssueOut])
async def list_issues(
    project_id: int,
    column_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_member(db, project_id, current_user.id)

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
        .outerjoin(attachment_count_subq, attachment_count_subq.c.issue_id == Issue.id)
        .outerjoin(checklist_count_subq, checklist_count_subq.c.issue_id == Issue.id)
        .where(Issue.project_id == project_id)
    )

    if column_id is not None:
        query = query.where(Issue.column_id == column_id)

    query = query.order_by(
        Issue.column_id.asc(),
        Issue.position.asc(),
        Issue.created_at.desc(),
    )

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


@router.post("", response_model=IssueOut, status_code=status.HTTP_201_CREATED)
async def create_issue(project_id: int, payload: IssueCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_editor(db, project_id, current_user.id)
    await _check_column(db, project_id, payload.column_id)
    await _check_assignee(db, project_id, payload.assignee_id)

    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    count_result = await db.execute(select(func.count(Issue.id)).where(Issue.project_id == project_id))
    next_number = count_result.scalar_one() + 1
    code = f"{project.key}-{next_number}"

    position_result = await db.execute(
        select(func.coalesce(func.max(Issue.position), -1)).where(Issue.project_id == project_id, Issue.column_id == payload.column_id)
    )
    position = position_result.scalar_one() + 1

    issue = Issue(
        project_id=project_id,
        column_id=payload.column_id,
        title=payload.title,
        description=payload.description,
        issue_type=payload.issue_type,
        priority=payload.priority,
        assignee_id=payload.assignee_id,
        due_date=payload.due_date,
        reporter_id=current_user.id,
        code=code,
        position=position,
    )
    db.add(issue)
    await db.commit()
    await db.refresh(issue)
    await create_activity_log(
        db,
        project_id=issue.project_id,
        issue_id=issue.id,
        actor_id=current_user.id,
        action="ISSUE_CREATED",
        message=f"{current_user.full_name} created {issue.code}",
        new_value=_issue_activity_snapshot(issue),
    )

    await db.commit()

    await manager.broadcast(
        issue.project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": issue.id,
                "action": "ISSUE_CREATED",
                "message": f"{current_user.full_name} created {issue.code}",
            },
        },
    )
    await manager.broadcast(project_id, {"event": "issue.created", "data": {"issue_id": issue.id, "code": issue.code}})
    await notify_project_members(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        notification_type="ISSUE_CREATED",
        title=f"New issue {issue.code}",
        message=issue.title,
        issue_id=issue.id,
    )
    issue = await _reload_issue_with_labels(db, issue.id)
    issue.attachment_count = 0
    issue.checklist_total = 0
    issue.checklist_done = 0
    return issue

@router.get("/search", response_model=list[IssueOut])
async def search_issues(
    project_id: int,
    keyword: str | None = Query(default=None),
    column_id: int | None = Query(default=None),
    assignee_id: int | None = Query(default=None),
    reporter_id: int | None = Query(default=None),
    priority: str | None = Query(default=None),
    issue_type: str | None = Query(default=None),
    has_attachment: bool | None = Query(default=None),
    sort_by: str = Query(default="updated_at"),
    order: str = Query(default="desc"),
    overdue: bool | None = Query(default=None),
    due_before: datetime | None = Query(default=None),
    due_after: datetime | None = Query(default=None),
    label_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_member(db, project_id, current_user.id)

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
        .outerjoin(attachment_count_subq, attachment_count_subq.c.issue_id == Issue.id)
        .outerjoin(checklist_count_subq, checklist_count_subq.c.issue_id == Issue.id)
        .where(Issue.project_id == project_id)
    )

    if keyword:
        search_text = f"%{keyword.strip()}%"
        query = query.where(
            or_(
                Issue.title.ilike(search_text),
                Issue.description.ilike(search_text),
                Issue.code.ilike(search_text),
            )
        )

    if column_id is not None:
        query = query.where(Issue.column_id == column_id)

    if assignee_id is not None:
        query = query.where(Issue.assignee_id == assignee_id)

    if reporter_id is not None:
        query = query.where(Issue.reporter_id == reporter_id)

    if priority:
        query = query.where(Issue.priority == priority.upper())

    if issue_type:
        query = query.where(Issue.issue_type == issue_type.upper())

    if has_attachment is True:
        query = query.where(func.coalesce(attachment_count_subq.c.attachment_count, 0) > 0)

    if has_attachment is False:
        query = query.where(func.coalesce(attachment_count_subq.c.attachment_count, 0) == 0)

    if label_id is not None:
        query = query.join(
            issue_labels_table,
            issue_labels_table.c.issue_id == Issue.id,
        ).where(
            issue_labels_table.c.label_id == label_id
        )

    if overdue is True:
        query = query.where(Issue.due_date.is_not(None))
        query = query.where(Issue.due_date < datetime.now(timezone.utc))

    if overdue is False:
        query = query.where(
            or_(
                Issue.due_date.is_(None),
                Issue.due_date >= datetime.now(timezone.utc),
            )
        )

    if due_before is not None:
        query = query.where(Issue.due_date <= due_before)

    if due_after is not None:
        query = query.where(Issue.due_date >= due_after)

    sort_columns = {
        "created_at": Issue.created_at,
        "updated_at": Issue.updated_at,
        "priority": Issue.priority,
        "title": Issue.title,
        "position": Issue.position,
    }

    sort_column = sort_columns.get(sort_by, Issue.updated_at)

    if order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

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

@router.get("/{issue_id}", response_model=IssueOut)
async def get_issue(project_id: int, issue_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_member(db, project_id, current_user.id)
    result = await db.execute(select(Issue).options(selectinload(Issue.labels)).where(Issue.id == issue_id, Issue.project_id == project_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return await _attach_issue_counts(db, issue)


@router.patch("/{issue_id}", response_model=IssueOut)
async def update_issue(project_id: int, issue_id: int, payload: IssueUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_editor(db, project_id, current_user.id)
    result = await db.execute(select(Issue).where(Issue.id == issue_id, Issue.project_id == project_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    before = _issue_activity_snapshot(issue)
    data = payload.model_dump(exclude_unset=True)
    if "assignee_id" in data:
        await _check_assignee(db, project_id, data["assignee_id"])
    for key, value in data.items():
        setattr(issue, key, value)

    await db.commit()
    await db.refresh(issue)
    await manager.broadcast(project_id, {"event": "issue.updated", "data": {"issue_id": issue.id}})
    await notify_project_members(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        notification_type="ISSUE_UPDATED",
        title=f"Issue {issue.code} was updated",
        message=issue.title,
        issue_id=issue.id,
    )

    after = _issue_activity_snapshot(issue)
    old_value, new_value = _get_changed_values(before, after)

    if new_value:
        await create_activity_log(
            db,
            project_id=issue.project_id,
            issue_id=issue.id,
            actor_id=current_user.id,
            action="ISSUE_UPDATED",
            message=f"{current_user.full_name} updated {issue.code}",
            old_value=old_value,
            new_value=new_value,
        )

        await db.commit()

        await manager.broadcast(
            issue.project_id,
            {
                "event": "activity.created",
                "data": {
                    "issue_id": issue.id,
                    "action": "ISSUE_UPDATED",
                    "message": f"{current_user.full_name} updated {issue.code}",
                },
            },
        )
    issue = await _reload_issue_with_labels(db, issue.id)
    return await _attach_issue_counts(db, issue)


@router.patch("/{issue_id}/move", response_model=IssueOut)
async def move_issue(project_id: int, issue_id: int, payload: IssueMove, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_editor(db, project_id, current_user.id)
    await _check_column(db, project_id, payload.column_id)

    result = await db.execute(select(Issue).where(Issue.id == issue_id, Issue.project_id == project_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    before_move = {
        "column_id": issue.column_id,
        "position": issue.position,
    }
    issue.column_id = payload.column_id
    issue.position = payload.position
    await db.commit()
    await db.refresh(issue)
    await manager.broadcast(
        project_id,
        {"event": "issue.moved", "data": {"issue_id": issue.id, "column_id": issue.column_id, "position": issue.position}},
    )
    await notify_project_members(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        notification_type="ISSUE_MOVED",
        title=f"Issue {issue.code} was moved",
        message=f"Moved to column #{issue.column_id}",
        issue_id=issue.id,
    )
    after_move = {
        "column_id": issue.column_id,
        "position": issue.position,
    }

    await create_activity_log(
        db,
        project_id=issue.project_id,
        issue_id=issue.id,
        actor_id=current_user.id,
        action="ISSUE_MOVED",
        message=f"{current_user.full_name} moved {issue.code}",
        old_value=before_move,
        new_value=after_move,
    )

    await db.commit()

    await manager.broadcast(
        issue.project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": issue.id,
                "action": "ISSUE_MOVED",
                "message": f"{current_user.full_name} moved {issue.code}",
            },
        },
    )
    issue = await _reload_issue_with_labels(db, issue.id)
    return await _attach_issue_counts(db, issue)


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue(project_id: int, issue_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_editor(db, project_id, current_user.id)
    result = await db.execute(select(Issue).where(Issue.id == issue_id, Issue.project_id == project_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    await db.delete(issue)
    await db.commit()
    await manager.broadcast(project_id, {"event": "issue.deleted", "data": {"issue_id": issue_id}})
