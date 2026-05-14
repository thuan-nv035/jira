from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user, require_project_editor, require_project_member
from app.models import Issue, Label, User, issue_labels_table
from app.schemas import LabelCreate, LabelOut, LabelUpdate
from app.services.activity_logs import create_activity_log
from app.websocket_manager import manager

router = APIRouter(tags=["Labels"])


async def _get_issue_and_check_member(
    db: AsyncSession,
    issue_id: int,
    user_id: int,
) -> Issue:
    result = await db.execute(
        select(Issue)
        .options(selectinload(Issue.labels))
        .where(Issue.id == issue_id)
    )
    issue = result.scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    await require_project_member(db, issue.project_id, user_id)
    return issue


async def _get_issue_and_check_editor(
    db: AsyncSession,
    issue_id: int,
    user_id: int,
) -> Issue:
    result = await db.execute(
        select(Issue)
        .options(selectinload(Issue.labels))
        .where(Issue.id == issue_id)
    )
    issue = result.scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    await require_project_editor(db, issue.project_id, user_id)
    return issue


async def _get_label(db: AsyncSession, label_id: int) -> Label:
    result = await db.execute(select(Label).where(Label.id == label_id))
    label = result.scalar_one_or_none()

    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    return label


async def _check_duplicate_label(
    db: AsyncSession,
    project_id: int,
    name: str,
    exclude_label_id: int | None = None,
):
    query = select(Label).where(
        Label.project_id == project_id,
        func.lower(Label.name) == name.lower(),
    )

    if exclude_label_id is not None:
        query = query.where(Label.id != exclude_label_id)

    result = await db.execute(query)
    exists = result.scalar_one_or_none()

    if exists:
        raise HTTPException(status_code=400, detail="Label name already exists")


