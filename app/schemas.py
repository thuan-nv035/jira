from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6)


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    key: str = Field(min_length=2, max_length=20, pattern=r"^[A-Z][A-Z0-9_]*$")
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    key: str
    description: Optional[str]
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberAdd(BaseModel):
    email: EmailStr
    role: str = Field(default="MEMBER", pattern=r"^(ADMIN|MEMBER|VIEWER)$")

class MemberRoleUpdate(BaseModel):
    role: str = Field(pattern=r"^(ADMIN|MEMBER|VIEWER)$")

class MemberOut(BaseModel):
    id: int
    project_id: int
    user_id: int
    role: str
    user: UserOut

    model_config = ConfigDict(from_attributes=True)


class ColumnCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    position: int = 0


class ColumnUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    position: Optional[int] = None


class ColumnOut(BaseModel):
    id: int
    project_id: int
    name: str
    position: int

    model_config = ConfigDict(from_attributes=True)


class IssueCreate(BaseModel):
    column_id: int
    title: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    issue_type: str = Field(default="TASK", pattern=r"^(TASK|BUG|STORY)$")
    priority: str = Field(default="MEDIUM", pattern=r"^(LOW|MEDIUM|HIGH|URGENT)$")
    due_date: Optional[datetime] = None

class IssueUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    issue_type: Optional[str] = Field(default=None, pattern=r"^(TASK|BUG|STORY)$")
    priority: Optional[str] = Field(default=None, pattern=r"^(LOW|MEDIUM|HIGH|URGENT)$")
    due_date: Optional[datetime] = None

class IssueMove(BaseModel):
    column_id: int
    position: int = 0

class LabelCreate(BaseModel):
    name: str
    color: str = "#64748b"


class LabelUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


class LabelOut(BaseModel):
    id: int
    project_id: int
    name: str
    color: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IssueOut(BaseModel):
    id: int
    project_id: int
    column_id: int
    reporter_id: Optional[int]
    assignee_id: Optional[int]
    code: str
    title: str
    description: Optional[str]
    issue_type: str
    priority: str
    position: int
    attachment_count: int = 0
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
    is_overdue: bool = False
    checklist_total: int = 0
    checklist_done: int = 0
    labels: list[LabelOut] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    body: str = Field(min_length=1)


class CommentOut(BaseModel):
    id: int
    issue_id: int
    author_id: int
    body: str
    created_at: datetime
    author: UserOut

    model_config = ConfigDict(from_attributes=True)


class NotificationOut(BaseModel):
    id: int
    recipient_id: int
    actor_id: Optional[int]
    project_id: Optional[int]
    issue_id: Optional[int]
    type: str
    title: str
    message: Optional[str]
    is_read: bool
    created_at: datetime
    actor: Optional[UserOut] = None

    model_config = ConfigDict(from_attributes=True)


class UnreadCountOut(BaseModel):
    unread_count: int

class AttachmentOut(BaseModel):
    id: int
    issue_id: int
    uploader_id: Optional[int]
    original_name: str
    content_type: Optional[str]
    size_bytes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ActivityActorOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class ActivityLogOut(BaseModel):
    id: int
    project_id: int
    issue_id: Optional[int]
    actor_id: Optional[int]

    action: str
    message: str

    old_value: Optional[dict[str, Any]] = None
    new_value: Optional[dict[str, Any]] = None

    created_at: datetime
    actor: Optional[ActivityActorOut] = None

    model_config = ConfigDict(from_attributes=True)

class ChecklistCreate(BaseModel):
    title: str
    position: Optional[int] = None


class ChecklistUpdate(BaseModel):
    title: Optional[str] = None
    is_done: Optional[bool] = None
    position: Optional[int] = None


class ChecklistOut(BaseModel):
    id: int
    issue_id: int
    creator_id: Optional[int]
    title: str
    is_done: bool
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DashboardSummaryOut(BaseModel):
    total_issues: int
    done_issues: int
    in_progress_issues: int
    overdue_issues: int
    unassigned_issues: int
    total_members: int


class DashboardStatusItemOut(BaseModel):
    column_id: int
    column_name: str
    total: int


class DashboardPriorityItemOut(BaseModel):
    priority: str
    total: int


class DashboardAssigneeItemOut(BaseModel):
    assignee_id: Optional[int]
    full_name: Optional[str] = None
    email: Optional[str] = None
    total: int