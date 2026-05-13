from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    activity_logs: Mapped[list["ActivityLog"]] = relationship(back_populates="actor")
    memberships: Mapped[list["ProjectMember"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(
        foreign_keys="Notification.recipient_id",
        back_populates="recipient",
        cascade="all, delete-orphan",
    )


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    key: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    columns: Mapped[list["BoardColumn"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    issues: Mapped[list["Issue"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    members: Mapped[list["ProjectMember"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan"
    )

class ProjectMember(Base, TimestampMixin):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(30), default="MEMBER")  # OWNER | ADMIN | MEMBER

    project: Mapped[Project] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="memberships")


class BoardColumn(Base, TimestampMixin):
    __tablename__ = "board_columns"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_project_column_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    position: Mapped[int] = mapped_column(default=0)

    project: Mapped[Project] = relationship(back_populates="columns")
    issues: Mapped[list["Issue"]] = relationship(back_populates="column")


class Issue(Base, TimestampMixin):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    column_id: Mapped[int] = mapped_column(ForeignKey("board_columns.id", ondelete="RESTRICT"), index=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)  # Example: DEMO-1
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    issue_type: Mapped[str] = mapped_column(String(30), default="TASK")  # TASK | BUG | STORY
    priority: Mapped[str] = mapped_column(String(30), default="MEDIUM")  # LOW | MEDIUM | HIGH | URGENT
    position: Mapped[int] = mapped_column(default=0)

    project: Mapped[Project] = relationship(back_populates="issues")
    column: Mapped[BoardColumn] = relationship(back_populates="issues")
    reporter: Mapped[Optional[User]] = relationship(foreign_keys=[reporter_id])
    assignee: Mapped[Optional[User]] = relationship(foreign_keys=[assignee_id])
    comments: Mapped[list["Comment"]] = relationship(back_populates="issue", cascade="all, delete-orphan")
    attachments: Mapped[list["IssueAttachment"]] = relationship(
        back_populates="issue",
        cascade="all, delete-orphan"
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        back_populates="issue",
        cascade="all, delete-orphan"
    )

    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    checklists: Mapped[list["ChecklistItem"]] = relationship(
        back_populates="issue",
        cascade="all, delete-orphan"
    )

    @property
    def is_overdue(self) -> bool:
        if not self.due_date:
            return False

        now = datetime.now(timezone.utc)
        due = self.due_date

        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)

        return due < now

class Comment(Base, TimestampMixin):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    body: Mapped[str] = mapped_column(Text)

    issue: Mapped[Issue] = relationship(back_populates="comments")
    author: Mapped[User] = relationship()


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    actor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    issue_id: Mapped[Optional[int]] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), nullable=True, index=True)

    type: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    recipient: Mapped[User] = relationship(foreign_keys=[recipient_id], back_populates="notifications")
    actor: Mapped[Optional[User]] = relationship(foreign_keys=[actor_id])
    project: Mapped[Optional[Project]] = relationship()
    issue: Mapped[Optional[Issue]] = relationship()

class IssueAttachment(Base, TimestampMixin):
    __tablename__ = "issue_attachments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), index=True)
    uploader_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255), unique=True)
    storage_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int] = mapped_column(default=0)

    issue: Mapped[Issue] = relationship(back_populates="attachments")
    uploader: Mapped[Optional[User]] = relationship()

class ActivityLog(Base, TimestampMixin):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )

    issue_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("issues.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    actor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(String(80), index=True)
    message: Mapped[str] = mapped_column(Text)

    old_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="activity_logs")
    issue: Mapped[Optional["Issue"]] = relationship(back_populates="activity_logs")
    actor: Mapped[Optional["User"]] = relationship(back_populates="activity_logs")

class ChecklistItem(Base, TimestampMixin):
    __tablename__ = "checklist_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    issue_id: Mapped[int] = mapped_column(
        ForeignKey("issues.id", ondelete="CASCADE"),
        index=True
    )

    creator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    title: Mapped[str] = mapped_column(String(255))
    is_done: Mapped[bool] = mapped_column(default=False)
    position: Mapped[int] = mapped_column(default=0)

    issue: Mapped["Issue"] = relationship(back_populates="checklists")
    creator: Mapped[Optional["User"]] = relationship()