from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=72,
    )


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# -------------------------
# Team schemas
# -------------------------

class TeamCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )


class TeamResponse(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# Project schemas
# -------------------------

class ProjectCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=3000,
    )

    status: str = Field(
        default="active",
        pattern="^(active|completed|on_hold|archived)$",
    )

    start_date: date | None = None
    due_date: date | None = None

    team_id: int


class ProjectUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=3000,
    )

    status: str | None = Field(
        default=None,
        pattern="^(active|completed|on_hold|archived)$",
    )

    start_date: date | None = None
    due_date: date | None = None

    team_id: int | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    status: str
    start_date: date | None
    due_date: date | None
    team_id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# Task schemas
# -------------------------

class TaskCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    due_date: date | None = None

    priority: str = Field(
        default="medium",
        pattern="^(low|medium|high)$",
    )

    category: str = Field(
        default="other",
        pattern="^(work|development|study|personal|other)$",
    )

    status: str = Field(
        default="todo",
        pattern="^(todo|in_progress|in_review|completed)$",
    )

    project_id: int | None = None

    assignee_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    due_date: date | None = None

    priority: str | None = Field(
        default=None,
        pattern="^(low|medium|high)$",
    )

    category: str | None = Field(
        default=None,
        pattern="^(work|development|study|personal|other)$",
    )

    status: str | None = Field(
        default=None,
        pattern="^(todo|in_progress|in_review|completed)$",
    )

    project_id: int | None = None

    assignee_id: int | None = None

    completed: bool | None = None

    completion_note: str | None = Field(
        default=None,
        max_length=2000,
    )


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    due_date: date | None
    priority: str
    category: str

    status: str
    completed: bool

    completed_at: datetime | None
    completion_note: str | None

    user_id: int
    project_id: int | None
    assignee_id: int | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# Team member schemas
# -------------------------

class TeamMemberCreate(BaseModel):
    user_id: int

    role: str = Field(
        default="member",
        pattern="^(member|admin)$",
    )


class TeamMemberResponse(BaseModel):
    id: int
    team_id: int
    user_id: int
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# Subtask schemas
# -------------------------

class SubtaskCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )


class SubtaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    completed: bool | None = None


class SubtaskResponse(BaseModel):
    id: int
    title: str
    completed: bool
    task_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# Task progress schemas
# -------------------------

class TaskProgressResponse(BaseModel):
    task_id: int
    total_subtasks: int
    completed_subtasks: int
    progress: int


# Comment schemas
class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    id: int
    content: str
    task_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Activity schemas

class ActivityResponse(BaseModel):
    id: int
    action: str
    description: str
    task_id: int | None
    project_id: int | None
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Notification schemas

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    user_id: int
    task_id: int | None
    project_id: int | None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationReadUpdate(BaseModel):
    is_read: bool




