import pytest

from app.models.user import UserRole
from tests.conftest import PASSWORD, auth_header, login


@pytest.fixture()
def admin_headers(client, make_user):
    make_user("admin@college.edu", UserRole.ADMIN, name="Main Admin")
    make_user("riya@college.edu", UserRole.STUDENT, name="Riya Sharma")
    make_user("arjun@college.edu", UserRole.STUDENT, name="Arjun Rao")
    make_user("prof@college.edu", UserRole.STAFF, name="Prof Mehta")
    return auth_header(client, "admin@college.edu")


def test_list_users_with_filters(client, admin_headers):
    res = client.get("/api/admin/users", headers=admin_headers)
    assert res.json()["data"]["total"] == 4

    res = client.get("/api/admin/users?role=STUDENT", headers=admin_headers)
    assert {u["email"] for u in res.json()["data"]["items"]} == {
        "riya@college.edu",
        "arjun@college.edu",
    }

    res = client.get("/api/admin/users?search=riya", headers=admin_headers)
    assert [u["full_name"] for u in res.json()["data"]["items"]] == ["Riya Sharma"]

    res = client.get("/api/admin/users?search=PROF@", headers=admin_headers)
    assert res.json()["data"]["total"] == 1


def test_deactivate_and_reactivate_user(client, admin_headers, db_session):
    res = client.get("/api/admin/users?search=riya", headers=admin_headers)
    riya_id = res.json()["data"]["items"][0]["id"]
    riya_headers = auth_header(client, "riya@college.edu")

    res = client.patch(
        f"/api/admin/users/{riya_id}/status", json={"is_active": False}, headers=admin_headers
    )
    assert res.status_code == 200
    assert res.json()["data"]["is_active"] is False
    # Existing token stops working immediately and login is refused.
    assert client.get("/api/auth/me", headers=riya_headers).status_code == 401
    assert login(client, "riya@college.edu").status_code == 403

    res = client.patch(
        f"/api/admin/users/{riya_id}/status", json={"is_active": True}, headers=admin_headers
    )
    assert res.json()["data"]["is_active"] is True
    assert login(client, "riya@college.edu").status_code == 200


def test_admin_cannot_deactivate_self(client, admin_headers):
    me = client.get("/api/auth/me", headers=admin_headers).json()["data"]
    res = client.patch(
        f"/api/admin/users/{me['id']}/status", json={"is_active": False}, headers=admin_headers
    )
    assert res.status_code == 400


def test_last_active_admin_protected(client, admin_headers, make_user):
    # A second admin tries to deactivate the first, then the first tries back.
    make_user("admin2@college.edu", UserRole.ADMIN)
    admin2_headers = auth_header(client, "admin2@college.edu")
    first = client.get("/api/auth/me", headers=admin_headers).json()["data"]
    second = client.get("/api/auth/me", headers=admin2_headers).json()["data"]

    res = client.patch(
        f"/api/admin/users/{first['id']}/status", json={"is_active": False}, headers=admin2_headers
    )
    assert res.status_code == 200

    # admin2 is now the only active admin and cannot deactivate themselves.
    res = client.patch(
        f"/api/admin/users/{second['id']}/status", json={"is_active": False},
        headers=admin2_headers,
    )
    assert res.status_code == 400


def test_status_update_unknown_user(client, admin_headers):
    res = client.patch("/api/admin/users/9999/status", json={"is_active": False},
                       headers=admin_headers)
    assert res.status_code == 404


def test_admin_creates_staff(client, admin_headers):
    res = client.post(
        "/api/admin/staff",
        json={"full_name": "New Staff", "email": "new.staff@college.edu", "password": PASSWORD},
        headers=admin_headers,
    )
    assert res.status_code == 201
    assert res.json()["data"]["role"] == "STAFF"
    assert login(client, "new.staff@college.edu", portal="STAFF").status_code == 200


def test_non_admin_cannot_create_staff(client, admin_headers):
    student_headers = auth_header(client, "riya@college.edu")
    res = client.post(
        "/api/admin/staff",
        json={"full_name": "Sneaky", "email": "sneaky@college.edu", "password": PASSWORD},
        headers=student_headers,
    )
    assert res.status_code == 403
