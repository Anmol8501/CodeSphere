from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import settings
from app.models.user import User, UserRole
from tests.conftest import PASSWORD, auth_header, login

STUDENT = {
    "full_name": "Asha Kumar",
    "email": "Asha@College.edu",
    "password": PASSWORD,
    "confirm_password": PASSWORD,
}


# TEST 1
def test_register_student_creates_student(client, db_session):
    res = client.post("/api/auth/register", json=STUDENT)
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    assert body["data"]["role"] == "STUDENT"
    assert body["data"]["email"] == "asha@college.edu"  # normalized
    assert "password_hash" not in body["data"]
    assert "password" not in body["data"]

    stored = db_session.query(User).one()
    assert stored.password_hash != PASSWORD
    assert stored.password_hash.startswith("$2")  # bcrypt


def test_register_rejects_role_field(client, db_session):
    for role in ("ADMIN", "STAFF", "STUDENT"):
        res = client.post("/api/auth/register", json={**STUDENT, "role": role})
        assert res.status_code == 422
        assert res.json()["message"] == "Role cannot be chosen during registration."
    assert db_session.query(User).count() == 0


# TEST 2
def test_register_duplicate_email_fails(client):
    client.post("/api/auth/register", json=STUDENT)
    res = client.post("/api/auth/register", json={**STUDENT, "email": "asha@college.edu"})
    assert res.status_code == 409
    assert res.json() == {
        "success": False,
        "message": "An account with this email already exists.",
        "error": {"code": "CONFLICT", "message": "An account with this email already exists."},
    }


def test_register_validation_messages(client):
    res = client.post(
        "/api/auth/register",
        json={**STUDENT, "confirm_password": "Different123"},
    )
    assert res.status_code == 422
    assert res.json()["message"] == "Passwords do not match."

    res = client.post("/api/auth/register", json={**STUDENT, "email": "not-an-email"})
    assert res.json()["message"] == "Please enter a valid email address."

    res = client.post(
        "/api/auth/register", json={**STUDENT, "password": "short", "confirm_password": "short"}
    )
    assert "at least 8 characters" in res.json()["message"]


# TEST 3
def test_login_student_returns_jwt(client):
    client.post("/api/auth/register", json=STUDENT)
    res = login(client, "asha@college.edu", portal="STUDENT")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "STUDENT"
    payload = jwt.decode(data["access_token"], settings.JWT_SECRET, algorithms=["HS256"])
    assert payload["sub"] == str(data["user"]["id"])


def test_login_wrong_password(client):
    client.post("/api/auth/register", json=STUDENT)
    res = login(client, "asha@college.edu", "WrongPass999")
    assert res.status_code == 401
    assert res.json()["message"] == "Invalid email or password."
    res = login(client, "nobody@college.edu")
    assert res.status_code == 401
    assert res.json()["message"] == "Invalid email or password."


def test_login_portal_mismatch_rejected(client, make_user):
    make_user("student@college.edu", UserRole.STUDENT)
    res = login(client, "student@college.edu", portal="STAFF")
    assert res.status_code == 403
    res = login(client, "student@college.edu", portal="ADMIN")
    assert res.status_code == 403
    assert "admin portal" in res.json()["message"]


def test_inactive_user_cannot_login(client, make_user, db_session):
    user = make_user("student@college.edu", UserRole.STUDENT)
    user.is_active = False
    db_session.commit()
    res = login(client, "student@college.edu")
    assert res.status_code == 403
    assert "deactivated" in res.json()["message"]


def test_me_returns_current_user(client, make_user):
    make_user("student@college.edu", UserRole.STUDENT)
    res = client.get("/api/auth/me", headers=auth_header(client, "student@college.edu"))
    assert res.status_code == 200
    assert res.json()["data"]["email"] == "student@college.edu"


# TEST 10 (server side): logout succeeds; afterwards the client has no token
def test_logout(client, make_user):
    make_user("student@college.edu", UserRole.STUDENT)
    res = client.post("/api/auth/logout", headers=auth_header(client, "student@college.edu"))
    assert res.status_code == 200
    assert client.get("/api/student/dashboard").status_code == 401


# TEST 12
def test_invalid_token_rejected(client):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401
    assert res.json()["success"] is False


def test_expired_token_rejected(client, make_user):
    user = make_user("student@college.edu", UserRole.STUDENT)
    past = datetime.now(UTC) - timedelta(hours=2)
    token = jwt.encode(
        {"sub": str(user.id), "type": "access", "iat": past, "exp": past + timedelta(minutes=1)},
        settings.JWT_SECRET,
        algorithm="HS256",
    )
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert res.json()["message"] == "Your session has expired. Please login again."


def test_token_with_forged_role_does_not_grant_admin(client, make_user):
    user = make_user("student@college.edu", UserRole.STUDENT)
    now = datetime.now(UTC)
    # Even a correctly signed token claiming ADMIN is ignored: role comes from the DB.
    token = jwt.encode(
        {"sub": str(user.id), "role": "ADMIN", "type": "access", "iat": now,
         "exp": now + timedelta(minutes=5)},
        settings.JWT_SECRET,
        algorithm="HS256",
    )
    res = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
