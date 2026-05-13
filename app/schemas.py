from datetime import datetime
from typing import Optional

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
    role: str = Field(default="MEMBER", pattern=r"^(ADMIN|MEMBER)$")


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


class IssueUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    issue_type: Optional[str] = Field(default=None, pattern=r"^(TASK|BUG|STORY)$")
    priority: Optional[str] = Field(default=None, pattern=r"^(LOW|MEDIUM|HIGH|URGENT)$")


class IssueMove(BaseModel):
    column_id: int
    position: int = 0


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
    created_at: datetime
    updated_at: datetime

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
