import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base, get_db
from src.main import app
from src import models


@pytest.fixture
def client(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'test.db'}"

    test_engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def manager_token(client):
    register_response = client.post(
        "/register",
        json={
            "username": "manager",
            "email": "manager@example.com",
            "password": "ManagerTest2026!",
        },
    )
    assert register_response.status_code == 201

    db = models
    from src.database import get_db

    # The test API intentionally does not allow self-assigned manager roles.
    # Promote the test-only manager directly in the isolated test database.
    original_override = app.dependency_overrides[get_db]
    test_db = next(original_override())
    try:
        manager_user = test_db.query(models.User).filter(
            models.User.username == "manager"
        ).first()
        manager_user.role = "manager"
        test_db.commit()
    finally:
        test_db.close()

    login_response = client.post(
        "/login",
        json={
            "username": "manager",
            "password": "ManagerTest2026!",
        },
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]

def register_user(
    client,
    username="testuser",
    email="testuser@example.com",
):
    return client.post(
        "/register",
        json={
            "username": username,
            "email": email,
            "password": "testpassword123",
        },
    )


def login_user(client, username="testuser"):
    return client.post(
        "/login",
        json={
            "username": username,
            "password": "testpassword123",
        },
    )


# -------------------------
# Basic / authentication tests
# -------------------------

def test_root(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "TaskFlow API is running"


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user(client):
    response = register_user(client)

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert "password" not in data
    assert "password_hash" not in data


def test_duplicate_registration(client):
    register_user(client)

    response = register_user(client)

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Username or email already registered"
    )


def test_login(client):
    register_user(client)

    response = login_user(client)

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_invalid_login(client):
    register_user(client)

    response = client.post(
        "/login",
        json={
            "username": "testuser",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid username or password"
    )


def test_me_requires_authentication(client):
    response = client.get("/me")

    assert response.status_code == 401


def test_get_current_user(client):
    register_user(client)

    login_response = login_user(client)
    token = login_response.json()["access_token"]

    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"


# -------------------------
# Task tests
# -------------------------

def test_create_task(client):
    register_user(client)

    token = login_user(client).json()["access_token"]

    response = client.post(
        "/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Learn FastAPI",
            "description": "Build a REST API project",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Learn FastAPI"
    assert data["description"] == "Build a REST API project"
    assert data["completed"] is False
    assert data["user_id"] == 1


def test_get_tasks(client):
    register_user(client)

    token = login_user(client).json()["access_token"]

    client.post(
        "/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Task One",
            "description": "First task",
        },
    )

    client.post(
        "/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Task Two",
            "description": "Second task",
        },
    )

    response = client.get(
        "/tasks",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    tasks = response.json()

    assert len(tasks) == 2
    assert tasks[0]["title"] == "Task One"
    assert tasks[1]["title"] == "Task Two"


def test_update_task(client):
    register_user(client)

    token = login_user(client).json()["access_token"]

    create_response = client.post(
        "/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Old Title",
            "description": "Old description",
        },
    )

    task_id = create_response.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated Title",
            "completed": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated Title"
    assert data["completed"] is True


def test_delete_task(client):
    register_user(client)

    token = login_user(client).json()["access_token"]

    create_response = client.post(
        "/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Delete Me",
            "description": "This task will be deleted",
        },
    )

    task_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert get_response.status_code == 404


def test_task_not_found(client):
    register_user(client)

    token = login_user(client).json()["access_token"]

    response = client.get(
        "/tasks/999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_invalid_task_data(client):
    register_user(client)

    token = login_user(client).json()["access_token"]

    response = client.post(
        "/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "",
            "description": "Invalid task",
        },
    )

    assert response.status_code == 422


# -------------------------
# Subtask tests
# -------------------------

def create_test_task(client):
    register_user(client)

    token = login_user(client).json()["access_token"]

    response = client.post(
        "/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Parent Task",
            "description": "Task with subtasks",
        },
    )

    assert response.status_code == 201

    return token, response.json()["id"]


