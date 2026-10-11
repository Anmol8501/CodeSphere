"""Phase 4: code drafts (isolation, upsert, conflicts, limits) and run/submit placeholders."""

import pytest

from app.models.draft import CodeDraft
from app.models.submission import Submission
from app.models.user import UserRole
from app.services import topic_service
from tests.conftest import auth_header


@pytest.fixture()
def ws(client, make_user, db_session):
    make_user("asha@college.edu", UserRole.STUDENT, name="Asha")
    make_user("ravi@college.edu", UserRole.STUDENT, name="Ravi")
    make_user("staff@college.edu", UserRole.STAFF)
    make_user("admin@college.edu", UserRole.ADMIN)
    h = {
        "A": auth_header(client, "asha@college.edu"),
        "B": auth_header(client, "ravi@college.edu"),
        "STAFF": auth_header(client, "staff@college.edu"),
        "ADMIN": auth_header(client, "admin@college.edu"),
    }
    topic = topic_service.create_topic(db_session, name="Arrays", slug="arrays", order_index=1)

    def problem(title, published=True, starter=("CPP", "JAVA", "PYTHON")):
        res = client.post(
            "/api/admin/problems",
            json={
                "title": title,
                "description": "A problem used by the workspace tests.",
                "difficulty": "EASY",
                "topic_id": topic.id,
                "starter_codes": [{"language": lang, "starter_code": f"// {lang} starter"} for lang in starter],
                "test_cases": [{"input_data": "1", "expected_output": "HIDDEN-OUT", "is_hidden": True}],
                "is_published": published,
            },
            headers=h["ADMIN"],
        )
        assert res.status_code == 201, res.text
        return res.json()["data"]["id"]

    return {
        "h": h,
        "pub": problem("Two Sum"),
        "draft_only": problem("Secret Draft", published=False),
        "python_only": problem("Python Only", starter=("PYTHON",)),
    }


def url(problem_id):
    return f"/api/problems/{problem_id}/draft"


def save(client, ws, who="A", problem=None, **body):
    data = {"language": "PYTHON", "source_code": "print(1)\n", "base_version": 0, **body}
    return client.put(url(problem or ws["pub"]), json=data, headers=ws["h"][who])


def get(client, ws, who="A", language="PYTHON", problem=None):
    return client.get(url(problem or ws["pub"]), params={"language": language}, headers=ws["h"][who])


# ------------------------------------------------------------------ drafts
def test_no_draft_returns_null(client, ws):
    res = get(client, ws)
    assert res.status_code == 200
    assert res.json()["data"] is None


def test_save_load_and_upsert_without_duplicates(client, ws, db_session):
    first = save(client, ws, source_code="# Phase 4 test\r\nprint(1)\n")
    assert first.status_code == 200, first.text
    assert first.json()["data"]["saved"] is True and first.json()["data"]["version"] == 1

    loaded = get(client, ws).json()["data"]
    assert loaded["source_code"] == "# Phase 4 test\nprint(1)\n"  # CRLF normalized
    assert loaded["language"] == "PYTHON" and loaded["version"] == 1 and loaded["problem_id"] == ws["pub"]

    second = save(client, ws, source_code="print(2)\n", base_version=1)
    assert second.json()["data"]["version"] == 2
    assert get(client, ws).json()["data"]["source_code"] == "print(2)\n"
    rows = db_session.query(CodeDraft).filter_by(problem_id=ws["pub"], language="PYTHON").all()
    assert len(rows) == 1


def test_drafts_are_language_specific(client, ws):
    save(client, ws, language="PYTHON", source_code="py code")
    save(client, ws, language="JAVA", source_code="java code")
    assert get(client, ws, language="PYTHON").json()["data"]["source_code"] == "py code"
    assert get(client, ws, language="JAVA").json()["data"]["source_code"] == "java code"
    assert get(client, ws, language="CPP").json()["data"] is None


def test_drafts_are_user_specific(client, ws, db_session):
    save(client, ws, who="A", source_code="ASHA-SECRET")
    # Ravi sees no draft for the same problem/language and cannot read Asha's code.
    res = get(client, ws, who="B")
    assert res.json()["data"] is None and "ASHA-SECRET" not in res.text
    # Ravi's first save (base_version 0) creates his own row; Asha's stays intact.
    assert save(client, ws, who="B", source_code="RAVI").status_code == 200
    assert get(client, ws, who="A").json()["data"]["source_code"] == "ASHA-SECRET"
    assert db_session.query(CodeDraft).count() == 2


@pytest.mark.parametrize("field", [{"user_id": 1}, {"user_id": 2}, {"problem_id": 99}])
def test_identity_fields_are_rejected(client, ws, field):
    res = save(client, ws, **field)
    assert res.status_code == 422
    assert res.json()["message"].startswith("Unexpected field")


def test_user_id_query_param_is_ignored(client, ws):
    save(client, ws, who="A", source_code="ASHA-SECRET")
    res = client.get(url(ws["pub"]), params={"language": "PYTHON", "user_id": 1}, headers=ws["h"]["B"])
    assert res.status_code == 200 and res.json()["data"] is None


