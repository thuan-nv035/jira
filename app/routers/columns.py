from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, require_project_admin, require_project_member
from app.models import BoardColumn, Issue, User
from app.schemas import ColumnCreate, ColumnOut, ColumnUpdate
from app.websocket_manager import manager

router = APIRouter(prefix="/projects/{project_id}/columns", tags=["Columns"])


@router.get("", response_model=list[ColumnOut])
async def list_columns(project_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_member(db, project_id, current_user.id)
    result = await db.execute(
        select(BoardColumn).where(BoardColumn.project_id == project_id).order_by(BoardColumn.position.asc())
    )
    return result.scalars().all()


@router.post("", response_model=ColumnOut, status_code=status.HTTP_201_CREATED)
async def create_column(project_id: int, payload: ColumnCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_admin(db, project_id, current_user.id)
    column = BoardColumn(project_id=project_id, name=payload.name, position=payload.position)
    db.add(column)
    await db.commit()
    await db.refresh(column)
    await manager.broadcast(project_id, {"event": "column.created", "data": {"column_id": column.id}})
    return column


@router.patch("/{column_id}", response_model=ColumnOut)
async def update_column(project_id: int, column_id: int, payload: ColumnUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_admin(db, project_id, current_user.id)
    result = await db.execute(
        select(BoardColumn).where(BoardColumn.id == column_id, BoardColumn.project_id == project_id)
    )
    column = result.scalar_one_or_none()
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(column, key, value)

    await db.commit()
    await db.refresh(column)
    await manager.broadcast(project_id, {"event": "column.updated", "data": {"column_id": column.id}})
    return column


@router.delete("/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column(project_id: int, column_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await require_project_admin(db, project_id, current_user.id)
    result = await db.execute(
        select(BoardColumn).where(BoardColumn.id == column_id, BoardColumn.project_id == project_id)
    )
    column = result.scalar_one_or_none()
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")

    issue_count_result = await db.execute(select(func.count(Issue.id)).where(Issue.column_id == column_id))
    if issue_count_result.scalar_one() > 0:
        raise HTTPException(status_code=400, detail="Cannot delete a column that still has issues")

    await db.delete(column)
    await db.commit()
    await manager.broadcast(project_id, {"event": "column.deleted", "data": {"column_id": column_id}})
