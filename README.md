# TaskFlow — Full-Stack Task & Project Management Platform

TaskFlow is a full-stack task and project management platform built with **FastAPI, React, SQLAlchemy, and SQLite**.

It provides secure authentication, role-based access control, team collaboration, project management, task tracking, progress monitoring, notifications, comments, subtasks, and a company-level manager dashboard.

## Features

### Authentication & Security

- User registration and login
- JWT-based authentication
- Secure password hashing with bcrypt
- Authenticated user profile
- Protected API endpoints
- Role-based authorization
- Request validation with Pydantic
- HTTP error handling

### Team Management

- Create and manage teams
- Add and remove team members
- Team membership management
- Member, Team Head, and Admin roles
- Manager-level team administration
- Team member isolation
- Protected cross-team access

### Task Management

- Create, view, update, and delete tasks
- Assign tasks to users
- Task priorities
- Task categories
- Due dates
- Completion tracking
- Overdue task detection
- Task search and filtering
- Subtasks
- Task progress tracking

### Project Management

- Create and manage projects
- Project ownership
- Project status
- Start and due dates
- Team-based projects
- Project overview
- Project progress tracking
- Project dashboard
- Role-based project authorization

### Manager Dashboard

Managers can view company-level performance information including:

- Total teams
- Total members
- Total projects
- Total tasks
- Completed tasks
- To-do tasks
- In-progress tasks
- In-review tasks
- Overdue tasks
- Overall completion progress
- Team performance summaries

### Role-Based Workspace

| Role | Capabilities |
|---|---|
| **Manager** | Company-wide visibility, team management, role management, manager dashboard |
| **Team Head** | Manage team members, team projects, and team tasks |
| **Member** | Work with assigned tasks and projects |

Authorization is enforced by the backend rather than relying only on frontend restrictions.

### Collaboration

- Task comments
- Comment updates
- Comment deletion
- Activity tracking
- User notifications
- Notification read/unread state

### Frontend

- Dashboard
- Task table
- Kanban workflow
- Calendar
- Project dashboard
- Team workspace
- Notifications
- Comments
- Subtasks and progress tracking
- Search and filtering
- Role-aware navigation
- Responsive interface

## Tech Stack

### Backend

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- SQLite
- Pydantic
- python-jose
- Passlib
- bcrypt
- pytest
- HTTPX

### Frontend

- React
- Vite
- JavaScript
- Axios
- CSS
- Tailwind CSS

## Architecture

```text
React + Vite
     |
     | HTTP / REST
     v
FastAPI
     |
     +-- Authentication
     +-- Authorization
     +-- Teams
     +-- Projects
     +-- Tasks
     +-- Comments
     +-- Notifications
     |
     v
SQLAlchemy
     |
     v
SQLite
Project Structure
task-management-api/
|
+-- src/
|   +-- __init__.py
|   +-- auth.py
|   +-- database.py
|   +-- main.py
|   +-- models.py
|   +-- schemas.py
|   +-- security.py
|
+-- tests/
|   +-- test_main.py
|
+-- frontend/
|   +-- src/
|   |   +-- App.jsx
|   |   +-- App.css
|   |   +-- ...
|   +-- package.json
|   +-- ...
|
+-- .gitignore
+-- README.md
+-- requirements.txt
Installation
Clone the Repository
git clone https://github.com/Chavhann/task-management-api.git
cd task-management-api
Backend Setup

Create a virtual environment:

python -m venv .venv

Activate it on Windows:

.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Start the backend:

uvicorn src.main:app --reload

Backend:

http://127.0.0.1:8000
Frontend Setup

Open another terminal:

cd frontend
npm install
npm run dev

Frontend:

http://localhost:5173
API Documentation
Swagger UI
http://127.0.0.1:8000/docs
ReDoc
http://127.0.0.1:8000/redoc
OpenAPI
http://127.0.0.1:8000/openapi.json
Testing

Run the backend test suite:

pytest -q

Current verification:

58 tests passed
Frontend production build successful
Git working tree clean
Authorization Model

TaskFlow uses two levels of roles.

Company-Level Role
Manager
Member
Team-Level Role
Admin
Team Head
Member

This separates company-wide responsibilities from team-specific permissions.

Example:

Company
|
+-- Manager
|
+-- Team Cyberpunk
|   +-- Admin
|   +-- Team Head
|   +-- Members
|
+-- Other Teams
    +-- Team Head
    +-- Members

Backend authorization prevents users from bypassing permission restrictions by directly calling protected API endpoints.

Security
JWT access tokens
Password hashing
Protected API routes
Role-based authorization
Team-level authorization
Project access control
Task access control
Cross-team isolation
Input validation
Duplicate membership protection
Protected role assignment
API Overview
Authentication
+-- POST /register
+-- POST /login
+-- GET  /me

Teams
+-- GET    /teams
+-- POST   /teams
+-- GET    /teams/{team_id}
+-- PUT    /teams/{team_id}
+-- DELETE /teams/{team_id}

Projects
+-- GET    /projects
+-- POST   /projects
+-- GET    /projects/{project_id}
+-- PUT    /projects/{project_id}
+-- DELETE /projects/{project_id}

Tasks
+-- GET    /tasks
+-- POST   /tasks
+-- GET    /tasks/{task_id}
+-- PUT    /tasks/{task_id}
+-- DELETE /tasks/{task_id}

Collaboration
+-- Comments
+-- Notifications
+-- Activities
+-- Subtasks

Management
+-- GET /manager/dashboard
Project Goals

TaskFlow demonstrates practical full-stack development skills including:

REST API development
Backend architecture
Database modeling
Authentication
Authorization
Role-based access control
React frontend development
API integration
Team collaboration workflows
Automated testing
Git and GitHub workflow
What Makes TaskFlow Different

TaskFlow goes beyond basic CRUD by implementing multiple levels of authorization:

Company Permissions
        +
Team Permissions
        +
Project Permissions
        +
Task Permissions

This creates a realistic foundation for collaborative productivity software.

Status
Backend API — Complete
Authentication — Complete
JWT Security — Complete
Task CRUD — Complete
Project Management — Complete
Team Management — Complete
Role-Based Access — Complete
Team Head Controls — Complete
Manager Dashboard — Complete
Notifications — Complete
Comments — Complete
Subtasks — Complete
Progress Tracking — Complete
React Frontend — Complete
Kanban — Complete
Calendar — Complete
Automated Tests — Complete
Production Build — Complete
Author

Ganesh Chavhan

GitHub: https://github.com/Chavhann

License

This project is available under the MIT License.
