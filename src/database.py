import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./task_manager.db",
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def migrate_database():
    inspector = inspect(engine)

    tables = inspector.get_table_names()

    # --------------------------------
    # Tasks table migrations
    # --------------------------------

    if "tasks" in tables:
        columns = {
            column["name"]
            for column in inspector.get_columns("tasks")
        }

        if "due_date" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE tasks "
                        "ADD COLUMN due_date DATE"
                    )
                )

        inspector = inspect(engine)

        columns = {
            column["name"]
            for column in inspector.get_columns("tasks")
        }

        if "priority" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE tasks "
                        "ADD COLUMN priority VARCHAR(10) "
                        "NOT NULL DEFAULT 'medium'"
                    )
                )

        inspector = inspect(engine)

        columns = {
            column["name"]
            for column in inspector.get_columns("tasks")
        }

        if "category" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE tasks "
                        "ADD COLUMN category VARCHAR(20) "
                        "NOT NULL DEFAULT 'other'"
                    )
                )

    # --------------------------------
    # Teams table
    # --------------------------------

    inspector = inspect(engine)

    tables = inspector.get_table_names()

    if "teams" not in tables:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE TABLE teams (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        owner_id INTEGER NOT NULL,
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(owner_id) REFERENCES users(id)
                    )
                    """
                )
            )

    # --------------------------------
    # Team members table
    # --------------------------------

    inspector = inspect(engine)

    tables = inspector.get_table_names()

    if "team_members" not in tables:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE TABLE team_members (
                        id INTEGER PRIMARY KEY,
                        team_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        role VARCHAR(20) NOT NULL DEFAULT 'member',
                        joined_at DATETIME NOT NULL,
                        FOREIGN KEY(team_id) REFERENCES teams(id),
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )
                    """
                )
            )