def test_create_subtask(client):
    token, task_id = create_test_task(client)

    response = client.post(
        f"/tasks/{task_id}/subtasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Build authentication API",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Build authentication API"
    assert data["completed"] is False
    assert data["task_id"] == task_id
    assert "id" in data


def test_get_subtasks(client):
    token, task_id = create_test_task(client)

    client.post(
        f"/tasks/{task_id}/subtasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "First subtask",
        },
    )

    client.post(
        f"/tasks/{task_id}/subtasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Second subtask",
        },
    )

    response = client.get(
        f"/tasks/{task_id}/subtasks",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    subtasks = response.json()

    assert len(subtasks) == 2
    assert subtasks[0]["title"] == "First subtask"
    assert subtasks[1]["title"] == "Second subtask"
    assert subtasks[0]["completed"] is False
    assert subtasks[1]["completed"] is False


def test_update_subtask(client):
    token, task_id = create_test_task(client)

    create_response = client.post(
        f"/tasks/{task_id}/subtasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Original subtask",
        },
    )

    subtask_id = create_response.json()["id"]

    response = client.put(
        f"/subtasks/{subtask_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated subtask",
            "completed": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated subtask"
    assert data["completed"] is True
    assert data["task_id"] == task_id


def test_delete_subtask(client):
    token, task_id = create_test_task(client)

    create_response = client.post(
        f"/tasks/{task_id}/subtasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Delete this subtask",
        },
    )

    subtask_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/subtasks/{subtask_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/tasks/{task_id}/subtasks",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert get_response.status_code == 200
    assert get_response.json() == []


def test_task_progress(client):
    token, task_id = create_test_task(client)

    first_response = client.post(
        f"/tasks/{task_id}/subtasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Completed subtask",
        },
    )

    first_subtask_id = first_response.json()["id"]

    client.post(
        f"/tasks/{task_id}/subtasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Pending subtask",
        },
    )

    client.post(
        f"/tasks/{task_id}/subtasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Another pending subtask",
        },
    )

    client.put(
        f"/subtasks/{first_subtask_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "completed": True,
        },
    )

    response = client.get(
        f"/tasks/{task_id}/progress",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["task_id"] == task_id
    assert data["total_subtasks"] == 3
    assert data["completed_subtasks"] == 1
    assert data["progress"] == 33


def test_task_progress_with_no_subtasks(client):
    token, task_id = create_test_task(client)

    response = client.get(
        f"/tasks/{task_id}/progress",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["task_id"] == task_id
    assert data["total_subtasks"] == 0
    assert data["completed_subtasks"] == 0
    assert data["progress"] == 0


def test_subtask_requires_task_owner(client):
    register_user(
        client,
        username="owner",
        email="owner@example.com",
    )

    owner_token = login_user(
        client,
        username="owner",
    ).json()["access_token"]

    task_response = client.post(
        "/tasks",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "title": "Private task",
        },
    )

    task_id = task_response.json()["id"]

    register_user(
        client,
        username="otheruser",
        email="other@example.com",
    )

    other_token = login_user(
        client,
        username="otheruser",
    ).json()["access_token"]

    response = client.post(
        f"/tasks/{task_id}/subtasks",
        headers={"Authorization": f"Bearer {other_token}"},
        json={
            "title": "Unauthorized subtask",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# =========================
# Comment tests
# =========================

def test_create_comment(client):
    token, task_id = create_test_task(client)

    response = client.post(
        f"/tasks/{task_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content": "Authentication API is ready for review.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["content"] == "Authentication API is ready for review."
    assert data["task_id"] == task_id
    assert data["user_id"] == 1
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_get_comments(client):
    token, task_id = create_test_task(client)

    first_response = client.post(
        f"/tasks/{task_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content": "First comment",
        },
    )

    second_response = client.post(
        f"/tasks/{task_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content": "Second comment",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get(
        f"/tasks/{task_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["content"] == "First comment"
    assert data[1]["content"] == "Second comment"
    assert data[0]["task_id"] == task_id
    assert data[1]["task_id"] == task_id


def test_update_comment(client):
    token, task_id = create_test_task(client)

    create_response = client.post(
        f"/tasks/{task_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content": "Original comment",
        },
    )

    assert create_response.status_code == 201

    comment_id = create_response.json()["id"]

    response = client.put(
        f"/comments/{comment_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content": "Updated comment",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == comment_id
    assert data["content"] == "Updated comment"
    assert data["task_id"] == task_id
    assert data["user_id"] == 1


def test_delete_comment(client):
    token, task_id = create_test_task(client)

    create_response = client.post(
        f"/tasks/{task_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content": "Comment to delete",
        },
    )

    assert create_response.status_code == 201

    comment_id = create_response.json()["id"]

    response = client.delete(
        f"/comments/{comment_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/tasks/{task_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert get_response.status_code == 200
    assert get_response.json() == []


def test_comment_requires_authentication(client):
    response = client.post(
        "/tasks/1/comments",
        json={
            "content": "Unauthenticated comment",
        },
    )

    assert response.status_code == 401


def test_get_comments_requires_authentication(client):
    response = client.get("/tasks/1/comments")

    assert response.status_code == 401


def test_comment_invalid_task(client):
    register_user(client)

    token = login_user(client).json()["access_token"]

    response = client.post(
        "/tasks/9999/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content": "This task does not exist",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_comment_empty_content(client):
    token, task_id = create_test_task(client)

    response = client.post(
        f"/tasks/{task_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content": "",
        },
    )

    assert response.status_code == 422


def test_update_nonexistent_comment(client):
    register_user(client)

    token = login_user(client).json()["access_token"]

    response = client.put(
        "/comments/9999",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content": "Updated comment",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Comment not found"


def test_delete_nonexistent_comment(client):
    register_user(client)

    token = login_user(client).json()["access_token"]

    response = client.delete(
        "/comments/9999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Comment not found"

# =========================
# Activity tests
# =========================

def test_task_creation_creates_activity(client):
    token, task_id = create_test_task(client)

    response = client.get(
        "/activities",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["action"] == "task_created"
    assert data[0]["task_id"] == task_id
    assert data[0]["project_id"] is None
    assert data[0]["user_id"] == 1
    assert "created task" in data[0]["description"]
    assert "created_at" in data[0]

def test_task_status_change_creates_activity(client):
    token, task_id = create_test_task(client)

    update_response = client.put(
        f"/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "in_progress"},
    )

    assert update_response.status_code == 200

    response = client.get(
        "/activities",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    # Latest activity should be the status change
    assert data[0]["action"] == "task_status_changed"
    assert data[0]["task_id"] == task_id
    assert data[0]["user_id"] == 1
    assert "in_progress" in data[0]["description"]

    # Original task creation activity
    assert data[1]["action"] == "task_created"
    assert data[1]["task_id"] == task_id


def test_task_assignment_creates_notification(client):
    token, _ = create_test_task(client)

    # Register a second user who will receive the notification.
    register_response = client.post(
        "/register",
        json={
            "username": "alex",
            "email": "alex@example.com",
            "password": "AlexTest2026!",
        },
    )

    assert register_response.status_code == 201

    # Login as Alex.
    login_response = client.post(
        "/login",
        json={
            "username": "alex",
            "password": "AlexTest2026!",
        },
    )

    assert login_response.status_code == 200

    alex_token = login_response.json()["access_token"]

    # Get Alex's user ID.
    me_response = client.get(
        "/me",
        headers={
            "Authorization": f"Bearer {alex_token}",
        },
    )

    assert me_response.status_code == 200

    alex_id = me_response.json()["id"]

    # Create a team.
    team_response = client.post(
        "/teams",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Team Cyberpunk",
            "description": "TaskFlow project workspace",
        },
    )

    assert team_response.status_code == 201

    team_id = team_response.json()["id"]

    # Add Alex to the team.
    member_response = client.post(
        f"/teams/{team_id}/members",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "user_id": alex_id,
            "role": "member",
        },
    )

    assert member_response.status_code == 201

    # Verify team members include user details.
    members_response = client.get(
        f"/teams/{team_id}/members",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert members_response.status_code == 200

    members = members_response.json()

    alex_member = next(
        member for member in members
        if member["user_id"] == alex_id
    )

    assert alex_member["username"] == "alex"
    assert alex_member["email"] == "alex@example.com"
    assert alex_member["role"] == "member"

    # Create a project inside the team.
    project_response = client.post(
        "/projects",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Notification Project",
            "description": "Project used for notification testing",
            "status": "active",
            "team_id": team_id,
        },
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    # Create a task inside the project and assign it to Alex.
    task_response = client.post(
        "/tasks",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "title": "Assigned task",
            "description": "Task assigned to Alex",
            "project_id": project_id,
            "assignee_id": alex_id,
        },
    )

    assert task_response.status_code == 201

    task_data = task_response.json()

    assert task_data["assignee_id"] == alex_id
    assert task_data["project_id"] == project_id

    # Check Alex's notifications.
    notifications_response = client.get(
        "/notifications",
        headers={
            "Authorization": f"Bearer {alex_token}",
        },
    )

    assert notifications_response.status_code == 200

    notifications = notifications_response.json()

    assert len(notifications) == 1

    notification = notifications[0]

    assert notification["title"] == "New task assigned"
    assert notification["notification_type"] == "task_assigned"
    assert notification["user_id"] == alex_id
    assert notification["task_id"] == task_data["id"]
    assert notification["project_id"] == project_id
    assert notification["is_read"] is False
    assert "Assigned task" in notification["message"]

def test_task_status_change_creates_notification_for_assignee(client):
    token, _ = create_test_task(client)

    # Register Alex.
    register_response = client.post(
        "/register",
        json={
            "username": "alex",
            "email": "alex@example.com",
            "password": "AlexTest2026!",
        },
    )

    assert register_response.status_code == 201

    # Login as Alex.
    login_response = client.post(
        "/login",
        json={
            "username": "alex",
            "password": "AlexTest2026!",
        },
    )

    assert login_response.status_code == 200

    alex_token = login_response.json()["access_token"]

    # Get Alex's ID.
    me_response = client.get(
        "/me",
        headers={
            "Authorization": f"Bearer {alex_token}",
        },
    )

    assert me_response.status_code == 200

    alex_id = me_response.json()["id"]

    # Create a team.
    team_response = client.post(
        "/teams",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Cyberpunk Team",
            "description": "Notification test team",
        },
    )

    assert team_response.status_code == 201

    team_id = team_response.json()["id"]

    # Add Alex to the team.
    member_response = client.post(
        f"/teams/{team_id}/members",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "user_id": alex_id,
            "role": "member",
        },
    )

    assert member_response.status_code == 201

    # Create a project.
    project_response = client.post(
        "/projects",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Status Notification Project",
            "description": "Testing status notifications",
            "status": "active",
            "team_id": team_id,
        },
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    # Create a task assigned to Alex.
    task_response = client.post(
        "/tasks",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "title": "Status notification task",
            "description": "Testing status changes",
            "project_id": project_id,
            "assignee_id": alex_id,
        },
    )

    assert task_response.status_code == 201

    task_id = task_response.json()["id"]

    # The assignment notification should already exist.
    notifications_response = client.get(
        "/notifications",
        headers={
            "Authorization": f"Bearer {alex_token}",
        },
    )

    assert notifications_response.status_code == 200

    notifications = notifications_response.json()

    assert len(notifications) == 1
    assert notifications[0]["notification_type"] == "task_assigned"

    # Change the task status as the owner.
    update_response = client.put(
        f"/tasks/{task_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "status": "in_progress",
        },
    )

    assert update_response.status_code == 200

    assert update_response.json()["status"] == "in_progress"

    # Alex should now have two notifications.
    notifications_response = client.get(
        "/notifications",
        headers={
            "Authorization": f"Bearer {alex_token}",
        },
    )

    assert notifications_response.status_code == 200

    notifications = notifications_response.json()

    assert len(notifications) == 2

    status_notification = notifications[0]

    assert status_notification["title"] == "Task status updated"
    assert status_notification["notification_type"] == "task_status_changed"
    assert status_notification["user_id"] == alex_id
    assert status_notification["task_id"] == task_id
    assert status_notification["project_id"] == project_id
    assert status_notification["is_read"] is False
    assert "in_progress" in status_notification["message"]

    assignment_notification = notifications[1]

    assert assignment_notification["notification_type"] == "task_assigned"
    assert assignment_notification["task_id"] == task_id


def test_comment_creates_notification_for_assignee(client):
    token, _ = create_test_task(client)

    # Register Alex.
    register_response = client.post(
        "/register",
        json={
            "username": "alex",
            "email": "alex@example.com",
            "password": "AlexTest2026!",
        },
    )

    assert register_response.status_code == 201

    # Login as Alex.
    login_response = client.post(
        "/login",
        json={
            "username": "alex",
            "password": "AlexTest2026!",
        },
    )

    assert login_response.status_code == 200

    alex_token = login_response.json()["access_token"]

    # Get Alex's ID.
    me_response = client.get(
        "/me",
        headers={
            "Authorization": f"Bearer {alex_token}",
        },
    )

    assert me_response.status_code == 200

    alex_id = me_response.json()["id"]

    # Create a team.
    team_response = client.post(
        "/teams",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Comment Team",
            "description": "Comment notification test team",
        },
    )

    assert team_response.status_code == 201

    team_id = team_response.json()["id"]

    # Add Alex to the team.
    member_response = client.post(
        f"/teams/{team_id}/members",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "user_id": alex_id,
            "role": "member",
        },
    )

    assert member_response.status_code == 201

    # Create a project.
    project_response = client.post(
        "/projects",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Comment Notification Project",
            "description": "Testing comment notifications",
            "status": "active",
            "team_id": team_id,
        },
    )

    assert project_response.status_code == 201

    project_id = project_response.json()["id"]

    # Create a task assigned to Alex.
    task_response = client.post(
        "/tasks",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "title": "Comment notification task",
            "description": "Testing comment notifications",
            "project_id": project_id,
            "assignee_id": alex_id,
        },
    )

    assert task_response.status_code == 201

    task_id = task_response.json()["id"]

    # Alex should initially have one assignment notification.
    notifications_response = client.get(
        "/notifications",
        headers={
            "Authorization": f"Bearer {alex_token}",
        },
    )

    assert notifications_response.status_code == 200

    notifications = notifications_response.json()

    assert len(notifications) == 1
    assert notifications[0]["notification_type"] == "task_assigned"

    # Alex comments on the task.
    comment_response = client.post(
        f"/tasks/{task_id}/comments",
        headers={
            "Authorization": f"Bearer {alex_token}",
        },
        json={
            "content": "I have started working on this task.",
        },
    )

    assert comment_response.status_code == 201

    comment_data = comment_response.json()

    assert comment_data["task_id"] == task_id
    assert comment_data["user_id"] == alex_id
    assert comment_data["content"] == (
        "I have started working on this task."
    )

    # Ganesh owns the task, so he should receive a notification
    # when Alex comments on it.
    notifications_response = client.get(
        "/notifications",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert notifications_response.status_code == 200

    ganesh_notifications = notifications_response.json()

    assert len(ganesh_notifications) == 1

    ganesh_notification = ganesh_notifications[0]

    assert ganesh_notification["title"] == "New comment"
    assert ganesh_notification["notification_type"] == "comment_added"
    assert ganesh_notification["user_id"] == 1
    assert ganesh_notification["task_id"] == task_id
    assert ganesh_notification["project_id"] == project_id
    assert ganesh_notification["is_read"] is False
    assert "alex" in ganesh_notification["message"]
    assert "Comment notification task" in ganesh_notification["message"]

    # Alex should NOT receive a notification for his own comment.
    notifications_response = client.get(
        "/notifications",
        headers={
            "Authorization": f"Bearer {alex_token}",
        },
    )

    assert notifications_response.status_code == 200

    alex_notifications = notifications_response.json()

    assert len(alex_notifications) == 1
    assert alex_notifications[0]["notification_type"] == "task_assigned"


def test_project_overview_returns_real_task_statistics(client):
    token, _ = create_test_task(client)

    headers = {"Authorization": f"Bearer {token}"}

    # Create a team owned by the test user.
    team_response = client.post(
        "/teams",
        headers=headers,
        json={
            "name": "Overview Test Team",
            "description": "Testing project overview",
        },
    )

    assert team_response.status_code == 201
    team_id = team_response.json()["id"]

    # Create a project.
    project_response = client.post(
        "/projects",
        headers=headers,
        json={
            "name": "Overview Test Project",
            "description": "Testing project statistics",
            "status": "active",
            "team_id": team_id,
        },
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # Create TODO task.
    todo_response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Todo task",
            "project_id": project_id,
            "status": "todo",
        },
    )
    assert todo_response.status_code == 201

    # Create IN PROGRESS task.
    progress_response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Progress task",
            "project_id": project_id,
            "status": "in_progress",
        },
    )
    assert progress_response.status_code == 201

    # Create IN REVIEW task.
    review_response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Review task",
            "project_id": project_id,
            "status": "in_review",
        },
    )
    assert review_response.status_code == 201

    # Create COMPLETED task.
    completed_response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Completed task",
            "project_id": project_id,
            "status": "completed",
        },
    )
    assert completed_response.status_code == 201

    # Get project overview.
    overview_response = client.get(
        f"/projects/{project_id}/overview",
        headers=headers,
    )

    assert overview_response.status_code == 200

    data = overview_response.json()

    assert data["project_id"] == project_id
    assert data["total_tasks"] == 4
    assert data["completed_tasks"] == 1
    assert data["todo_tasks"] == 1
    assert data["in_progress_tasks"] == 1
    assert data["in_review_tasks"] == 1
    assert data["overdue_tasks"] == 0
    assert data["progress"] == 25


