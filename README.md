# Task Management API

A RESTful Task Management API built with Python and FastAPI.

This project provides user authentication, JWT-based authorization, personal task management, SQLite database persistence, input validation, error handling, interactive API documentation, and automated tests.

## Features

- User registration
- User login
- Password hashing with bcrypt
- JWT authentication
- Authenticated user profile
- Create tasks
- List personal tasks
- Get a task by ID
- Update tasks
- Delete tasks
- User-specific task access
- Request validation with Pydantic
- HTTP error handling
- SQLite database
- SQLAlchemy ORM
- Swagger API documentation
- ReDoc API documentation
- Automated tests with pytest
- Environment-based JWT secret configuration

## Tech Stack

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

## Project Structure

```text
task-management-api/
├── src/
│   ├── __init__.py
│   ├── auth.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── security.py
│
├── tests/
│   └── test_main.py
│
├── .gitignore
└── README.md
