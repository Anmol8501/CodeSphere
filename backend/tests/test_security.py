"""Security-focused checks from the Phase 1 authentication audit."""

import base64
import json
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole
from app.utils.rate_limiter import RateLimiter
from tests.conftest import PASSWORD, auth_header, login

VALID = {
    "full_name": "Test Student",
    "email": "student_test@example.com",
    "password": "TestPassword123!",
    "confirm_password": "TestPassword123!",
}


# ---------------------------------------------------------------- registration
@pytest.mark.parametrize(
    "patch, expected",
    [
        ({"full_name": ""}, "Full name is required."),
        ({"full_name": "     "}, "Full name is required."),
        ({"email": ""}, "Please enter a valid email address."),
        ({"email": "   "}, "Please enter a valid email address."),
        ({"email": "student@"}, "Please enter a valid email address."),
        ({"password": "Ab1", "confirm_password": "Ab1"}, "at least 8 characters"),
        ({"password": "        ", "confirm_password": "        "}, "one letter and one number"),
        ({"confirm_password": "Mismatch123!"}, "Passwords do not match."),
    ],
)
def test_invalid_registration_rejected_and_not_saved(client, db_session, patch, expected):
    res = client.post("/api/auth/register", json={**VALID, **patch})
    assert res.status_code == 422
    assert expected in res.json()["message"]
    assert db_session.query(User).count() == 0


def test_missing_confirm_password(client, db_session):
    body = {k: v for k, v in VALID.items() if k != "confirm_password"}
    res = client.post("/api/auth/register", json=body)
    assert res.status_code == 422
    assert res.json()["message"] == "Confirm password is required."
    assert db_session.query(User).count() == 0


def test_valid_registration_hashes_password(client, db_session):
    res = client.post("/api/auth/register", json=VALID)
    assert res.status_code == 201
    user = db_session.query(User).one()
    assert user.role == UserRole.STUDENT
    assert user.password_hash != VALID["password"]
    assert VALID["password"] not in user.password_hash
    assert user.password_hash.startswith("$2b$")


