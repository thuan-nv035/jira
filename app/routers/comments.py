from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user, require_project_editor, require_project_member
from app.models import Comment, Issue, User
from app.schemas import CommentCreate, CommentOut
from app.services.notifications import notify_project_members
from app.websocket_manager import manager

router = APIRouter(prefix="/issues/{issue_id}/comments", tags=["Comments"])


async def _get_issue_and_check_member(db: AsyncSession, issue_id: int, user_id: int) -> Issue:
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    await require_project_member(db, issue.project_id, user_id)
    return issue


@router.get("", response_model=list[CommentOut])
async def list_comments(issue_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _get_issue_and_check_member(db, issue_id, current_user.id)
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(Comment.issue_id == issue_id)
        .order_by(Comment.created_at.asc())
    )
    return result.scalars().all()


@router.post("", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(issue_id: int, payload: CommentCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    issue = await require_project_editor(db, issue_id, current_user.id)
    comment = Comment(issue_id=issue_id, author_id=current_user.id, body=payload.body)
    db.add(comment)
    await db.commit()

    result = await db.execute(select(Comment).options(selectinload(Comment.author)).where(Comment.id == comment.id))
    saved_comment = result.scalar_one()
    await manager.broadcast(issue.project_id, {"event": "comment.created", "data": {"issue_id": issue_id, "comment_id": saved_comment.id}})
    await notify_project_members(
        db,
        project_id=issue.project_id,
        actor_id=current_user.id,
        notification_type="COMMENT_CREATED",
        title=f"New comment on {issue.code}",
        message=payload.body[:180],
        issue_id=issue.id,
    )
    return saved_comment
