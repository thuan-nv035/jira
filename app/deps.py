from numbers import Number

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ProjectMember, User, Project
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await get_user_from_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_user_from_token(db: AsyncSession, token: str | None) -> User | None:
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    try:
        user_id = int(payload["sub"])
    except ValueError:
        return None
    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    return result.scalar_one_or_none()


async def require_project_member(
    db: AsyncSession,
    project_id: int,
    user_id: int,
) -> ProjectMember:
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    member_result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    member = member_result.scalar_one_or_none()

    if member:
        return member

    if int(project.owner_id) == int(user_id):
        owner_member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role="OWNER",
        )

        db.add(owner_member)
        await db.flush()

        return owner_member

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not a member of this project",
    )

async def require_project_admin(db: AsyncSession, project_id: int, user_id: int) -> ProjectMember:
    member = await require_project_member(db, project_id, user_id)
    if member.role not in {"OWNER", "ADMIN"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permission required")
    return member

PROJECT_ROLES = {
    "OWNER": 4,
    "ADMIN": 3,
    "MEMBER": 2,
    "VIEWER": 1,
}


def has_role_at_least(current_role: str, required_role: str) -> bool:
    return PROJECT_ROLES.get(current_role, 0) >= PROJECT_ROLES.get(required_role, 0)


async def require_project_owner(
    db: AsyncSession,
    project_id: int,
    user_id: int,
) -> ProjectMember:
    member = await require_project_member(db, project_id, user_id)

    if member.role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner permission required",
        )

    return member


async def require_project_editor(
    db: AsyncSession,
    project_id: int,
    user_id: int,
) -> ProjectMember:
    member = await require_project_member(db, project_id, user_id)

    if member.role not in {"OWNER", "ADMIN", "MEMBER"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit permission required",
        )

    return member