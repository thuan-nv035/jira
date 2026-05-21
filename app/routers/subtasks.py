from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user, require_project_editor, require_project_member
from app.models import Issue, ProjectMember, Subtask, User
from app.schemas import SubtaskCreate, SubtaskOut, SubtaskUpdate
from app.services.activity_logs import create_activity_log
from app.websocket_manager import manager

router = APIRouter(tags=["Subtasks"])


async def get_issue_or_404(db: AsyncSession, issue_id: int) -> Issue:
    result = await db.execute(
        select(Issue).where(Issue.id == issue_id)
    )

    issue = result.scalar_one_or_none()

    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found",
        )

    return issue


async def get_subtask_or_404(db: AsyncSession, subtask_id: int) -> Subtask:
    result = await db.execute(
        select(Subtask)
        .options(selectinload(Subtask.assignee))
        .where(Subtask.id == subtask_id)
    )

    subtask = result.scalar_one_or_none()

    if not subtask:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subtask not found",
        )

    return subtask


async def validate_assignee(
    db: AsyncSession,
    *,
    project_id: int,
    assignee_id: int | None,
):
    if assignee_id is None:
        return

    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == assignee_id,
        )
    )

    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignee is not a member of this project",
        )


@router.get("/issues/{issue_id}/subtasks", response_model=list[SubtaskOut])
async def list_subtasks(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    issue = await get_issue_or_404(db, issue_id)

    await require_project_member(
        db,
        issue.project_id,
        current_user.id,
    )

    result = await db.execute(
        select(Subtask)
        .options(selectinload(Subtask.assignee))
        .where(Subtask.issue_id == issue.id)
        .order_by(Subtask.created_at.asc())
    )

    return result.scalars().all()


@router.post(
    "/issues/{issue_id}/subtasks",
    response_model=SubtaskOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_subtask(
    issue_id: int,
    payload: SubtaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    issue = await get_issue_or_404(db, issue_id)

    await require_project_editor(
        db,
        issue.project_id,
        current_user.id,
    )

    title = payload.title.strip()

    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subtask title is required",
        )

    await validate_assignee(
        db,
        project_id=issue.project_id,
        assignee_id=payload.assignee_id,
    )

    subtask = Subtask(
        issue_id=issue.id,
        title=title,
        assignee_id=payload.assignee_id,
        is_done=False,
    )

    db.add(subtask)
    await db.flush()

    await create_activity_log(
        db,
        project_id=issue.project_id,
        issue_id=issue.id,
        actor_id=current_user.id,
        action="SUBTASK_CREATED",
        message=f"{current_user.full_name} created subtask in {issue.code}",
        new_value={
            "subtask_id": subtask.id,
            "title": subtask.title,
            "assignee_id": subtask.assignee_id,
        },
    )

    await db.commit()

    result = await db.execute(
        select(Subtask)
        .options(selectinload(Subtask.assignee))
        .where(Subtask.id == subtask.id)
    )
    saved_subtask = result.scalar_one()

    await manager.broadcast(
        issue.project_id,
        {
            "event": "subtask.created",
            "data": {
                "issue_id": issue.id,
                "subtask_id": saved_subtask.id,
            },
        },
    )

    await manager.broadcast(
        issue.project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": issue.id,
                "action": "SUBTASK_CREATED",
                "message": f"{current_user.full_name} created subtask in {issue.code}",
            },
        },
    )

    return saved_subtask


@router.patch("/subtasks/{subtask_id}", response_model=SubtaskOut)
async def update_subtask(
    subtask_id: int,
    payload: SubtaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    subtask = await get_subtask_or_404(db, subtask_id)
    issue = await get_issue_or_404(db, subtask.issue_id)

    await require_project_editor(
        db,
        issue.project_id,
        current_user.id,
    )

    update_data = payload.model_dump(exclude_unset=True)

    old_value = {}
    new_value = {}

    if "title" in update_data:
        title = update_data["title"].strip() if update_data["title"] else ""

        if not title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subtask title is required",
            )

        if subtask.title != title:
            old_value["title"] = subtask.title
            new_value["title"] = title
            subtask.title = title

    if "is_done" in update_data:
        next_done = bool(update_data["is_done"])

        if subtask.is_done != next_done:
            old_value["is_done"] = subtask.is_done
            new_value["is_done"] = next_done
            subtask.is_done = next_done

    if "assignee_id" in update_data:
        assignee_id = update_data["assignee_id"]

        await validate_assignee(
            db,
            project_id=issue.project_id,
            assignee_id=assignee_id,
        )

        if subtask.assignee_id != assignee_id:
            old_value["assignee_id"] = subtask.assignee_id
            new_value["assignee_id"] = assignee_id
            subtask.assignee_id = assignee_id

    if old_value:
        await create_activity_log(
            db,
            project_id=issue.project_id,
            issue_id=issue.id,
            actor_id=current_user.id,
            action="SUBTASK_UPDATED",
            message=f"{current_user.full_name} updated subtask in {issue.code}",
            old_value=old_value,
            new_value={
                "subtask_id": subtask.id,
                **new_value,
            },
        )

    await db.commit()

    result = await db.execute(
        select(Subtask)
        .options(selectinload(Subtask.assignee))
        .where(Subtask.id == subtask.id)
    )
    saved_subtask = result.scalar_one()

    await manager.broadcast(
        issue.project_id,
        {
            "event": "subtask.updated",
            "data": {
                "issue_id": issue.id,
                "subtask_id": saved_subtask.id,
            },
        },
    )

    if old_value:
        await manager.broadcast(
            issue.project_id,
            {
                "event": "activity.created",
                "data": {
                    "issue_id": issue.id,
                    "action": "SUBTASK_UPDATED",
                    "message": f"{current_user.full_name} updated subtask in {issue.code}",
                },
            },
        )

    return saved_subtask


@router.delete("/subtasks/{subtask_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subtask(
    subtask_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    subtask = await get_subtask_or_404(db, subtask_id)
    issue = await get_issue_or_404(db, subtask.issue_id)

    await require_project_editor(
        db,
        issue.project_id,
        current_user.id,
    )

    old_title = subtask.title

    await create_activity_log(
        db,
        project_id=issue.project_id,
        issue_id=issue.id,
        actor_id=current_user.id,
        action="SUBTASK_DELETED",
        message=f"{current_user.full_name} deleted subtask in {issue.code}",
        old_value={
            "subtask_id": subtask.id,
            "title": old_title,
        },
    )

    await db.delete(subtask)
    await db.commit()

    await manager.broadcast(
        issue.project_id,
        {
            "event": "subtask.deleted",
            "data": {
                "issue_id": issue.id,
                "subtask_id": subtask_id,
            },
        },
    )

    await manager.broadcast(
        issue.project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": issue.id,
                "action": "SUBTASK_DELETED",
                "message": f"{current_user.full_name} deleted subtask in {issue.code}",
            },
        },
    )