@router.get("/projects/{project_id}/labels", response_model=list[LabelOut])
async def list_project_labels(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_member(db, project_id, current_user.id)

    result = await db.execute(
        select(Label)
        .where(Label.project_id == project_id)
        .order_by(Label.name.asc())
    )

    return result.scalars().all()


@router.post(
    "/projects/{project_id}/labels",
    response_model=LabelOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_label(
    project_id: int,
    payload: LabelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_project_editor(db, project_id, current_user.id)

    name = payload.name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Label name is required")

    await _check_duplicate_label(db, project_id, name)

    label = Label(
        project_id=project_id,
        name=name,
        color=payload.color or "#64748b",
    )

    db.add(label)
    await db.flush()

    await create_activity_log(
        db,
        project_id=project_id,
        issue_id=None,
        actor_id=current_user.id,
        action="LABEL_CREATED",
        message=f"{current_user.full_name} created label {label.name}",
        new_value={
            "label_id": label.id,
            "name": label.name,
            "color": label.color,
        },
    )

    await db.commit()
    await db.refresh(label)

    await manager.broadcast(
        project_id,
        {
            "event": "label.created",
            "data": {
                "label_id": label.id,
                "name": label.name,
                "color": label.color,
            },
        },
    )

    await manager.broadcast(
        project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": None,
                "action": "LABEL_CREATED",
                "message": f"{current_user.full_name} created label {label.name}",
            },
        },
    )

    return label


@router.patch("/labels/{label_id}", response_model=LabelOut)
async def update_label(
    label_id: int,
    payload: LabelUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    label = await _get_label(db, label_id)

    await require_project_editor(db, label.project_id, current_user.id)

    before = {
        "name": label.name,
        "color": label.color,
    }

    if payload.name is not None:
        name = payload.name.strip()

        if not name:
            raise HTTPException(status_code=400, detail="Label name is required")

        await _check_duplicate_label(
            db,
            label.project_id,
            name,
            exclude_label_id=label.id,
        )

        label.name = name

    if payload.color is not None:
        label.color = payload.color

    after = {
        "name": label.name,
        "color": label.color,
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
            project_id=label.project_id,
            issue_id=None,
            actor_id=current_user.id,
            action="LABEL_UPDATED",
            message=f"{current_user.full_name} updated label {label.name}",
            old_value=old_value,
            new_value={
                "label_id": label.id,
                **new_value,
            },
        )

    await db.commit()
    await db.refresh(label)

    await manager.broadcast(
        label.project_id,
        {
            "event": "label.updated",
            "data": {
                "label_id": label.id,
                "name": label.name,
                "color": label.color,
            },
        },
    )

    if old_value:
        await manager.broadcast(
            label.project_id,
            {
                "event": "activity.created",
                "data": {
                    "issue_id": None,
                    "action": "LABEL_UPDATED",
                    "message": f"{current_user.full_name} updated label {label.name}",
                },
            },
        )

    return label


@router.delete("/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    label_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    label = await _get_label(db, label_id)

    await require_project_editor(db, label.project_id, current_user.id)

    project_id = label.project_id
    label_name = label.name

    await create_activity_log(
        db,
        project_id=project_id,
        issue_id=None,
        actor_id=current_user.id,
        action="LABEL_DELETED",
        message=f"{current_user.full_name} deleted label {label_name}",
        old_value={
            "label_id": label.id,
            "name": label.name,
            "color": label.color,
        },
    )

    await db.delete(label)
    await db.commit()

    await manager.broadcast(
        project_id,
        {
            "event": "label.deleted",
            "data": {
                "label_id": label_id,
            },
        },
    )

    await manager.broadcast(
        project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": None,
                "action": "LABEL_DELETED",
                "message": f"{current_user.full_name} deleted label {label_name}",
            },
        },
    )


@router.get("/issues/{issue_id}/labels", response_model=list[LabelOut])
async def list_issue_labels(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    issue = await _get_issue_and_check_member(db, issue_id, current_user.id)

    return issue.labels


@router.post("/issues/{issue_id}/labels/{label_id}", response_model=list[LabelOut])
async def add_label_to_issue(
    issue_id: int,
    label_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    issue = await _get_issue_and_check_editor(db, issue_id, current_user.id)
    label = await _get_label(db, label_id)

    if label.project_id != issue.project_id:
        raise HTTPException(status_code=400, detail="Label does not belong to this project")

    exists_result = await db.execute(
        select(issue_labels_table).where(
            issue_labels_table.c.issue_id == issue_id,
            issue_labels_table.c.label_id == label_id,
        )
    )

    if exists_result.first():
        return issue.labels

    await db.execute(
        issue_labels_table.insert().values(
            issue_id=issue_id,
            label_id=label_id,
        )
    )

    await create_activity_log(
        db,
        project_id=issue.project_id,
        issue_id=issue.id,
        actor_id=current_user.id,
        action="ISSUE_LABEL_ADDED",
        message=f"{current_user.full_name} added label {label.name} to {issue.code}",
        new_value={
            "label_id": label.id,
            "name": label.name,
            "color": label.color,
        },
    )

    await db.commit()

    result = await db.execute(
        select(Issue)
        .options(selectinload(Issue.labels))
        .where(Issue.id == issue_id)
    )
    issue = result.scalar_one()

    await manager.broadcast(
        issue.project_id,
        {
            "event": "issue.label_added",
            "data": {
                "issue_id": issue.id,
                "label_id": label.id,
                "name": label.name,
                "color": label.color,
            },
        },
    )

    await manager.broadcast(
        issue.project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": issue.id,
                "action": "ISSUE_LABEL_ADDED",
                "message": f"{current_user.full_name} added label {label.name} to {issue.code}",
            },
        },
    )

    return issue.labels


@router.delete("/issues/{issue_id}/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_label_from_issue(
    issue_id: int,
    label_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    issue = await _get_issue_and_check_editor(db, issue_id, current_user.id)
    label = await _get_label(db, label_id)

    if label.project_id != issue.project_id:
        raise HTTPException(status_code=400, detail="Label does not belong to this project")

    await db.execute(
        issue_labels_table.delete().where(
            issue_labels_table.c.issue_id == issue_id,
            issue_labels_table.c.label_id == label_id,
        )
    )

    await create_activity_log(
        db,
        project_id=issue.project_id,
        issue_id=issue.id,
        actor_id=current_user.id,
        action="ISSUE_LABEL_REMOVED",
        message=f"{current_user.full_name} removed label {label.name} from {issue.code}",
        old_value={
            "label_id": label.id,
            "name": label.name,
            "color": label.color,
        },
    )

    await db.commit()

    await manager.broadcast(
        issue.project_id,
        {
            "event": "issue.label_removed",
            "data": {
                "issue_id": issue.id,
                "label_id": label.id,
            },
        },
    )

    await manager.broadcast(
        issue.project_id,
        {
            "event": "activity.created",
            "data": {
                "issue_id": issue.id,
                "action": "ISSUE_LABEL_REMOVED",
                "message": f"{current_user.full_name} removed label {label.name} from {issue.code}",
            },
        },
    )