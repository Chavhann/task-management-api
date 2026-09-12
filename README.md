# TaskFlow — Full-Stack Task & Project Management Platform

![Python](https://img.shields.io/badge/Python-3.x-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-REST-green)
![React](https://img.shields.io/badge/React-Frontend-61DAFB)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57)
![Tests](https://img.shields.io/badge/Tests-58%20passed-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

TaskFlow is a full-stack task and project management platform built with **FastAPI, React, SQLAlchemy, and SQLite**.

It combines secure authentication, role-based access control, team collaboration, project management, task tracking, progress monitoring, notifications, comments, subtasks, Kanban workflow, calendar views, and a company-level manager dashboard.

## Features

### Authentication & Security
- User registration and login
- JWT-based authentication
- Secure password hashing with bcrypt
- Protected API endpoints
- Role-based authorization
- Request validation
- Cross-team access isolation

### Team Management
- Create and manage teams
- Add and remove team members
- Member, Team Head, and Admin roles
- Manager-level team administration
- Protected role assignment
- Duplicate membership protection

### Task Management
- Full task CRUD
- Task assignment
- Priorities and categories
- Due dates
- Completion tracking
- Overdue detection
- Search and filtering
- Subtasks
- Progress tracking

### Project Management
- Full project CRUD
- Project ownership
- Project status
- Start and due dates
- Team-based projects
- Project overview and progress
- Role-based authorization

### Manager Dashboard
- Total teams
- Total members
- Total projects
- Total tasks
- Completed tasks
- To-do tasks
- In-progress tasks
- In-review tasks
- Overdue tasks
- Overall progress
- Team performance summaries

### Role-Based Workspace

| Role | Capabilities |
|---|---|
| **Manager** | Company-wide visibility, team management, role management, manager dashboard |
| **Team Head** | Manage team members, team projects, and team tasks |
| **Member** | Work with assigned tasks and projects |

### Collaboration
- Task comments
- Comment updates and deletion
- Activity tracking
- User notifications
- Notification read/unread state
- Subtasks and progress tracking

### Frontend
- Dashboard
- Task table
- Kanban workflow
- Calendar
- Project dashboard
- Team workspace
- Notifications
- Comments
- Search and filtering
- Role-aware navigation
- Responsive interface

## Tech Stack

**Backend**
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

**Frontend**
- React
- Vite
- JavaScript
- Axios
- CSS
- Tailwind CSS

## Architecture

    React + Vite
         |
         | HTTP / REST
         v
       FastAPI
         |
    +----+----+-------------+
    |         |             |
    Auth   Authorization   API
    |         |             |
    +---------+-------------+
              |
         SQLAlchemy
              |
              v
            SQLite

## Project Structure

    task-management-api/
    ├── src/
    │   ├── __init__.py
    │   ├── auth.py
    │   ├── database.py
    │   ├── main.py
    │   ├── models.py
    │   ├── schemas.py
    │   └── security.py
    ├── tests/
    │   └── test_main.py
    ├── frontend/
    │   ├── src/
    │   │   ├── App.jsx
    │   │   ├── App.css
    │   │   └── ...
    │   ├── package.json
    │   └── ...
    ├── .gitignore
    ├── README.md
    └── requirements.txt

## Installation

### Clone

    git clone https://github.com/Chavhann/task-management-api.git
    cd task-management-api

### Backend

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    uvicorn src.main:app --reload

Backend: `http://127.0.0.1:8000`

### Frontend

Open another terminal:

    cd frontend
    npm install
    npm run dev

Frontend: `http://localhost:5173`

## API Documentation

Once the backend is running:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`

## Testing

Run:

    pytest -q

Current verification:

**58 tests passed**

Frontend production build:

    npm --prefix frontend run build

## Authorization Model

TaskFlow uses two levels of roles.

**Company roles**
- Manager
- Member

**Team roles**
- Admin
- Team Head
- Member

This separates company-wide responsibilities from team-specific permissions.

    Company
    ├── Manager
    │
    ├── Team Cyberpunk
    │   ├── Admin
    │   ├── Team Head
    │   └── Members
    │
    └── Other Teams
        ├── Team Head
        └── Members

Backend authorization prevents users from bypassing permission restrictions through protected API endpoints.

## Security

- JWT access tokens
- Password hashing
- Protected API routes
- Role-based authorization
- Team-level authorization
- Project access control
- Task access control
- Cross-team isolation
- Input validation
- Duplicate membership protection
- Protected role assignment

## API Overview

**Authentication**
- `POST /register`
- `POST /login`
- `GET /me`

**Teams**
- `GET /teams`
- `POST /teams`
- `GET /teams/{team_id}`
- `PUT /teams/{team_id}`
- `DELETE /teams/{team_id}`

**Team Members**
- `GET /teams/{team_id}/members`
- `POST /teams/{team_id}/members`
- `PUT /teams/{team_id}/members/{user_id}`
- `DELETE /teams/{team_id}/members/{user_id}`

**Projects**
- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}`
- `PUT /projects/{project_id}`
- `DELETE /projects/{project_id}`

**Tasks**
- `GET /tasks`
- `POST /tasks`
- `GET /tasks/{task_id}`
- `PUT /tasks/{task_id}`
- `DELETE /tasks/{task_id}`

**Management**
- `GET /manager/dashboard`

## What Makes TaskFlow Different

TaskFlow goes beyond basic CRUD by implementing multiple authorization layers:

    Company Permissions
            +
       Team Permissions
            +
     Project Permissions
            +
       Task Permissions

This creates a realistic foundation for collaborative productivity software.

## Project Status

| Component | Status |
|---|---|
| Backend API | Complete |
| Authentication | Complete |
| JWT Security | Complete |
| Task CRUD | Complete |
| Project Management | Complete |
| Team Management | Complete |
| Role-Based Access | Complete |
| Team Head Controls | Complete |
| Manager Dashboard | Complete |
| Notifications | Complete |
| Comments | Complete |
| Subtasks | Complete |
| Progress Tracking | Complete |
| React Frontend | Complete |
| Kanban | Complete |
| Calendar | Complete |
| Automated Tests | Complete |
| Production Build | Complete |

## Author

**Ganesh Chavhan**

GitHub: https://github.com/Chavhann

## License

This project is licensed under the MIT License.