# ---------------------------------------------------------- responses / leaks
def test_no_password_data_in_any_auth_response(client):
    reg = client.post("/api/auth/register", json=VALID).text
    log = login(client, VALID["email"], VALID["password"]).text
    token = json.loads(log)["data"]["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).text
    for body in (reg, log, me):
        assert "password" not in body.lower()
        assert "$2b$" not in body
        assert settings.JWT_SECRET not in body


def test_unknown_email_and_wrong_password_look_identical(client, make_user):
    make_user("real@college.edu", UserRole.STUDENT)
    a = login(client, "real@college.edu", "WrongPass123")
    b = login(client, "ghost@college.edu", "WrongPass123")
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json() == {
        "success": False,
        "message": "Invalid email or password.",
        "error": {"code": "UNAUTHORIZED", "message": "Invalid email or password."},
    }


# ---------------------------------------------------------------- authorization
@pytest.fixture()
def tokens(client, make_user):
    make_user("student@college.edu", UserRole.STUDENT)
    make_user("staff@college.edu", UserRole.STAFF)
    make_user("admin@college.edu", UserRole.ADMIN)
    return {
        "STUDENT": auth_header(client, "student@college.edu"),
        "STAFF": auth_header(client, "staff@college.edu"),
        "ADMIN": auth_header(client, "admin@college.edu"),
    }


ENDPOINTS = {
    ("GET", "/api/student/dashboard"): {"STUDENT"},
    ("GET", "/api/staff/dashboard"): {"STAFF"},
    ("GET", "/api/admin/stats"): {"ADMIN"},
    ("GET", "/api/admin/dashboard"): {"ADMIN"},
    ("GET", "/api/admin/users"): {"ADMIN"},
    ("PATCH", "/api/admin/users/1/status"): {"ADMIN"},
    ("POST", "/api/admin/staff"): {"ADMIN"},
}


@pytest.mark.parametrize("role", ["STUDENT", "STAFF", "ADMIN"])
def test_role_matrix(client, tokens, role):
    for (method, path), allowed in ENDPOINTS.items():
        body = None
        if path.endswith("/status"):
            body = {"is_active": True}
        elif path.endswith("/staff"):
            body = {"full_name": "New Staff", "email": f"new.{role.lower()}@college.edu", "password": PASSWORD}
        res = client.request(method, path, headers=tokens[role], json=body)
        if role in allowed:
            assert res.status_code in (200, 201), (role, path, res.text)
        else:
            assert res.status_code == 403, (role, path, res.status_code)
            assert "data" not in res.json()


# ------------------------------------------------------------------- tokens
def _b64(obj) -> str:
    return base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=").decode()


@pytest.mark.parametrize(
    "header",
    [
        None,  # missing
        "Bearer",  # empty
        "Bearer not-a-jwt",  # malformed
        "Bearer a.b.c",  # malformed segments
        "Basic dXNlcjpwYXNz",  # wrong scheme
    ],
)
def test_missing_or_malformed_token(client, tokens, header):
    headers = {"Authorization": header} if header else {}
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 401
    assert res.json()["success"] is False
    assert "data" not in res.json()


def test_alg_none_and_wrong_secret_rejected(client, make_user):
    user = make_user("student@college.edu", UserRole.STUDENT)
    now = datetime.now(UTC)
    claims = {"sub": str(user.id), "type": "access", "iat": int(now.timestamp()),
              "exp": int((now + timedelta(minutes=5)).timestamp())}
    none_token = f"{_b64({'alg': 'none', 'typ': 'JWT'})}.{_b64(claims)}."
    forged = jwt.encode(claims, "attacker-secret-attacker-secret-attacker", algorithm="HS256")
    for token in (none_token, forged):
        res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401


def test_token_for_deleted_user_rejected(client, make_user, db_session):
    user = make_user("student@college.edu", UserRole.STUDENT)
    headers = auth_header(client, "student@college.edu")
    db_session.delete(user)
    db_session.commit()
    assert client.get("/api/auth/me", headers=headers).status_code == 401


# ------------------------------------------------------------- error handling
def test_unhandled_error_returns_generic_message():
    router = APIRouter()

    @router.get("/api/_boom_test")
    def boom():
        raise RuntimeError("secret internal detail /srv/app/db.py password=hunter2")

    app.include_router(router)
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            res = client.get("/api/_boom_test")
        assert res.status_code == 500
        assert res.json() == {
            "success": False,
            "message": "Something went wrong on our side. Please try again later.",
            "error": {"code": "INTERNAL_ERROR", "message": "Something went wrong on our side. Please try again later."},
        }
        assert "hunter2" not in res.text and "Traceback" not in res.text
    finally:
        app.router.routes[:] = [r for r in app.router.routes if getattr(r, "path", "") != "/api/_boom_test"]


def test_database_down_returns_generic_message():
    class BrokenSession:
        def scalar(self, *args, **kwargs):
            raise OperationalError("SELECT 1", {}, Exception("connection to 10.0.0.5 failed: password=xyz"))

        def close(self):
            pass

    app.dependency_overrides[get_db] = lambda: BrokenSession()
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            res = login(client, "someone@college.edu", "Password123")
        assert res.status_code == 500
        assert "xyz" not in res.text and "10.0.0.5" not in res.text
        assert res.json()["message"].startswith("Something went wrong")
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------- rate limit
def test_rate_limiter_blocks_after_limit(monkeypatch):
    from starlette.requests import Request

    from app.core.exceptions import AppError

    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    request = Request({"type": "http", "client": ("1.2.3.4", 1234), "headers": []})
    for _ in range(3):
        limiter(request)
    with pytest.raises(AppError) as exc:
        limiter(request)
    assert exc.value.status_code == 429
