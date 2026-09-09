from datetime import date, datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src import models
from src.auth import get_current_user
from src.database import Base, engine, get_db, migrate_database
from src.schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    SubtaskCreate,
    SubtaskResponse,
    SubtaskUpdate,
    TaskCreate,
    TaskProgressResponse,
    TaskResponse,
    TaskUpdate,
    TeamCreate,
    TeamMemberCreate,
    TeamMemberResponse,
    TeamResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    ActivityResponse,
    NotificationResponse,
    NotificationReadUpdate,
    ProjectOverviewResponse,
    ProjectDashboardResponse,
)
from src.security import create_access_token, hash_password, verify_password


Base.metadata.create_all(bind=engine)
migrate_database()


app = FastAPI(
    title="TaskFlow API",
    description="A full-stack task and project management API.",
    version="2.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Notification helper
# -------------------------

def create_notification(
    db,
    *,
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
    task_id: int | None = None,
    project_id: int | None = None,
):
    notification = models.Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        task_id=task_id,
        project_id=project_id,
        is_read=False,
    )

    db.add(notification)

    return notification


# -------------------------
# Basic endpoints
# -------------------------

@app.get("/")
def root():
    return {
        "message": "TaskFlow API is running",
        "version": "2.0.0",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# -------------------------
# Authentication
# -------------------------

@app.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(models.User)
        .filter(
            (models.User.username == user.username)
            | (models.User.email == user.email)
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(models.User)
        .filter(models.User.username == user.username)
        .first()
    )

    if not existing_user or not verify_password(
        user.password,
        existing_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(
        data={"sub": str(existing_user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get(
    "/me",
    response_model=UserResponse,
)
def get_my_profile(
    current_user: models.User = Depends(get_current_user),
):
    return current_user


# -------------------------
# Team helpers
# -------------------------

def get_user_team(
    team_id: int,
    current_user: models.User,
    db: Session,
):
    membership = (
        db.query(models.TeamMember)
        .filter(
            models.TeamMember.team_id == team_id,
            models.TeamMember.user_id == current_user.id,
        )
        .first()
    )

    if membership:
        return membership

    team = (
        db.query(models.Team)
        .filter(
            models.Team.id == team_id,
            models.Team.owner_id == current_user.id,
        )
        .first()
    )

    if team:
        return team

    return None


# -------------------------
# User search
# -------------------------

@app.get("/users/search", response_model=list[UserResponse])
def search_users(
    q: str = "",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = q.strip()

    if not query:
        return []

    users = (
        db.query(models.User)
        .filter(
            (models.User.username.ilike(f"%{query}%"))
            | (models.User.email.ilike(f"%{query}%"))
        )
        .filter(models.User.id != current_user.id)
        .order_by(models.User.username)
        .limit(10)
        .all()
    )

    return users


# -------------------------
# Teams
# -------------------------

@app.post(
    "/teams",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_team(
    team_data: TeamCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_team = models.Team(
        name=team_data.name.strip(),
        description=team_data.description,
        owner_id=current_user.id,
    )

    db.add(new_team)
    db.flush()

    owner_membership = models.TeamMember(
        team_id=new_team.id,
        user_id=current_user.id,
        role="admin",
    )

    db.add(owner_membership)
    db.commit()
    db.refresh(new_team)

    return new_team


@app.get(
    "/teams",
    response_model=list[TeamResponse],
)
def get_teams(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    teams = (
        db.query(models.Team)
        .outerjoin(
            models.TeamMember,
            models.TeamMember.team_id == models.Team.id,
        )
        .filter(
            (models.Team.owner_id == current_user.id)
            | (models.TeamMember.user_id == current_user.id)
        )
        .distinct()
        .all()
    )

    return teams


@app.get(
    "/teams/{team_id}",
    response_model=TeamResponse,
)
def get_team(
    team_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = (
        db.query(models.Team)
        .outerjoin(
            models.TeamMember,
            models.TeamMember.team_id == models.Team.id,
        )
        .filter(
            models.Team.id == team_id,
            (
                (models.Team.owner_id == current_user.id)
                | (models.TeamMember.user_id == current_user.id)
            ),
        )
        .first()
    )

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    return team


@app.put(
    "/teams/{team_id}",
    response_model=TeamResponse,
)
def update_team(
    team_id: int,
    team_data: TeamCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = (
        db.query(models.Team)
        .filter(
            models.Team.id == team_id,
            models.Team.owner_id == current_user.id,
        )
        .first()
    )

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found or you are not the team owner",
        )

    team.name = team_data.name.strip()
    team.description = team_data.description

    db.commit()
    db.refresh(team)

    return team


@app.delete(
    "/teams/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_team(
    team_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = (
        db.query(models.Team)
        .filter(
            models.Team.id == team_id,
            models.Team.owner_id == current_user.id,
        )
        .first()
    )

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found or you are not the team owner",
        )

    db.delete(team)
    db.commit()

    return None


# -------------------------
# Team members
# -------------------------

@app.post(
    "/teams/{team_id}/members",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_team_member(
    team_id: int,
    member_data: TeamMemberCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = (
        db.query(models.Team)
        .filter(
            models.Team.id == team_id,
            models.Team.owner_id == current_user.id,
        )
        .first()
    )

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found or you are not the team owner",
        )

    user = (
        db.query(models.User)
        .filter(models.User.id == member_data.user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    existing_member = (
        db.query(models.TeamMember)
        .filter(
            models.TeamMember.team_id == team_id,
            models.TeamMember.user_id == member_data.user_id,
        )
        .first()
    )

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this team",
        )

    new_member = models.TeamMember(
        team_id=team_id,
        user_id=member_data.user_id,
        role=member_data.role,
    )

    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return {
        "id": new_member.id,
        "team_id": new_member.team_id,
        "user_id": new_member.user_id,
        "username": user.username,
        "email": user.email,
        "role": new_member.role,
        "joined_at": new_member.joined_at,
    }


@app.get(
    "/teams/{team_id}/members",
    response_model=list[TeamMemberResponse],
)
def get_team_members(
    team_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = (
        db.query(models.Team)
        .outerjoin(
            models.TeamMember,
            models.TeamMember.team_id == models.Team.id,
        )
        .filter(
            models.Team.id == team_id,
            (
                (models.Team.owner_id == current_user.id)
                | (models.TeamMember.user_id == current_user.id)
            ),
        )
        .first()
    )

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    members = (
        db.query(models.TeamMember, models.User)
        .join(
            models.User,
            models.User.id == models.TeamMember.user_id,
        )
        .filter(models.TeamMember.team_id == team_id)
        .all()
    )

    return [
        {
            "id": membership.id,
            "team_id": membership.team_id,
            "user_id": membership.user_id,
            "username": user.username,
            "email": user.email,
            "role": membership.role,
            "joined_at": membership.joined_at,
        }
        for membership, user in members
    ]


@app.delete(
    "/teams/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_team_member(
    team_id: int,
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = (
        db.query(models.Team)
        .filter(
            models.Team.id == team_id,
            models.Team.owner_id == current_user.id,
        )
        .first()
    )

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found or you are not the team owner",
        )

    if user_id == team.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The team owner cannot be removed",
        )

    member = (
        db.query(models.TeamMember)
        .filter(
            models.TeamMember.team_id == team_id,
            models.TeamMember.user_id == user_id,
        )
        .first()
    )

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team member not found",
        )

    db.delete(member)
    db.commit()

    return None


# -------------------------
# Project helpers
# -------------------------

def get_user_project(
    project_id: int,
    current_user: models.User,
    db: Session,
):
    project = (
        db.query(models.Project)
        .join(
            models.Team,
            models.Project.team_id == models.Team.id,
        )
        .outerjoin(
            models.TeamMember,
            models.TeamMember.team_id == models.Team.id,
        )
        .filter(
            models.Project.id == project_id,
            (
                (models.Project.owner_id == current_user.id)
                | (models.Team.owner_id == current_user.id)
                | (models.TeamMember.user_id == current_user.id)
            ),
        )
        .first()
    )

    return project


# -------------------------
# Projects
# -------------------------

@app.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    project_data: ProjectCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = get_user_team(
        project_data.team_id,
        current_user,
        db,
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )

    if (
        project_data.start_date
        and project_data.due_date
        and project_data.due_date < project_data.start_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Due date cannot be before start date",
        )

    new_project = models.Project(
        name=project_data.name.strip(),
        description=project_data.description,
        status=project_data.status,
        start_date=project_data.start_date,
        due_date=project_data.due_date,
        team_id=project_data.team_id,
        owner_id=current_user.id,
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


@app.get(
    "/projects",
    response_model=list[ProjectResponse],
)
def get_projects(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = (
        db.query(models.Project)
        .join(
            models.Team,
            models.Project.team_id == models.Team.id,
        )
        .outerjoin(
            models.TeamMember,
            models.TeamMember.team_id == models.Team.id,
        )
        .filter(
            (
                (models.Project.owner_id == current_user.id)
                | (models.Team.owner_id == current_user.id)
                | (models.TeamMember.user_id == current_user.id)
            )
        )
        .distinct()
        .all()
    )

    return projects


@app.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_user_project(
        project_id,
        current_user,
        db,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@app.put(
    "/projects/{project_id}",
    response_model=ProjectResponse,
)

@app.get(
    "/projects/{project_id}/overview",
    response_model=ProjectOverviewResponse,
)
def get_project_overview(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_user_project(project_id, current_user, db)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    tasks = (
        db.query(models.Task)
        .filter(models.Task.project_id == project_id)
        .all()
    )

    total_tasks = len(tasks)

    completed_tasks = sum(
        1 for task in tasks if task.status == "completed"
    )

    todo_tasks = sum(
        1 for task in tasks if task.status == "todo"
    )

    in_progress_tasks = sum(
        1 for task in tasks if task.status == "in_progress"
    )

    in_review_tasks = sum(
        1 for task in tasks if task.status == "in_review"
    )

    today = date.today()

    overdue_tasks = sum(
        1
        for task in tasks
        if task.due_date is not None
        and task.due_date < today
        and task.status != "completed"
    )

    progress = (
        round((completed_tasks / total_tasks) * 100)
        if total_tasks > 0
        else 0
    )

    return ProjectOverviewResponse(
        project_id=project_id,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        todo_tasks=todo_tasks,
        in_progress_tasks=in_progress_tasks,
        in_review_tasks=in_review_tasks,
        overdue_tasks=overdue_tasks,
        progress=progress,
    )


def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_user_project(
        project_id,
        current_user,
        db,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    team = (
        db.query(models.Team)
        .filter(models.Team.id == project.team_id)
        .first()
    )

    if project.owner_id != current_user.id and (
        team is None or team.owner_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this project",
        )

    new_team_id = (
        project_data.team_id
        if project_data.team_id is not None
        else project.team_id
    )

    membership = get_user_team(
        new_team_id,
        current_user,
        db,
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of the target team",
        )

    new_start_date = (
        project_data.start_date
        if project_data.start_date is not None
        else project.start_date
    )

    new_due_date = (
        project_data.due_date
        if project_data.due_date is not None
        else project.due_date
    )

    if (
        new_start_date
        and new_due_date
        and new_due_date < new_start_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Due date cannot be before start date",
        )

    if project_data.name is not None:
        project.name = project_data.name.strip()

    if project_data.description is not None:
        project.description = project_data.description

    if project_data.status is not None:
        project.status = project_data.status

    if project_data.start_date is not None:
        project.start_date = project_data.start_date

    if project_data.due_date is not None:
        project.due_date = project_data.due_date

    if project_data.team_id is not None:
        project.team_id = project_data.team_id

    db.commit()
    db.refresh(project)

    return project


@app.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_project(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_user_project(
        project_id,
        current_user,
        db,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    team = (
        db.query(models.Team)
        .filter(models.Team.id == project.team_id)
        .first()
    )

    if project.owner_id != current_user.id and (
        team is None or team.owner_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this project",
        )

    db.delete(project)
    db.commit()

    return None


# -------------------------
# Task helpers
# -------------------------

ALLOWED_TASK_STATUSES = {
    "todo",
    "in_progress",
    "in_review",
    "completed",
}


def apply_task_status(
    task: models.Task,
    new_status: str,
    completion_note: str | None = None,
):
    if new_status not in ALLOWED_TASK_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task status",
        )

    task.status = new_status

    if new_status == "completed":
        if not task.completed:
            task.completed_at = datetime.now(timezone.utc)

        task.completed = True

        if completion_note is not None:
            task.completion_note = completion_note

    else:
        task.completed = False
        task.completed_at = None
        task.completion_note = None


def get_project_team_id(
    project_id: int,
    db: Session,
):
    project = (
        db.query(models.Project)
        .filter(models.Project.id == project_id)
        .first()
    )

    if project is None:
        return None

    return project.team_id


def validate_task_assignee(
    assignee_id: int,
    project_id: int | None,
    current_user: models.User,
    db: Session,
):
    assignee = (
        db.query(models.User)
        .filter(models.User.id == assignee_id)
        .first()
    )

    if assignee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignee user not found",
        )

    if project_id is None:
        if assignee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A task without a project can only be assigned to its owner",
            )

        return assignee

    team_id = get_project_team_id(
        project_id,
        db,
    )

    if team_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    team = (
        db.query(models.Team)
        .filter(models.Team.id == team_id)
        .first()
    )

    if team is not None and team.owner_id == assignee_id:
        return assignee

    membership = (
        db.query(models.TeamMember)
        .filter(
            models.TeamMember.team_id == team_id,
            models.TeamMember.user_id == assignee_id,
        )
        .first()
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignee must be a member of the project's team",
        )

    return assignee


# -------------------------
# Tasks
# -------------------------

@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    task: TaskCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if task.project_id is not None:
        project = get_user_project(
            task.project_id,
            current_user,
            db,
        )

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

    if task.assignee_id is not None:
        validate_task_assignee(
            task.assignee_id,
            task.project_id,
            current_user,
            db,
        )

    new_task = models.Task(
        title=task.title.strip(),
        description=task.description,
        due_date=task.due_date,
        priority=task.priority,
        category=task.category,
        status=task.status,
        completed=(task.status == "completed"),
        completed_at=(
            datetime.now(timezone.utc)
            if task.status == "completed"
            else None
        ),
        project_id=task.project_id,
        assignee_id=task.assignee_id,
        user_id=current_user.id,
    )

    db.add(new_task)
    db.flush()

    activity = models.Activity(
        action="task_created",
        description=f"{current_user.username} created task '{new_task.title}'",
        task_id=new_task.id,
        project_id=new_task.project_id,
        user_id=current_user.id,
    )

    db.add(activity)

    # Notify the assignee when a task is assigned to another user.
    if (
        new_task.assignee_id is not None
        and new_task.assignee_id != current_user.id
    ):
        create_notification(
            db,
            user_id=new_task.assignee_id,
            title="New task assigned",
            message=(
                f"{current_user.username} assigned you "
                f"the task '{new_task.title}'"
            ),
            notification_type="task_assigned",
            task_id=new_task.id,
            project_id=new_task.project_id,
        )


    db.commit()
    db.refresh(new_task)

    return new_task

@app.get(
    "/tasks",
    response_model=list[TaskResponse],
)
def get_tasks(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tasks = (
        db.query(models.Task)
        .outerjoin(
            models.Project,
            models.Task.project_id == models.Project.id,
        )
        .outerjoin(
            models.Team,
            models.Project.team_id == models.Team.id,
        )
        .outerjoin(
            models.TeamMember,
            models.TeamMember.team_id == models.Team.id,
        )
        .filter(
            (models.Task.user_id == current_user.id)
            | (models.Task.assignee_id == current_user.id)
            | (models.Project.owner_id == current_user.id)
            | (models.Team.owner_id == current_user.id)
            | (models.TeamMember.user_id == current_user.id)
        )
        .distinct()
        .all()
    )

    return tasks

@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = get_user_task(
        task_id,
        current_user,
        db,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task

@app.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = get_user_task(
        task_id,
        current_user,
        db,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    can_modify = task.user_id == current_user.id

    if not can_modify and task.project_id is not None:
        project = (
            db.query(models.Project)
            .filter(models.Project.id == task.project_id)
            .first()
        )

        if project is not None:
            if project.owner_id == current_user.id:
                can_modify = True
            else:
                team = (
                    db.query(models.Team)
                    .filter(models.Team.id == project.team_id)
                    .first()
                )

                if team is not None and team.owner_id == current_user.id:
                    can_modify = True

    if not can_modify and task.assignee_id == current_user.id:
        can_modify = True

    if not can_modify:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this task",
        )
    target_project_id = task.project_id

    if "project_id" in task_data.model_fields_set:
        target_project_id = task_data.project_id

    if "project_id" in task_data.model_fields_set:
        if task_data.project_id is not None:
            project = get_user_project(
                task_data.project_id,
                current_user,
                db,
            )

            if project is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found",
                )

        task.project_id = task_data.project_id

    if "assignee_id" in task_data.model_fields_set:
        if task_data.assignee_id is None:
            task.assignee_id = None

        else:
            validate_task_assignee(
                task_data.assignee_id,
                target_project_id,
                current_user,
                db,
            )

            task.assignee_id = task_data.assignee_id

    if task_data.title is not None:
        task.title = task_data.title.strip()

    if task_data.description is not None:
        task.description = task_data.description

    if "due_date" in task_data.model_fields_set:
        task.due_date = task_data.due_date

    if task_data.priority is not None:
        task.priority = task_data.priority

    if task_data.category is not None:
        task.category = task_data.category

    if task_data.status is not None:
        old_status = task.status

        apply_task_status(
            task,
            task_data.status,
            task_data.completion_note,
        )

        if old_status != task.status:
            activity = models.Activity(
                action="task_status_changed",
                description=(
                    f"{current_user.username} moved "
                    f"task '{task.title}' from {old_status} to {task.status}"
                ),
                task_id=task.id,
                project_id=task.project_id,
                user_id=current_user.id,
            )

            db.add(activity)
            
            # Notify the assigned user when the task status changes.
            # Do not notify the user who made the change.
            if (
                task.assignee_id is not None
                and task.assignee_id != current_user.id
            ):
                create_notification(
                    db,
                    user_id=task.assignee_id,
                    title="Task status updated",
                    message=(
                        f"{current_user.username} moved "
                        f"task '{task.title}' to {task.status}"
                    ),
                    notification_type="task_status_changed",
                    task_id=task.id,
                    project_id=task.project_id,
               )

    elif task_data.completed is not None:
        if task_data.completed:
            apply_task_status(
                task,
                "completed",
                task_data.completion_note,
            )
        else:
            apply_task_status(
                task,
                "todo",
            )

    elif task_data.completion_note is not None:
        task.completion_note = task_data.completion_note

    db.commit()
    db.refresh(task)

    return task


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = get_user_task(
        task_id,
        current_user,
        db,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    can_delete = task.user_id == current_user.id

    if not can_delete and task.project_id is not None:
        project = (
            db.query(models.Project)
            .filter(models.Project.id == task.project_id)
            .first()
        )

        if project is not None:
            if project.owner_id == current_user.id:
                can_delete = True
            else:
                team = (
                    db.query(models.Team)
                    .filter(models.Team.id == project.team_id)
                    .first()
                )

                if team is not None and team.owner_id == current_user.id:
                    can_delete = True

    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this task",
        )

    db.delete(task)
    db.commit()

    return None

# -------------------------
# Subtask helpers
# -------------------------

def get_user_task(
    task_id: int,
    current_user: models.User,
    db: Session,
):
    task = (
        db.query(models.Task)
        .filter(models.Task.id == task_id)
        .first()
    )

    if task is None:
        return None

    # Task owner always has access.
    if task.user_id == current_user.id:
        return task

    # Assigned user has access.
    if task.assignee_id == current_user.id:
        return task

    # If the task belongs to a project, project team members
    # can access the task.
    if task.project_id is not None:
        project = (
            db.query(models.Project)
            .filter(models.Project.id == task.project_id)
            .first()
        )

        if project is None:
            return None

        if project.owner_id == current_user.id:
            return task

        team = (
            db.query(models.Team)
            .filter(models.Team.id == project.team_id)
            .first()
        )

        if team is not None and team.owner_id == current_user.id:
            return task

        membership = (
            db.query(models.TeamMember)
            .filter(
                models.TeamMember.team_id == project.team_id,
                models.TeamMember.user_id == current_user.id,
            )
            .first()
        )

        if membership is not None:
            return task

    return None

def get_user_subtask(
    subtask_id: int,
    current_user: models.User,
    db: Session,
):
    return (
        db.query(models.Subtask)
        .join(
            models.Task,
            models.Subtask.task_id == models.Task.id,
        )
        .filter(
            models.Subtask.id == subtask_id,
            models.Task.user_id == current_user.id,
        )
        .first()
    )


# -------------------------
# Subtasks
# -------------------------

@app.post(
    "/tasks/{task_id}/subtasks",
    response_model=SubtaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subtask(
    task_id: int,
    subtask_data: SubtaskCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = get_user_task(
        task_id,
        current_user,
        db,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    new_subtask = models.Subtask(
        title=subtask_data.title.strip(),
        completed=False,
        task_id=task.id,
    )

    db.add(new_subtask)
    db.commit()
    db.refresh(new_subtask)

    return new_subtask


@app.get(
    "/tasks/{task_id}/subtasks",
    response_model=list[SubtaskResponse],
)
def get_subtasks(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = get_user_task(
        task_id,
        current_user,
        db,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return (
        db.query(models.Subtask)
        .filter(models.Subtask.task_id == task.id)
        .order_by(models.Subtask.created_at.asc())
        .all()
    )


@app.put(
    "/subtasks/{subtask_id}",
    response_model=SubtaskResponse,
)
def update_subtask(
    subtask_id: int,
    subtask_data: SubtaskUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subtask = get_user_subtask(
        subtask_id,
        current_user,
        db,
    )

    if subtask is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subtask not found",
        )

    if subtask_data.title is not None:
        subtask.title = subtask_data.title.strip()

    if subtask_data.completed is not None:
        subtask.completed = subtask_data.completed

    db.commit()
    db.refresh(subtask)

    return subtask


@app.delete(
    "/subtasks/{subtask_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_subtask(
    subtask_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subtask = get_user_subtask(
        subtask_id,
        current_user,
        db,
    )

    if subtask is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subtask not found",
        )

    db.delete(subtask)
    db.commit()

    return None


# -------------------------
# Task progress
# -------------------------

@app.get(
    "/tasks/{task_id}/progress",
    response_model=TaskProgressResponse,
)
def get_task_progress(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = get_user_task(
        task_id,
        current_user,
        db,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    total_subtasks = (
        db.query(models.Subtask)
        .filter(models.Subtask.task_id == task.id)
        .count()
    )

    completed_subtasks = (
        db.query(models.Subtask)
        .filter(
            models.Subtask.task_id == task.id,
            models.Subtask.completed.is_(True),
        )
        .count()
    )

    if total_subtasks == 0:
        progress = 0
    else:
        progress = round(
            (completed_subtasks / total_subtasks) * 100
        )

    return TaskProgressResponse(
        task_id=task.id,
        total_subtasks=total_subtasks,
        completed_subtasks=completed_subtasks,
        progress=progress,
    )


# =========================
# Comment endpoints
# =========================

@app.post(
    "/tasks/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    task_id: int,
    comment_data: CommentCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    task = get_user_task(task_id, current_user, db)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    comment = models.Comment(
        content=comment_data.content,
        task_id=task.id,
        user_id=current_user.id,
    )

    db.add(comment)
    db.flush()

    # Notify the task owner when another user comments.
    # Do not notify the commenter.
    if (
        task.user_id is not None
        and task.user_id != current_user.id
    ):
        create_notification(
            db,
            user_id=task.user_id,
            title="New comment",
            message=(
                f"{current_user.username} commented on "
                f"'{task.title}'"
            ),
            notification_type="comment_added",
            task_id=task.id,
            project_id=task.project_id,
        )

    db.commit()
    db.refresh(comment)

    return comment


@app.get(
    "/tasks/{task_id}/comments",
    response_model=list[CommentResponse],
)
def get_comments(
    task_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    task = get_user_task(task_id, current_user, db)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    return (
        db.query(models.Comment)
        .filter(models.Comment.task_id == task.id)
        .order_by(models.Comment.created_at.asc())
        .all()
    )


@app.put(
    "/comments/{comment_id}",
    response_model=CommentResponse,
)
def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    comment = (
        db.query(models.Comment)
        .filter(
            models.Comment.id == comment_id,
            models.Comment.user_id == current_user.id,
        )
        .first()
    )

    if comment is None:
        raise HTTPException(
            status_code=404,
            detail="Comment not found",
        )

    comment.content = comment_data.content

    db.commit()
    db.refresh(comment)

    return comment


@app.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_comment(
    comment_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    comment = (
        db.query(models.Comment)
        .filter(
            models.Comment.id == comment_id,
            models.Comment.user_id == current_user.id,
        )
        .first()
    )

    if comment is None:
        raise HTTPException(
            status_code=404,
            detail="Comment not found",
        )

    db.delete(comment)
    db.commit()

    return None

# =========================
# Activity endpoints
# =========================

@app.get(
    "/activities",
    response_model=list[ActivityResponse],
)
def get_activities(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    activities = (
        db.query(models.Activity)
        .filter(models.Activity.user_id == current_user.id)
        .order_by(models.Activity.created_at.desc())
        .all()
    )

    return activities

# =========================
# Notification endpoints
# =========================

@app.get(
    "/notifications",
    response_model=list[NotificationResponse],
)
def get_notifications(
    unread_only: bool = False,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    query = (
        db.query(models.Notification)
        .filter(
            models.Notification.user_id == current_user.id
        )
    )

    if unread_only:
        query = query.filter(
            models.Notification.is_read.is_(False)
        )

    notifications = (
        query
        .order_by(models.Notification.created_at.desc())
        .all()
    )

    return notifications


@app.get(
    "/notifications/unread-count",
)
def get_unread_notification_count(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    count = (
        db.query(models.Notification)
        .filter(
            models.Notification.user_id == current_user.id,
            models.Notification.is_read.is_(False),
        )
        .count()
    )

    return {
        "count": count,
    }


@app.patch(
    "/notifications/{notification_id}",
    response_model=NotificationResponse,
)
def update_notification(
    notification_id: int,
    notification_data: NotificationReadUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    notification = (
        db.query(models.Notification)
        .filter(
            models.Notification.id == notification_id,
            models.Notification.user_id == current_user.id,
        )
        .first()
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    notification.is_read = notification_data.is_read

    db.commit()
    db.refresh(notification)

    return notification


@app.delete(
    "/notifications/{notification_id}",
)
def delete_notification(
    notification_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    notification = (
        db.query(models.Notification)
        .filter(
            models.Notification.id == notification_id,
            models.Notification.user_id == current_user.id,
        )
        .first()
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    db.delete(notification)
    db.commit()

    return {
        "message": "Notification deleted successfully",
    }

@app.get(
    "/projects/{project_id}/dashboard",
    response_model=ProjectDashboardResponse,
)
def get_project_dashboard(
    project_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_user_project(project_id, current_user, db)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = (
        db.query(models.Task)
        .filter(models.Task.project_id == project_id)
        .order_by(models.Task.created_at.desc())
        .all()
    )

    total_tasks = len(tasks)

    completed_tasks = sum(
        1 for task in tasks if task.status == "completed"
    )

    todo_tasks = sum(
        1 for task in tasks if task.status == "todo"
    )

    in_progress_tasks = sum(
        1 for task in tasks if task.status == "in_progress"
    )

    in_review_tasks = sum(
        1 for task in tasks if task.status == "in_review"
    )

    today = date.today()

    overdue_tasks = sum(
        1
        for task in tasks
        if task.due_date is not None
        and task.due_date < today
        and task.status != "completed"
    )

    progress = (
        round((completed_tasks / total_tasks) * 100)
        if total_tasks > 0
        else 0
    )

    task_ids = [task.id for task in tasks]

    total_comments = 0
    total_subtasks = 0

    if task_ids:
        total_comments = (
            db.query(models.Comment)
            .filter(models.Comment.task_id.in_(task_ids))
            .count()
        )

        total_subtasks = (
            db.query(models.Subtask)
            .filter(models.Subtask.task_id.in_(task_ids))
            .count()
        )

    recent_activity = (
        db.query(models.Activity)
        .filter(models.Activity.project_id == project_id)
        .order_by(models.Activity.created_at.desc())
        .limit(10)
        .all()
    )

    return ProjectDashboardResponse(
        project_id=project.id,
        project_name=project.name,
        project_status=project.status,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        todo_tasks=todo_tasks,
        in_progress_tasks=in_progress_tasks,
        in_review_tasks=in_review_tasks,
        overdue_tasks=overdue_tasks,
        progress=progress,
        total_comments=total_comments,
        total_subtasks=total_subtasks,
        recent_tasks=tasks[:10],
        recent_activity=recent_activity,
    )






