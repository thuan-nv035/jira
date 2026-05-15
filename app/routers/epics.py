from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, require_project_editor, require_project_member
from app.models import Epic, Issue, User
from app.schemas import EpicCreate, EpicOut, EpicUpdate, IssueEpicUpdate
from app.services.activity_logs import create_activity_log
from app.websocket_manager import manager

router = APIRouter(tags=["Epics"])


@router.get("/projects/{project_id}/epics", response_model=list[EpicOut])
async def list_epics(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_member(db, project_id, current_user.id)

    result = await db.execute(
        select(Epic)
        .where(Epic.project_id == project_id)
        .order_by(Epic.created_at.desc())
    )

    return result.scalars().all()


@router.post(
    "/projects/{project_id}/epics",
    response_model=EpicOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_epic(
    project_id: int,
    payload: EpicCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_editor(db, project_id, current_user.id)

    name = payload.name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Epic name is required")

    epic = Epic(
        project_id=project_id,
        name=name,
        description=payload.description,
        color=payload.color or "#7c3aed",
    )

    db.add(epic)
    await db.flush()

    await create_activity_log(
        db,
        project_id=project_id,
        issue_id=None,
        actor_id=current_user.id,
        action="EPIC_CREATED",
        message=f"{current_user.full_name} created epic {epic.name}",
        new_value={
            "epic_id": epic.id,
            "name": epic.name,
            "color": epic.color,
        },
    )

    await db.commit()
    await db.refresh(epic)

    await manager.broadcast(
        project_id,
        {
            "event": "epic.created",
            "data": {
                "epic_id": epic.id,
                "name": epic.name,
                "color": epic.color,
            },
        },
    )

    await manager.broadcast(
        project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": None,
                "action": "EPIC_CREATED",
                "message": f"{current_user.full_name} created epic {epic.name}",
            },
        },
    )

    return epic


@router.patch("/epics/{epic_id}", response_model=EpicOut)
async def update_epic(
    epic_id: int,
    payload: EpicUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Epic).where(Epic.id == epic_id))
    epic = result.scalar_one_or_none()

    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    await require_project_editor(db, epic.project_id, current_user.id)

    before = {
        "name": epic.name,
        "description": epic.description,
        "color": epic.color,
    }

    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data:
        name = update_data["name"].strip() if update_data["name"] else ""

        if not name:
            raise HTTPException(status_code=400, detail="Epic name is required")

        epic.name = name

    if "description" in update_data:
        epic.description = update_data["description"]

    if "color" in update_data:
        epic.color = update_data["color"] or "#7c3aed"

    after = {
        "name": epic.name,
        "description": epic.description,
        "color": epic.color,
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
            project_id=epic.project_id,
            issue_id=None,
            actor_id=current_user.id,
            action="EPIC_UPDATED",
            message=f"{current_user.full_name} updated epic {epic.name}",
            old_value=old_value,
            new_value={
                "epic_id": epic.id,
                **new_value,
            },
        )

    await db.commit()
    await db.refresh(epic)

    await manager.broadcast(
        epic.project_id,
        {
            "event": "epic.updated",
            "data": {
                "epic_id": epic.id,
                "name": epic.name,
                "color": epic.color,
            },
        },
    )

    if old_value:
        await manager.broadcast(
            epic.project_id,
            {
                "event": "activity.created",
                "data": {
                    "issue_id": None,
                    "action": "EPIC_UPDATED",
                    "message": f"{current_user.full_name} updated epic {epic.name}",
                },
            },
        )

    return epic


@router.delete("/epics/{epic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_epic(
    epic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Epic).where(Epic.id == epic_id))
    epic = result.scalar_one_or_none()

    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")

    await require_project_editor(db, epic.project_id, current_user.id)

    project_id = epic.project_id
    epic_name = epic.name

    await create_activity_log(
        db,
        project_id=project_id,
        issue_id=None,
        actor_id=current_user.id,
        action="EPIC_DELETED",
        message=f"{current_user.full_name} deleted epic {epic_name}",
        old_value={
            "epic_id": epic.id,
            "name": epic.name,
        },
    )

    await db.delete(epic)
    await db.commit()

    await manager.broadcast(
        project_id,
        {
            "event": "epic.deleted",
            "data": {
                "epic_id": epic_id,
            },
        },
    )

    await manager.broadcast(
        project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": None,
                "action": "EPIC_DELETED",
                "message": f"{current_user.full_name} deleted epic {epic_name}",
            },
        },
    )


@router.patch("/issues/{issue_id}/epic")
async def update_issue_epic(
    issue_id: int,
    payload: IssueEpicUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    issue_result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = issue_result.scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    await require_project_editor(db, issue.project_id, current_user.id)

    old_epic_id = issue.epic_id

    if payload.epic_id is not None:
        epic_result = await db.execute(select(Epic).where(Epic.id == payload.epic_id))
        epic = epic_result.scalar_one_or_none()

        if not epic:
            raise HTTPException(status_code=404, detail="Epic not found")

        if epic.project_id != issue.project_id:
            raise HTTPException(status_code=400, detail="Epic does not belong to this project")

    issue.epic_id = payload.epic_id

    await create_activity_log(
        db,
        project_id=issue.project_id,
        issue_id=issue.id,
        actor_id=current_user.id,
        action="ISSUE_EPIC_UPDATED",
        message=f"{current_user.full_name} updated epic for {issue.code}",
        old_value={"epic_id": old_epic_id},
        new_value={"epic_id": issue.epic_id},
    )

    await db.commit()
    await db.refresh(issue)

    await manager.broadcast(
        issue.project_id,
        {
            "event": "issue.epic_updated",
            "data": {
                "issue_id": issue.id,
                "epic_id": issue.epic_id,
            },
        },
    )

    await manager.broadcast(
        issue.project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": issue.id,
                "action": "ISSUE_EPIC_UPDATED",
                "message": f"{current_user.full_name} updated epic for {issue.code}",
            },
        },
    )

    return {
        "issue_id": issue.id,
        "epic_id": issue.epic_id,
    }