from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification, ProjectMember
from app.websocket_manager import manager


async def notify_project_members(
    db: AsyncSession,
    project_id: int,
    actor_id: int | None,
    notification_type: str,
    title: str,
    message: str | None = None,
    issue_id: int | None = None,
    exclude_actor: bool = True,
    exclude_user_ids: set[int] | None = None,
) -> list[Notification]:
    """Create notifications for all members in a project and broadcast a realtime event."""
    result = await db.execute(select(ProjectMember.user_id).where(ProjectMember.project_id == project_id))
    user_ids = list(dict.fromkeys(result.scalars().all()))

    excluded = exclude_user_ids or set()

    notifications: list[Notification] = []
    for user_id in user_ids:
        if exclude_actor and actor_id is not None and user_id == actor_id:
            continue
        if user_id in excluded:
            continue
        notification = Notification(
            recipient_id=user_id,
            actor_id=actor_id,
            project_id=project_id,
            issue_id=issue_id,
            type=notification_type,
            title=title,
            message=message,
        )
        db.add(notification)
        notifications.append(notification)

    if notifications:
        await db.commit()
        await manager.broadcast(
            project_id,
            {
                "event": "notification.created",
                "data": {
                    "project_id": project_id,
                    "issue_id": issue_id,
                    "type": notification_type,
                    "title": title,
                },
            },
        )

    return notifications


async def notify_user(
    db: AsyncSession,
    recipient_id: int,
    actor_id: int | None,
    notification_type: str,
    title: str,
    message: str | None = None,
    project_id: int | None = None,
    issue_id: int | None = None,
) -> Notification:
    notification = Notification(
        recipient_id=recipient_id,
        actor_id=actor_id,
        project_id=project_id,
        issue_id=issue_id,
        type=notification_type,
        title=title,
        message=message,
    )
    db.add(notification)
    await db.commit()

    if project_id is not None:
        await manager.broadcast(
            project_id,
            {
                "event": "notification.created",
                "data": {
                    "project_id": project_id,
                    "issue_id": issue_id,
                    "type": notification_type,
                    "title": title,
                },
            },
        )

    return notification



async def notify_specific_users(
    db: AsyncSession,
    *,
    user_ids: list[int],
    project_id: int,
    actor_id: int | None,
    notification_type: str,
    title: str,
    message: str | None = None,
    issue_id: int | None = None,
):
    unique_user_ids = set(user_ids)

    if actor_id in unique_user_ids:
        unique_user_ids.remove(actor_id)

    if not unique_user_ids:
        return []

    member_result = await db.execute(
        select(ProjectMember.user_id).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id.in_(unique_user_ids),
        )
    )

    valid_user_ids = list(dict.fromkeys(member_result.scalars().all()))

    notifications = []

    for user_id in valid_user_ids:
        notification = Notification(
            recipient_id=user_id,
            actor_id=actor_id,
            project_id=project_id,
            issue_id=issue_id,
            type=notification_type,
            title=title,
            message=message,
        )

        db.add(notification)
        notifications.append(notification)

    if notifications:
        await db.flush()

        await manager.broadcast(
            project_id,
            {
                "event": "notification.created",
                "data": {
                    "project_id": project_id,
                    "issue_id": issue_id,
                    "type": notification_type,
                    "title": title,
                    "message": message,
                    "recipient_ids": valid_user_ids,
                },
            },
        )

    return notifications
