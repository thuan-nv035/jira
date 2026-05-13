from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, require_project_editor, require_project_member
from app.models import Issue, IssueAttachment, User
from app.schemas import AttachmentOut
from app.services.notifications import notify_project_members
from app.websocket_manager import manager
from typing import List
router = APIRouter(prefix="/issues/{issue_id}/attachments", tags=["Attachments"])

UPLOAD_DIR = Path("uploads/issues")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


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

async def _get_issue_and_check_editor(
    db: AsyncSession,
    issue_id: int,
    user_id: int,
) -> Issue:
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    await require_project_editor(db, issue.project_id, user_id)

    return issue

def _safe_filename(filename: str) -> str:
    return Path(filename).name.replace("/", "_").replace("\\", "_")

async def _save_upload_file(
    db: AsyncSession,
    issue_id: int,
    uploader_id: int,
    file: UploadFile,
) -> IssueAttachment:
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")

    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail=f"File {file.filename} is empty")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File {file.filename} must be less than 10MB",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    original_name = _safe_filename(file.filename)
    stored_name = f"{uuid4().hex}_{original_name}"
    storage_path = UPLOAD_DIR / stored_name

    storage_path.write_bytes(content)

    attachment = IssueAttachment(
        issue_id=issue_id,
        uploader_id=uploader_id,
        original_name=original_name,
        stored_name=stored_name,
        storage_path=str(storage_path).replace("\\", "/"),
        content_type=file.content_type,
        size_bytes=len(content),
    )

    db.add(attachment)
    return attachment

@router.get("", response_model=list[AttachmentOut])
async def list_attachments(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_issue_and_check_member(db, issue_id, current_user.id)

    result = await db.execute(
        select(IssueAttachment)
        .where(IssueAttachment.issue_id == issue_id)
        .order_by(IssueAttachment.created_at.desc())
    )

    return result.scalars().all()


@router.post("", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    issue_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    issue = await _get_issue_and_check_editor(db, issue_id, current_user.id)

    attachment = await _save_upload_file(
        db=db,
        issue_id=issue_id,
        uploader_id=current_user.id,
        file=file,
    )

    await db.commit()
    await db.refresh(attachment)

    await manager.broadcast(
        issue.project_id,
        {
            "event": "attachment.uploaded",
            "data": {
                "issue_id": issue.id,
                "attachment_id": attachment.id,
                "file_name": attachment.original_name,
            },
        },
    )

    await notify_project_members(
        db,
        project_id=issue.project_id,
        actor_id=current_user.id,
        notification_type="ATTACHMENT_UPLOADED",
        title=f"New attachment on {issue.code}",
        message=attachment.original_name,
        issue_id=issue.id,
    )

    return attachment

@router.post("/bulk", response_model=list[AttachmentOut], status_code=status.HTTP_201_CREATED)
async def upload_many_attachments(
    issue_id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    issue = await _get_issue_and_check_member(db, issue_id, current_user.id)

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    if len(files) > 10:
        raise HTTPException(status_code=400, detail="You can upload up to 10 files at once")

    attachments = []

    for file in files:
        attachment = await _save_upload_file(
            db=db,
            issue_id=issue_id,
            uploader_id=current_user.id,
            file=file,
        )
        attachments.append(attachment)

    await db.commit()

    for attachment in attachments:
        await db.refresh(attachment)

    for attachment in attachments:
        await manager.broadcast(
            issue.project_id,
            {
                "event": "attachment.uploaded",
                "data": {
                    "issue_id": issue.id,
                    "attachment_id": attachment.id,
                    "file_name": attachment.original_name,
                },
            },
        )

    await notify_project_members(
        db,
        project_id=issue.project_id,
        actor_id=current_user.id,
        notification_type="ATTACHMENT_UPLOADED",
        title=f"New attachments on {issue.code}",
        message=f"{len(attachments)} files uploaded",
        issue_id=issue.id,
    )

    return attachments

@router.get("/{attachment_id}/download")
async def download_attachment(
    issue_id: int,
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_issue_and_check_member(db, issue_id, current_user.id)

    result = await db.execute(
        select(IssueAttachment).where(
            IssueAttachment.id == attachment_id,
            IssueAttachment.issue_id == issue_id,
        )
    )
    attachment = result.scalar_one_or_none()

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    file_path = Path(attachment.storage_path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=file_path,
        filename=attachment.original_name,
        media_type=attachment.content_type or "application/octet-stream",
    )

@router.get("/{attachment_id}/view")
async def view_attachment(
    issue_id: int,
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_issue_and_check_member(db, issue_id, current_user.id)

    result = await db.execute(
        select(IssueAttachment).where(
            IssueAttachment.id == attachment_id,
            IssueAttachment.issue_id == issue_id,
        )
    )
    attachment = result.scalar_one_or_none()

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    file_path = Path(attachment.storage_path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=file_path,
        media_type=attachment.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'inline; filename="{attachment.original_name}"'
        },
    )

@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    issue_id: int,
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    issue = await _get_issue_and_check_editor(db, issue_id, current_user.id)

    result = await db.execute(
        select(IssueAttachment).where(
            IssueAttachment.id == attachment_id,
            IssueAttachment.issue_id == issue_id,
        )
    )
    attachment = result.scalar_one_or_none()

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    file_path = Path(attachment.storage_path)

    await db.delete(attachment)
    await db.commit()

    if file_path.exists():
        file_path.unlink()

    await manager.broadcast(
        issue.project_id,
        {
            "event": "attachment.deleted",
            "data": {
                "issue_id": issue.id,
                "attachment_id": attachment_id,
            },
        },
    )