from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user, require_project_admin, require_project_member
from app.models import BoardColumn, Project, ProjectMember, User
from app.schemas import MemberAdd, MemberOut, ProjectCreate, ProjectOut, ProjectUpdate
from app.services.notifications import notify_project_members, notify_user
from app.websocket_manager import manager

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectOut])
async def list_projects(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == current_user.id)
        .order_by(Project.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.key == payload.key.upper()))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Project key already exists")

    project = Project(
        name=payload.name,
        key=payload.key.upper(),
        description=payload.description,
        owner_id=current_user.id,
    )
    db.add(project)
    await db.flush()

    db.add(ProjectMember(project_id=project.id, user_id=current_user.id, role="OWNER"))

    default_columns = ["TO DO", "IN PROGRESS", "REVIEW", "DONE"]
    for index, name in enumerate(default_columns):
        db.add(BoardColumn(project_id=project.id, name=name, position=index))

    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_member(db, project_id, current_user.id)
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: int, payload: ProjectUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_admin(db, project_id, current_user.id)
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(project, key, value)

    await db.commit()
    await db.refresh(project)
    await manager.broadcast(project_id, {"event": "project.updated", "data": {"project_id": project_id}})
    return project


@router.get("/{project_id}/members", response_model=list[MemberOut])
async def list_members(project_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_member(db, project_id, current_user.id)
    result = await db.execute(
        select(ProjectMember)
        .options(selectinload(ProjectMember.user))
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.created_at.asc())
    )
    return result.scalars().all()


@router.post("/{project_id}/members", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
async def add_member(project_id: int, payload: MemberAdd, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_admin(db, project_id, current_user.id)

    user_result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    exists_result = await db.execute(
        select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == user.id)
    )
    if exists_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a member")

    member = ProjectMember(project_id=project_id, user_id=user.id, role=payload.role)
    db.add(member)
    await db.commit()

    result = await db.execute(
        select(ProjectMember).options(selectinload(ProjectMember.user)).where(ProjectMember.id == member.id)
    )
    saved_member = result.scalar_one()
    await manager.broadcast(project_id, {"event": "member.added", "data": {"user_id": user.id, "role": payload.role}})
    await notify_user(
        db,
        recipient_id=user.id,
        actor_id=current_user.id,
        notification_type="MEMBER_ADDED",
        title="You were added to a project",
        message=f"You were added to project #{project_id} as {payload.role}.",
        project_id=project_id,
    )
    await notify_project_members(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        notification_type="MEMBER_ADDED",
        title="New project member",
        message=f"{user.full_name} joined the project as {payload.role}.",
        exclude_actor=True,
        exclude_user_ids={user.id},
    )
    return saved_member
