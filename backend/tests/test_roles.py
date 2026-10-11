import pytest

from app.models.user import UserRole
from tests.conftest import auth_header, login


@pytest.fixture()
def users(make_user):
    make_user("student@college.edu", UserRole.STUDENT)
    make_user("staff@college.edu", UserRole.STAFF)
    make_user("admin@college.edu", UserRole.ADMIN)


# TEST 4
def test_student_can_access_student_dashboard(client, users):
    res = client.get("/api/student/dashboard", headers=auth_header(client, "student@college.edu"))
    assert res.status_code == 200
    assert res.json()["data"]["statistics"]["problems_solved"] == 0


# TEST 5
def test_student_cannot_access_staff_dashboard(client, users):
    res = client.get("/api/staff/dashboard", headers=auth_header(client, "student@college.edu"))
    assert res.status_code == 403


# TEST 6
def test_student_cannot_access_admin(client, users):
    res = client.get("/api/admin/stats", headers=auth_header(client, "student@college.edu"))
    assert res.status_code == 403


# TEST 7
def test_staff_login_and_dashboard(client, users):
    res = login(client, "staff@college.edu", portal="STAFF")
    assert res.status_code == 200
    assert res.json()["data"]["user"]["role"] == "STAFF"
    res = client.get("/api/staff/dashboard", headers=auth_header(client, "staff@college.edu"))
    assert res.status_code == 200


# TEST 8
def test_staff_cannot_access_admin(client, users):
    res = client.get("/api/admin/users", headers=auth_header(client, "staff@college.edu"))
    assert res.status_code == 403


# TEST 9
def test_admin_login_and_dashboard(client, users):
    res = login(client, "admin@college.edu", portal="ADMIN")
    assert res.status_code == 200
    res = client.get("/api/admin/stats", headers=auth_header(client, "admin@college.edu"))
    assert res.status_code == 200
    assert res.json()["data"] == {
        "total_students": 1,
        "total_staff": 1,
        "total_admins": 1,
        "total_problems": 0,
        "active_users": 3,
    }


def test_unauthenticated_requests_rejected(client):
    for path in ("/api/student/dashboard", "/api/staff/dashboard", "/api/admin/stats"):
        assert client.get(path).status_code == 401
