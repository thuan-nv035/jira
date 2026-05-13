from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, require_project_member
from app.models import BoardColumn, Issue, Project, ProjectMember, User
from app.schemas import IssueCreate, IssueMove, IssueOut, IssueUpdate
from app.services.notifications import notify_project_members
from app.websocket_manager import manager

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


@router.get("", response_model=list[IssueOut])
async def list_issues(
    project_id: int,
    column_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_member(db, project_id, current_user.id)
    query = select(Issue).where(Issue.project_id == project_id)
    if column_id is not None:
        query = query.where(Issue.column_id == column_id)
    query = query.order_by(Issue.column_id.asc(), Issue.position.asc(), Issue.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=IssueOut, status_code=status.HTTP_201_CREATED)
async def create_issue(project_id: int, payload: IssueCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_member(db, project_id, current_user.id)
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
        reporter_id=current_user.id,
        assignee_id=payload.assignee_id,
        code=code,
        title=payload.title,
        description=payload.description,
        issue_type=payload.issue_type,
        priority=payload.priority,
        position=position,
    )
    db.add(issue)
    await db.commit()
    await db.refresh(issue)
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
    return issue


@router.get("/{issue_id}", response_model=IssueOut)
async def get_issue(project_id: int, issue_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_member(db, project_id, current_user.id)
    result = await db.execute(select(Issue).where(Issue.id == issue_id, Issue.project_id == project_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.patch("/{issue_id}", response_model=IssueOut)
async def update_issue(project_id: int, issue_id: int, payload: IssueUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_member(db, project_id, current_user.id)
    result = await db.execute(select(Issue).where(Issue.id == issue_id, Issue.project_id == project_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

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
    return issue


@router.patch("/{issue_id}/move", response_model=IssueOut)
async def move_issue(project_id: int, issue_id: int, payload: IssueMove, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_member(db, project_id, current_user.id)
    await _check_column(db, project_id, payload.column_id)

    result = await db.execute(select(Issue).where(Issue.id == issue_id, Issue.project_id == project_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

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
    return issue


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue(project_id: int, issue_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_member(db, project_id, current_user.id)
    result = await db.execute(select(Issue).where(Issue.id == issue_id, Issue.project_id == project_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    await db.delete(issue)
    await db.commit()
    await manager.broadcast(project_id, {"event": "issue.deleted", "data": {"issue_id": issue_id}})