def test_stale_tab_conflict_then_forced_overwrite(client, ws):
    save(client, ws, source_code="tab A v1")                      # version 1
    save(client, ws, source_code="tab A v2", base_version=1)      # version 2
    stale = save(client, ws, source_code="tab B old", base_version=1)
    assert stale.status_code == 409
    assert stale.json()["message"] == "This draft was changed in another tab or window."
    assert get(client, ws).json()["data"]["source_code"] == "tab A v2"  # nothing lost
    forced = save(client, ws, source_code="tab B wins", base_version=1, force=True)
    assert forced.status_code == 200 and forced.json()["data"]["version"] == 3
    # A second "first save" from another tab is also a conflict, not a duplicate row.
    assert save(client, ws, source_code="new tab", base_version=0).status_code == 409


def test_source_size_limit(client, ws):
    assert save(client, ws, source_code="x" * 200_000).status_code == 200
    too_big = save(client, ws, source_code="x" * 200_001, base_version=1)
    assert too_big.status_code == 422


@pytest.mark.parametrize("body", [{"language": "RUBY"}, {"source_code": None}, {"source_code": 123}, {"base_version": -1}])
def test_invalid_draft_payloads(client, ws, body):
    assert save(client, ws, **body).status_code == 422


def test_unpublished_and_missing_problems_are_hidden(client, ws):
    for pid in (ws["draft_only"], 999_999):
        g, p = get(client, ws, problem=pid), save(client, ws, problem=pid)
        assert g.status_code == 404 and p.status_code == 404
        assert g.json()["message"] == "Problem not found." and g.json()["error"]["code"] == "NOT_FOUND"
    assert client.get("/api/problems/99999999999/draft?language=PYTHON", headers=ws["h"]["A"]).status_code == 422
    assert get(client, ws, language="RUBY").status_code == 422


def test_language_must_be_offered_by_problem(client, ws):
    res = save(client, ws, problem=ws["python_only"], language="CPP")
    assert res.status_code == 400
    assert save(client, ws, problem=ws["python_only"], language="PYTHON").status_code == 200
    detail = client.get("/api/problems/python-only", headers=ws["h"]["A"]).json()["data"]
    assert detail["languages"] == ["PYTHON"]
    assert client.get("/api/problems/two-sum", headers=ws["h"]["A"]).json()["data"]["languages"] == ["CPP", "JAVA", "PYTHON"]


@pytest.mark.parametrize("who", ["STAFF", "ADMIN"])
def test_only_students_use_drafts(client, ws, who):
    save(client, ws, who="A", source_code="ASHA-SECRET")
    for res in (get(client, ws, who=who), save(client, ws, who=who)):
        assert res.status_code == 403 and "ASHA-SECRET" not in res.text


def test_drafts_require_login(client, ws):
    assert client.get(url(ws["pub"]), params={"language": "PYTHON"}).status_code == 401
    assert client.put(url(ws["pub"]), json={"language": "PYTHON", "source_code": ""}).status_code == 401


def test_deleting_problem_removes_drafts_not_users(client, ws, db_session):
    from app.models.problem import Problem
    from app.models.user import User

    save(client, ws, source_code="x")
    users = db_session.query(User).count()
    db_session.delete(db_session.get(Problem, ws["pub"]))
    db_session.commit()
    assert db_session.query(CodeDraft).count() == 0 and db_session.query(User).count() == users


# ------------------------------------------------------------------ run / submit without a judge
# (Full judging behaviour with a Judge0 test double lives in test_execution.py.)
def test_run_and_submit_without_judge_never_fake_results(client, ws, db_session):
    body = {"problem_id": ws["pub"], "language": "CPP", "source_code": "int main(){}"}
    run = client.post("/api/executions/run", json=body, headers=ws["h"]["A"])
    sub = client.post("/api/submissions", json=body, headers=ws["h"]["A"])
    for res in (run, sub):
        assert res.status_code == 503
        assert res.json()["error"] == {"code": "EXECUTION_UNAVAILABLE", "message": "Code execution service is temporarily unavailable."}
        for word in ("ACCEPTED", "WRONG_ANSWER", "HIDDEN-OUT"):
            assert word not in res.text
    # Nothing stored, nothing solved or attempted.
    assert db_session.query(Submission).count() == 0
    assert client.get("/api/problems/two-sum", headers=ws["h"]["A"]).json()["data"]["user_status"] == "UNSOLVED"
    assert client.get("/api/learning-path", headers=ws["h"]["A"]).json()["data"]["total_solved"] == 0


@pytest.mark.parametrize("path", ["/api/submissions", "/api/executions/run"])
def test_run_submit_validation_and_access(client, ws, path):
    body = {"problem_id": ws["pub"], "language": "PYTHON", "source_code": "pass"}
    assert client.post(path, json=body).status_code == 401
    assert client.post(path, json=body, headers=ws["h"]["STAFF"]).status_code == 403
    assert client.post(path, json=body, headers=ws["h"]["ADMIN"]).status_code == 403
    assert client.post(path, json={**body, "problem_id": ws["draft_only"]}, headers=ws["h"]["A"]).status_code == 404
    assert client.post(path, json={**body, "source_code": "x" * 1_000_001}, headers=ws["h"]["A"]).status_code == 422
    assert client.post(path, json={**body, "user_id": 2}, headers=ws["h"]["A"]).status_code == 422
    assert client.post(path, json={**body, "problem_id": ws["python_only"], "language": "JAVA"}, headers=ws["h"]["A"]).status_code == 400
