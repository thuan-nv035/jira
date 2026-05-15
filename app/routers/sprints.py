from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, require_project_editor, require_project_member
from app.models import Issue, Sprint, User
from app.schemas import IssueSprintUpdate, SprintCreate, SprintOut, SprintUpdate
from app.services.activity_logs import create_activity_log
from app.websocket_manager import manager

router = APIRouter(tags=["Sprints"])


VALID_SPRINT_STATUSES = {"PLANNED", "ACTIVE", "COMPLETED"}


@router.get("/projects/{project_id}/sprints", response_model=list[SprintOut])
async def list_sprints(
    project_id: int,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_member(db, project_id, current_user.id)

    query = (
        select(Sprint)
        .where(Sprint.project_id == project_id)
        .order_by(Sprint.created_at.desc())
    )

    if status_filter:
        query = query.where(Sprint.status == status_filter.upper())

    result = await db.execute(query)

    return result.scalars().all()


@router.post(
    "/projects/{project_id}/sprints",
    response_model=SprintOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_sprint(
    project_id: int,
    payload: SprintCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_editor(db, project_id, current_user.id)

    name = payload.name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Sprint name is required")

    status_value = payload.status.upper()

    if status_value not in VALID_SPRINT_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid sprint status")

    sprint = Sprint(
        project_id=project_id,
        name=name,
        goal=payload.goal,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=status_value,
    )

    db.add(sprint)
    await db.flush()

    await create_activity_log(
        db,
        project_id=project_id,
        issue_id=None,
        actor_id=current_user.id,
        action="SPRINT_CREATED",
        message=f"{current_user.full_name} created sprint {sprint.name}",
        new_value={
            "sprint_id": sprint.id,
            "name": sprint.name,
            "status": sprint.status,
        },
    )

    await db.commit()
    await db.refresh(sprint)

    await manager.broadcast(
        project_id,
        {
            "event": "sprint.created",
            "data": {
                "sprint_id": sprint.id,
                "name": sprint.name,
                "status": sprint.status,
            },
        },
    )

    await manager.broadcast(
        project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": None,
                "action": "SPRINT_CREATED",
                "message": f"{current_user.full_name} created sprint {sprint.name}",
            },
        },
    )

    return sprint


@router.patch("/sprints/{sprint_id}", response_model=SprintOut)
async def update_sprint(
    sprint_id: int,
    payload: SprintUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Sprint).where(Sprint.id == sprint_id))
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    await require_project_editor(db, sprint.project_id, current_user.id)

    before = {
        "name": sprint.name,
        "goal": sprint.goal,
        "start_date": sprint.start_date.isoformat() if sprint.start_date else None,
        "end_date": sprint.end_date.isoformat() if sprint.end_date else None,
        "status": sprint.status,
    }

    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data:
        name = update_data["name"].strip() if update_data["name"] else ""

        if not name:
            raise HTTPException(status_code=400, detail="Sprint name is required")

        sprint.name = name

    if "goal" in update_data:
        sprint.goal = update_data["goal"]

    if "start_date" in update_data:
        sprint.start_date = update_data["start_date"]

    if "end_date" in update_data:
        sprint.end_date = update_data["end_date"]

    if "status" in update_data:
        status_value = update_data["status"].upper()

        if status_value not in VALID_SPRINT_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid sprint status")

        sprint.status = status_value

    after = {
        "name": sprint.name,
        "goal": sprint.goal,
        "start_date": sprint.start_date.isoformat() if sprint.start_date else None,
        "end_date": sprint.end_date.isoformat() if sprint.end_date else None,
        "status": sprint.status,
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
            project_id=sprint.project_id,
            issue_id=None,
            actor_id=current_user.id,
            action="SPRINT_UPDATED",
            message=f"{current_user.full_name} updated sprint {sprint.name}",
            old_value=old_value,
            new_value={
                "sprint_id": sprint.id,
                **new_value,
            },
        )

    await db.commit()
    await db.refresh(sprint)

    await manager.broadcast(
        sprint.project_id,
        {
            "event": "sprint.updated",
            "data": {
                "sprint_id": sprint.id,
                "name": sprint.name,
                "status": sprint.status,
            },
        },
    )

    if old_value:
        await manager.broadcast(
            sprint.project_id,
            {
                "event": "activity.created",
                "data": {
                    "issue_id": None,
                    "action": "SPRINT_UPDATED",
                    "message": f"{current_user.full_name} updated sprint {sprint.name}",
                },
            },
        )

    return sprint


@router.delete("/sprints/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sprint(
    sprint_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Sprint).where(Sprint.id == sprint_id))
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    await require_project_editor(db, sprint.project_id, current_user.id)

    project_id = sprint.project_id
    sprint_name = sprint.name

    await create_activity_log(
        db,
        project_id=project_id,
        issue_id=None,
        actor_id=current_user.id,
        action="SPRINT_DELETED",
        message=f"{current_user.full_name} deleted sprint {sprint_name}",
        old_value={
            "sprint_id": sprint.id,
            "name": sprint.name,
        },
    )

    await db.delete(sprint)
    await db.commit()

    await manager.broadcast(
        project_id,
        {
            "event": "sprint.deleted",
            "data": {
                "sprint_id": sprint_id,
            },
        },
    )

    await manager.broadcast(
        project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": None,
                "action": "SPRINT_DELETED",
                "message": f"{current_user.full_name} deleted sprint {sprint_name}",
            },
        },
    )


@router.patch("/issues/{issue_id}/sprint")
async def update_issue_sprint(
    issue_id: int,
    payload: IssueSprintUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    issue_result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = issue_result.scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    await require_project_editor(db, issue.project_id, current_user.id)

    old_sprint_id = issue.sprint_id

    if payload.sprint_id is not None:
        sprint_result = await db.execute(select(Sprint).where(Sprint.id == payload.sprint_id))
        sprint = sprint_result.scalar_one_or_none()

        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint not found")

        if sprint.project_id != issue.project_id:
            raise HTTPException(status_code=400, detail="Sprint does not belong to this project")

    issue.sprint_id = payload.sprint_id

    await create_activity_log(
        db,
        project_id=issue.project_id,
        issue_id=issue.id,
        actor_id=current_user.id,
        action="ISSUE_SPRINT_UPDATED",
        message=f"{current_user.full_name} updated sprint for {issue.code}",
        old_value={"sprint_id": old_sprint_id},
        new_value={"sprint_id": issue.sprint_id},
    )

    await db.commit()
    await db.refresh(issue)

    await manager.broadcast(
        issue.project_id,
        {
            "event": "issue.sprint_updated",
            "data": {
                "issue_id": issue.id,
                "sprint_id": issue.sprint_id,
            },
        },
    )

    await manager.broadcast(
        issue.project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": issue.id,
                "action": "ISSUE_SPRINT_UPDATED",
                "message": f"{current_user.full_name} updated sprint for {issue.code}",
            },
        },
    )

    return {
        "issue_id": issue.id,
        "sprint_id": issue.sprint_id,
    }