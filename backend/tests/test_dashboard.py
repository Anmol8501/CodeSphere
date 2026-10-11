"""Phase 2 dashboard API tests: structure, real values only, role access."""

import pytest

from app.models.user import UserRole
from tests.conftest import auth_header


@pytest.fixture()
def headers(client, make_user):
    make_user("student@college.edu", UserRole.STUDENT, name="Asha Kumar")
    make_user("student2@college.edu", UserRole.STUDENT, name="Ravi Iyer")
    make_user("staff@college.edu", UserRole.STAFF, name="Prof Mehta")
    make_user("admin@college.edu", UserRole.ADMIN, name="Main Admin")
    return {
        "STUDENT": auth_header(client, "student@college.edu"),
        "STAFF": auth_header(client, "staff@college.edu"),
        "ADMIN": auth_header(client, "admin@college.edu"),
    }


def test_student_dashboard_structure_and_honest_values(client, headers):
    res = client.get("/api/student/dashboard", headers=headers["STUDENT"])
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["user"] == {
        "id": data["user"]["id"],
        "full_name": "Asha Kumar",
        "email": "student@college.edu",
        "role": "STUDENT",
    }
    assert data["statistics"] == {
        "problems_solved": 0,
        "total_problems": 0,
        "attempted_problems": 0,
        "total_attempts": 0,
        "accepted_submissions": 0,
        "acceptance_rate": 0,
        "current_streak": 0,
        "longest_streak": 0,
        "active_today": False,
        "contest_rating": None,
    }
    zero = {"total": 0, "solved": 0, "percentage": 0}
    assert data["difficulty"] == {"easy": zero, "medium": zero, "hard": zero}
    # Learning progress comes from database topics that have published problems;
    # this fixture has none, so the honest values are empty lists (see
    # test_problems.py and test_progress.py for populated cases).
    assert data["learning_progress"] == []
    assert data["continue_learning"] == []
    assert data["timezone"] == "Asia/Kolkata"
    assert "password" not in res.text.lower()


def test_staff_dashboard_structure(client, headers):
    res = client.get("/api/staff/dashboard", headers=headers["STAFF"])
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["user"]["full_name"] == "Prof Mehta"
    assert data["user"]["role"] == "STAFF"
    # Two STUDENT accounts exist in the fixture; staff/admin are not counted.
    assert data["statistics"] == {"students": 2, "classrooms": 0, "assignments": 0, "contests": 0}


def test_staff_student_count_reflects_new_registration(client, headers):
    """Regression: the staff dashboard used to return a hardcoded 0."""
    before = client.get("/api/staff/dashboard", headers=headers["STAFF"]).json()["data"]["statistics"]["students"]
    res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Phase2 Test Student",
            "email": "phase2_test@example.com",
            "password": "TestPassword123!",
            "confirm_password": "TestPassword123!",
        },
    )
    assert res.status_code == 201
    after = client.get("/api/staff/dashboard", headers=headers["STAFF"]).json()["data"]["statistics"]["students"]
    assert after == before + 1

    admin = client.get("/api/admin/dashboard", headers=headers["ADMIN"]).json()["data"]
    assert admin["total_students"] == after


def test_admin_dashboard_counts_come_from_database(client, headers, make_user, db_session):
    make_user("inactive@college.edu", UserRole.STUDENT)
    from app.models.user import User

    user = db_session.query(User).filter_by(email="inactive@college.edu").one()
    user.is_active = False
    db_session.commit()

    data = client.get("/api/admin/dashboard", headers=headers["ADMIN"]).json()["data"]
    assert data["total_users"] == 5
    assert data["total_students"] == 3
    assert data["total_staff"] == 1
    assert data["total_admins"] == 1
    assert data["active_users"] == 4
    assert data["inactive_users"] == 1


def test_admin_dashboard_system_status_is_honest(client, headers):
    data = client.get("/api/admin/dashboard", headers=headers["ADMIN"]).json()["data"]
    status = {s["key"]: s["status"] for s in data["system_status"]}
    assert status == {
        "api": "online",
        "database": "online",
        "auth": "online",
        "judge": "not_connected",
        "ai": "not_connected",
    }


@pytest.mark.parametrize(
    "path, allowed",
    [
        ("/api/student/dashboard", "STUDENT"),
        ("/api/staff/dashboard", "STAFF"),
        ("/api/admin/dashboard", "ADMIN"),
    ],
)
def test_dashboard_role_access(client, headers, path, allowed):
    for role, header in headers.items():
        res = client.get(path, headers=header)
        expected = 200 if role == allowed else 403
        assert res.status_code == expected, (role, path, res.status_code)
    assert client.get(path).status_code == 401


def test_admin_user_status_filter(client, headers, make_user, db_session):
    from app.models.user import User

    make_user("off@college.edu", UserRole.STUDENT)
    db_session.query(User).filter_by(email="off@college.edu").one().is_active = False
    db_session.commit()

    inactive = client.get("/api/admin/users?is_active=false", headers=headers["ADMIN"]).json()["data"]
    assert [u["email"] for u in inactive["items"]] == ["off@college.edu"]

    active = client.get("/api/admin/users?is_active=true&role=STUDENT", headers=headers["ADMIN"]).json()["data"]
    assert {u["email"] for u in active["items"]} == {"student@college.edu", "student2@college.edu"}
