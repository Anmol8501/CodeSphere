"""Test setup: an isolated in-memory SQLite database per test.

Environment variables are set BEFORE importing the app so tests never touch
your real PostgreSQL database or .env secrets.
"""

import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-that-is-at-least-32-characters-long"
os.environ["RATE_LIMIT_ENABLED"] = "false"
# Cheap password hashes keep the suite fast (production default is 12).
os.environ["BCRYPT_ROUNDS"] = "4"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import UserRole  # noqa: E402
from app.services import user_service  # noqa: E402

PASSWORD = "Password123"


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enforce foreign keys (ON DELETE CASCADE / SET NULL) like PostgreSQL does.
    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db_session):
    def _make(email: str, role: UserRole, password: str = PASSWORD, name: str = "Test User"):
        return user_service.create_user(
            db_session, full_name=name, email=email, password=password, role=role
        )

    return _make


def login(client: TestClient, email: str, password: str = PASSWORD, portal: str | None = None):
    body = {"email": email, "password": password}
    if portal:
        body["portal"] = portal
    return client.post("/api/auth/login", json=body)


def auth_header(client: TestClient, email: str, password: str = PASSWORD) -> dict[str, str]:
    token = login(client, email, password).json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
