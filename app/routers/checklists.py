from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, require_project_editor, require_project_member
from app.models import ChecklistItem, Issue, User
from app.schemas import ChecklistCreate, ChecklistOut, ChecklistUpdate
from app.services.activity_logs import create_activity_log
from app.websocket_manager import manager

router = APIRouter(tags=["Checklists"])


async def _get_issue_and_check_member(
    db: AsyncSession,
    issue_id: int,
    user_id: int,
) -> Issue:
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    await require_project_member(db, issue.project_id, user_id)

    return issue


async def _get_checklist_and_check_member(
    db: AsyncSession,
    checklist_id: int,
    user_id: int,
) -> tuple[ChecklistItem, Issue]:
    result = await db.execute(
        select(ChecklistItem, Issue)
        .join(Issue, Issue.id == ChecklistItem.issue_id)
        .where(ChecklistItem.id == checklist_id)
    )

    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    checklist, issue = row

    await require_project_member(db, issue.project_id, user_id)

    return checklist, issue


@router.get("/issues/{issue_id}/checklists", response_model=list[ChecklistOut])
async def list_checklists(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_issue_and_check_member(db, issue_id, current_user.id)

    result = await db.execute(
        select(ChecklistItem)
        .where(ChecklistItem.issue_id == issue_id)
        .order_by(ChecklistItem.position.asc(), ChecklistItem.created_at.asc())
    )

    return result.scalars().all()


@router.post(
    "/issues/{issue_id}/checklists",
    response_model=ChecklistOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_checklist(
    issue_id: int,
    payload: ChecklistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    issue = await _get_issue_and_check_member(db, issue_id, current_user.id)
    await require_project_editor(db, issue.project_id, current_user.id)
    title = payload.title.strip()

    if not title:
        raise HTTPException(status_code=400, detail="Checklist title is required")

    if payload.position is None:
        count_result = await db.execute(
            select(func.count(ChecklistItem.id)).where(ChecklistItem.issue_id == issue_id)
        )
        position = count_result.scalar_one()
    else:
        position = payload.position

    checklist = ChecklistItem(
        issue_id=issue_id,
        creator_id=current_user.id,
        title=title,
        position=position,
        is_done=False,
    )

    db.add(checklist)
    await db.flush()

    await create_activity_log(
        db,
        project_id=issue.project_id,
        issue_id=issue.id,
        actor_id=current_user.id,
        action="CHECKLIST_CREATED",
        message=f"{current_user.full_name} added checklist item to {issue.code}",
        new_value={
            "checklist_id": checklist.id,
            "title": checklist.title,
            "is_done": checklist.is_done,
            "position": checklist.position,
        },
    )

    await db.commit()
    await db.refresh(checklist)

    await manager.broadcast(
        issue.project_id,
        {
            "event": "checklist.created",
            "data": {
                "issue_id": issue.id,
                "checklist_id": checklist.id,
                "title": checklist.title,
            },
        },
    )

    await manager.broadcast(
        issue.project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": issue.id,
                "action": "CHECKLIST_CREATED",
                "message": f"{current_user.full_name} added checklist item to {issue.code}",
            },
        },
    )

    return checklist


@router.patch("/checklists/{checklist_id}", response_model=ChecklistOut)
async def update_checklist(
    checklist_id: int,
    payload: ChecklistUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    checklist, issue = await _get_checklist_and_check_member(
        db,
        checklist_id,
        current_user.id,
    )

    await require_project_editor(db, issue.project_id, current_user.id)

    before = {
        "title": checklist.title,
        "is_done": checklist.is_done,
        "position": checklist.position,
    }

    update_data = payload.model_dump(exclude_unset=True)

    if "title" in update_data:
        title = update_data["title"].strip() if update_data["title"] else ""

        if not title:
            raise HTTPException(status_code=400, detail="Checklist title is required")

        checklist.title = title

    if "is_done" in update_data:
        checklist.is_done = update_data["is_done"]

    if "position" in update_data:
        checklist.position = update_data["position"]

    after = {
        "title": checklist.title,
        "is_done": checklist.is_done,
        "position": checklist.position,
    }

    old_value = {}
    new_value = {}

    for key, before_value in before.items():
        after_value = after.get(key)

        if before_value != after_value:
            old_value[key] = before_value
            new_value[key] = after_value

    if old_value:
        await create_activity_log(
            db,
            project_id=issue.project_id,
            issue_id=issue.id,
            actor_id=current_user.id,
            action="CHECKLIST_UPDATED",
            message=f"{current_user.full_name} updated checklist item in {issue.code}",
            old_value=old_value,
            new_value={
                "checklist_id": checklist.id,
                **new_value,
            },
        )

    await db.commit()
    await db.refresh(checklist)

    await manager.broadcast(
        issue.project_id,
        {
            "event": "checklist.updated",
            "data": {
                "issue_id": issue.id,
                "checklist_id": checklist.id,
                "title": checklist.title,
                "is_done": checklist.is_done,
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
                    "action": "CHECKLIST_UPDATED",
                    "message": f"{current_user.full_name} updated checklist item in {issue.code}",
                },
            },
        )

    return checklist


@router.delete("/checklists/{checklist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checklist(
    checklist_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    checklist, issue = await _get_checklist_and_check_member(
        db,
        checklist_id,
        current_user.id,
    )

    await require_project_editor(db, issue.project_id, current_user.id)

    deleted_value = {
        "checklist_id": checklist.id,
        "title": checklist.title,
        "is_done": checklist.is_done,
        "position": checklist.position,
    }

    await db.delete(checklist)

    await create_activity_log(
        db,
        project_id=issue.project_id,
        issue_id=issue.id,
        actor_id=current_user.id,
        action="CHECKLIST_DELETED",
        message=f"{current_user.full_name} deleted checklist item from {issue.code}",
        old_value=deleted_value,
    )

    await db.commit()

    await manager.broadcast(
        issue.project_id,
        {
            "event": "checklist.deleted",
            "data": {
                "issue_id": issue.id,
                "checklist_id": checklist_id,
            },
        },
    )

    await manager.broadcast(
        issue.project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": issue.id,
                "action": "CHECKLIST_DELETED",
                "message": f"{current_user.full_name} deleted checklist item from {issue.code}",
            },
        },
    )