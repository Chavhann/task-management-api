import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base, get_db
from src.main import app


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


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Task Management API is running"


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user(client):
    response = client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert "password" not in data
    assert "password_hash" not in data


def test_duplicate_registration(client):
    client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword123",
        },
    )

    response = client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Username or email already registered"