def test_assignee_can_update_but_cannot_delete_task(client):
    token, _ = create_test_task(client)

    # Register Alex.
    register_response = client.post(
        "/register",
        json={
            "username": "alex",
            "email": "alex@example.com",
            "password": "AlexTest2026!",
        },
    )
    assert register_response.status_code == 201

    # Login Alex.
    alex_login_response = client.post(
        "/login",
        json={
            "username": "alex",
            "password": "AlexTest2026!",
        },
    )
    assert alex_login_response.status_code == 200

    alex_token = alex_login_response.json()["access_token"]
    alex_headers = {"Authorization": f"Bearer {alex_token}"}

    # Create a team.
    team_response = client.post(
        "/teams",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Assignee Authorization Team",
            "description": "Testing assignee permissions",
        },
    )
    assert team_response.status_code == 201
    team_id = team_response.json()["id"]

    # Add Alex to the team.
    member_response = client.post(
        f"/teams/{team_id}/members",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": 2, "role": "member"},
    )
    assert member_response.status_code == 201

    # Create a project.
    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Assignee Authorization Project",
            "description": "Testing assignee permissions",
            "status": "active",
            "team_id": team_id,
        },
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # Create a task assigned to Alex.
    task_response = client.post(
        "/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Assignee Authorization Task",
            "description": "Testing assignee access",
            "project_id": project_id,
            "assignee_id": 2,
        },
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    # Alex can update the task because he is the assignee.
    update_response = client.put(
        f"/tasks/{task_id}",
        headers=alex_headers,
        json={
            "title": "Updated by Alex",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated by Alex"

    # Alex cannot delete the task because he is only the assignee.
    delete_response = client.delete(
        f"/tasks/{task_id}",
        headers=alex_headers,
    )
    assert delete_response.status_code == 403


def test_team_member_can_view_but_cannot_modify_task(client):
    token, _ = create_test_task(client)

    # Register Alex.
    register_response = client.post(
        "/register",
        json={
            "username": "alex",
            "email": "alex@example.com",
            "password": "AlexTest2026!",
        },
    )
    assert register_response.status_code == 201

    # Login Alex.
    alex_login_response = client.post(
        "/login",
        json={
            "username": "alex",
            "password": "AlexTest2026!",
        },
    )
    assert alex_login_response.status_code == 200

    alex_token = alex_login_response.json()["access_token"]
    alex_headers = {"Authorization": f"Bearer {alex_token}"}

    # Create a team.
    team_response = client.post(
        "/teams",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Member Authorization Team",
            "description": "Testing team member permissions",
        },
    )
    assert team_response.status_code == 201
    team_id = team_response.json()["id"]

    # Add Alex as a regular team member.
    member_response = client.post(
        f"/teams/{team_id}/members",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": 2, "role": "member"},
    )
    assert member_response.status_code == 201

    # Create a project in the team.
    project_response = client.post(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Member Authorization Project",
            "description": "Testing team member permissions",
            "status": "active",
            "team_id": team_id,
        },
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # Create a task owned by Ganesh.
    task_response = client.post(
        "/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Member Authorization Task",
            "description": "Testing team member access",
            "project_id": project_id,
        },
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]

    # Alex can view the task because he is a team member.
    get_response = client.get(
        f"/tasks/{task_id}",
        headers=alex_headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == task_id

    # Alex cannot modify the task.
    update_response = client.put(
        f"/tasks/{task_id}",
        headers=alex_headers,
        json={
            "title": "Alex should not be able to change this",
        },
    )
    assert update_response.status_code == 403

    # Alex cannot delete the task.
    delete_response = client.delete(
        f"/tasks/{task_id}",
        headers=alex_headers,
    )
    assert delete_response.status_code == 403



def test_project_dashboard_returns_real_project_data(client):
    token, _ = create_test_task(client)

    headers = {"Authorization": f"Bearer {token}"}

    team_response = client.post(
        "/teams",
        headers=headers,
        json={
            "name": "Dashboard Test Team",
            "description": "Testing dashboard",
        },
    )

    assert team_response.status_code == 201
    team_id = team_response.json()["id"]

    project_response = client.post(
        "/projects",
        headers=headers,
        json={
            "name": "Dashboard Test Project",
            "description": "Testing dashboard data",
            "status": "active",
            "team_id": team_id,
        },
    )

    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # Create tasks in different states.
    for title, task_status in [
        ("Todo task", "todo"),
        ("Progress task", "in_progress"),
        ("Review task", "in_review"),
        ("Completed task", "completed"),
    ]:
        response = client.post(
            "/tasks",
            headers=headers,
            json={
                "title": title,
                "project_id": project_id,
                "status": task_status,
            },
        )
        assert response.status_code == 201

    dashboard_response = client.get(
        f"/projects/{project_id}/dashboard",
        headers=headers,
    )

    assert dashboard_response.status_code == 200

    data = dashboard_response.json()

    assert data["project_id"] == project_id
    assert data["project_name"] == "Dashboard Test Project"
    assert data["project_status"] == "active"

    assert data["total_tasks"] == 4
    assert data["completed_tasks"] == 1
    assert data["todo_tasks"] == 1
    assert data["in_progress_tasks"] == 1
    assert data["in_review_tasks"] == 1

    assert data["overdue_tasks"] == 0
    assert data["progress"] == 25

    assert data["total_comments"] == 0
    assert data["total_subtasks"] == 0

    assert len(data["recent_tasks"]) == 4






    
def test_manager_can_add_and_remove_team_member(client):
    token, _ = create_test_task(client)
    headers = {"Authorization": f"Bearer {token}"}

    team_response = client.post(
        "/teams",
        headers=headers,
        json={
            "name": "Manager Authorization Team",
            "description": "Testing manager team permissions",
        },
    )
    assert team_response.status_code == 201
    team_id = team_response.json()["id"]

    register_response = client.post(
        "/register",
        json={
            "username": "alex",
            "email": "alex@example.com",
            "password": "AlexTest2026!",
        },
    )
    assert register_response.status_code == 201

    add_response = client.post(
        f"/teams/{team_id}/members",
        headers=headers,
        json={"user_id": 2, "role": "member"},
    )
    assert add_response.status_code == 201

    remove_response = client.delete(
        f"/teams/{team_id}/members/2",
        headers=headers,
    )
    assert remove_response.status_code == 204


def test_regular_member_cannot_manage_team_members(client):
    token, _ = create_test_task(client)
    headers = {"Authorization": f"Bearer {token}"}

    team_response = client.post(
        "/teams",
        headers=headers,
        json={
            "name": "Member Management Authorization Team",
            "description": "Testing member restrictions",
        },
    )
    assert team_response.status_code == 201
    team_id = team_response.json()["id"]

    register_response = client.post(
        "/register",
        json={
            "username": "alex",
            "email": "alex@example.com",
            "password": "AlexTest2026!",
        },
    )
    assert register_response.status_code == 201

    add_response = client.post(
        f"/teams/{team_id}/members",
        headers=headers,
        json={"user_id": 2, "role": "member"},
    )
    assert add_response.status_code == 201

    alex_login_response = client.post(
        "/login",
        json={
            "username": "alex",
            "password": "AlexTest2026!",
        },
    )
    assert alex_login_response.status_code == 200

    alex_headers = {
        "Authorization": f"Bearer {alex_login_response.json()['access_token']}"
    }

    add_again_response = client.post(
        f"/teams/{team_id}/members",
        headers=alex_headers,
        json={"user_id": 1, "role": "member"},
    )
    assert add_again_response.status_code == 403

    remove_response = client.delete(
        f"/teams/{team_id}/members/1",
        headers=alex_headers,
    )
    assert remove_response.status_code == 403


def test_team_head_can_manage_team_members(client, manager_token):
    token = manager_token
    headers = {"Authorization": f"Bearer {token}"}

    team_response = client.post(
        "/teams",
        headers=headers,
        json={
            "name": "Team Head Authorization Team",
            "description": "Testing team head permissions",
        },
    )
    assert team_response.status_code == 201
    team_id = team_response.json()["id"]

    register_response = client.post(
        "/register",
        json={
            "username": "alex",
            "email": "alex@example.com",
            "password": "AlexTest2026!",
        },
    )
    assert register_response.status_code == 201

    add_head_response = client.post(
        f"/teams/{team_id}/members",
        headers=headers,
        json={"user_id": 2, "role": "team_head"},
    )
    assert add_head_response.status_code == 201

    alex_login_response = client.post(
        "/login",
        json={
            "username": "alex",
            "password": "AlexTest2026!",
        },
    )
    assert alex_login_response.status_code == 200

    alex_headers = {
        "Authorization": f"Bearer {alex_login_response.json()['access_token']}"
    }

    add_member_response = client.post(
        f"/teams/{team_id}/members",
        headers=alex_headers,
        json={"user_id": 1, "role": "member"},
    )

    # The team owner is already a member, so this should reach
    # authorization first and succeed past the permission check.
    assert add_member_response.status_code == 400


def test_team_owner_cannot_be_removed(client):
    token, _ = create_test_task(client)
    headers = {"Authorization": f"Bearer {token}"}

    team_response = client.post(
        "/teams",
        headers=headers,
        json={
            "name": "Owner Protection Team",
            "description": "Testing owner protection",
        },
    )
    assert team_response.status_code == 201
    team_id = team_response.json()["id"]

    remove_response = client.delete(
        f"/teams/{team_id}/members/1",
        headers=headers,
    )

    assert remove_response.status_code == 400
    assert remove_response.json()["detail"] == "The team owner cannot be removed"


def test_manager_can_edit_any_team(client):
    token, _ = create_test_task(client)

    from src.database import get_db

    original_override = app.dependency_overrides[get_db]
    test_db = next(original_override())
    try:
        test_user = (
            test_db.query(models.User)
            .filter(models.User.username == "testuser")
            .first()
        )
        test_user.role = "manager"
        test_db.commit()
    finally:
        test_db.close()

    manager_headers = {"Authorization": f"Bearer {token}"}

    # Create the first team.
    team_a = client.post(
        "/teams",
        headers=manager_headers,
        json={
            "name": "Team Alpha",
            "description": "Alpha team",
        },
    )
    assert team_a.status_code == 201

    # Create a second manager to become the owner of Team Beta.
    register_response = client.post(
        "/register",
        json={
            "username": "secondmanager",
            "email": "secondmanager@example.com",
            "password": "SecondManager2026!",
        },
    )
    assert register_response.status_code == 201

    from src.database import get_db

    original_override = app.dependency_overrides[get_db]
    test_db = next(original_override())
    try:
        second_manager = (
            test_db.query(models.User)
            .filter(models.User.username == "secondmanager")
            .first()
        )
        second_manager.role = "manager"
        test_db.commit()
    finally:
        test_db.close()

    second_login = client.post(
        "/login",
        json={
            "username": "secondmanager",
            "password": "SecondManager2026!",
        },
    )
    assert second_login.status_code == 200

    second_headers = {
        "Authorization": f"Bearer {second_login.json()['access_token']}"
    }

    # Second manager creates Team Beta.
    team_b = client.post(
        "/teams",
        headers=second_headers,
        json={
            "name": "Team Beta",
            "description": "Beta team",
        },
    )
    assert team_b.status_code == 201
    team_b_id = team_b.json()["id"]

    # First manager edits a team owned by another manager.
    update_response = client.put(
        f"/teams/{team_b_id}",
        headers=manager_headers,
        json={
            "name": "Team Beta Updated",
            "description": "Updated by company manager",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Team Beta Updated"
    assert update_response.json()["description"] == "Updated by company manager"


def test_regular_member_cannot_edit_team(client):
    token, _ = create_test_task(client)
    manager_headers = {"Authorization": f"Bearer {token}"}

    team_response = client.post(
        "/teams",
        headers=manager_headers,
        json={
            "name": "Protected Team",
            "description": "Protected team",
        },
    )
    assert team_response.status_code == 201
    team_id = team_response.json()["id"]

    register_response = client.post(
        "/register",
        json={
            "username": "alex",
            "email": "alex@example.com",
            "password": "AlexTest2026!",
        },
    )
    assert register_response.status_code == 201

    add_response = client.post(
        f"/teams/{team_id}/members",
        headers=manager_headers,
        json={"user_id": 2, "role": "member"},
    )
    assert add_response.status_code == 201

    alex_login = client.post(
        "/login",
        json={
            "username": "alex",
            "password": "AlexTest2026!",
        },
    )
    assert alex_login.status_code == 200

    alex_headers = {
        "Authorization": f"Bearer {alex_login.json()['access_token']}"
    }

    update_response = client.put(
        f"/teams/{team_id}",
        headers=alex_headers,
        json={
            "name": "Unauthorized Change",
            "description": "Should not be allowed",
        },
    )

    assert update_response.status_code == 403

def test_manager_can_delete_any_team(client):
    token, _ = create_test_task(client)

    from src.database import get_db

    original_override = app.dependency_overrides[get_db]
    test_db = next(original_override())
    try:
        test_user = (
            test_db.query(models.User)
            .filter(models.User.username == "testuser")
            .first()
        )
        test_user.role = "manager"
        test_db.commit()
    finally:
        test_db.close()

    manager_headers = {"Authorization": f"Bearer {token}"}

    team_response = client.post(
        "/teams",
        headers=manager_headers,
        json={
            "name": "Manager Delete Team",
            "description": "Team to be deleted by manager",
        },
    )
    assert team_response.status_code == 201
    team_id = team_response.json()["id"]

    delete_response = client.delete(
        f"/teams/{team_id}",
        headers=manager_headers,
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/teams/{team_id}",
        headers=manager_headers,
    )
    assert get_response.status_code == 404


def test_regular_member_cannot_delete_team(client):
    token, _ = create_test_task(client)

    from src.database import get_db

    original_override = app.dependency_overrides[get_db]
    test_db = next(original_override())
    try:
        test_user = (
            test_db.query(models.User)
            .filter(models.User.username == "testuser")
            .first()
        )
        test_user.role = "manager"
        test_db.commit()
    finally:
        test_db.close()

    manager_headers = {"Authorization": f"Bearer {token}"}

    team_response = client.post(
        "/teams",
        headers=manager_headers,
        json={
            "name": "Protected Delete Team",
            "description": "Protected team",
        },
    )
    assert team_response.status_code == 201
    team_id = team_response.json()["id"]

    register_response = client.post(
        "/register",
        json={
            "username": "deletealex",
            "email": "deletealex@example.com",
            "password": "DeleteAlex2026!",
        },
    )
    assert register_response.status_code == 201

    add_response = client.post(
        f"/teams/{team_id}/members",
        headers=manager_headers,
        json={"user_id": 2, "role": "member"},
    )
    assert add_response.status_code == 201

    alex_login = client.post(
        "/login",
        json={
            "username": "deletealex",
            "password": "DeleteAlex2026!",
        },
    )
    assert alex_login.status_code == 200

    alex_headers = {
        "Authorization": f"Bearer {alex_login.json()['access_token']}"
    }

    delete_response = client.delete(
        f"/teams/{team_id}",
        headers=alex_headers,
    )

    assert delete_response.status_code == 404

