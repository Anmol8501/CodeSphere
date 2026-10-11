"""Phase 5: RUN / SUBMIT through Judge0 (test double), verdicts, hidden-test
protection, failure handling, history, isolation, limits and rate limiting.

The Judge0 double (tests/fake_judge0.py) never executes code; each test tells
it which canned outcome to return. Real execution is covered by
tests/test_judge0_live.py when a real Judge0 is configured.
"""

import base64
from datetime import UTC, datetime, timedelta

import pytest

from app.core.config import settings
from app.core.languages import LANGUAGES
from app.models.problem import ProgrammingLanguage
from app.models.submission import Submission, SubmissionStatus
from app.services import execution_service
from app.services.judging.comparator import normalize_output, outputs_match
from app.services.judging.harness import HarnessError, build_program
from app.services.judging.judge0 import JudgeResult
from app.services.judging.runner import limits_for
from tests.fake_judge0 import Outcome
from tests.judge_support import (  # noqa: F401  (fixtures are used by name)
    HIDDEN,
    HIDDEN_MARKERS,
    PUBLIC,
    adds_correctly,
    by_status,
    compile_error,
    env,
    judge,
    overflows_on_hidden,
    prints_ten,
    run,
    runtime_error_echoing_input,
    submit,
)


# ------------------------------------------------------------------ pure units
@pytest.mark.parametrize(
    "actual, expected, same",
    [
        ("5\n", "5", True),
        ("5\r\n", "5\n", True),
        ("1 2 3   \n4 5\t\n\n\n", "1 2 3\n4 5", True),
        ("  *\n ***\n", "  *\n ***", True),  # leading spaces are meaningful
        ("*\n***", "  *\n ***", False),
        ("1  2", "1 2", False),  # spaces between tokens are kept
        ("a\n\nb", "a\nb", False),  # blank line in the middle is kept
        ("", "", True),
        ("0", "", False),
    ],
)
def test_output_comparison(actual, expected, same):
    assert outputs_match(actual, expected) is same


def test_normalize_output_only_trims_line_ends():
    assert normalize_output("x  \r\ny\r\n\r\n") == "x\ny"
    assert normalize_output(" lead") == " lead"


def test_harness_assembly():
    assert build_program("print(1)", None) == "print(1)"
    program = build_program("class Solution:\n    pass\n\n", "import sys\n{{USER_CODE}}\nprint(Solution)\n")
    assert program == "import sys\nclass Solution:\n    pass\nprint(Solution)\n"
    assert build_program("x = 1", "{{USER_CODE}}tail") == "x = 1\ntail"
    # The student's code is inserted verbatim even if it contains the marker text.
    assert build_program("# {{USER_CODE}}", "A\n{{USER_CODE}}\nB") == "A\n# {{USER_CODE}}\nB"
    with pytest.raises(HarnessError):
        build_program("x", "no marker")


@pytest.mark.parametrize(
    "status_id, memory, stderr, expected",
    [
        (3, 1000, "", None),
        (4, 1000, "", None),
        (5, 1000, "", SubmissionStatus.TIME_LIMIT_EXCEEDED),
        (6, None, "", SubmissionStatus.COMPILE_ERROR),
        (7, 1000, "", SubmissionStatus.RUNTIME_ERROR),
        (8, 1000, "", SubmissionStatus.OUTPUT_LIMIT_EXCEEDED),
        (11, 1000, "", SubmissionStatus.RUNTIME_ERROR),
        (12, 65000, "", SubmissionStatus.MEMORY_LIMIT_EXCEEDED),  # killed near the memory limit
        (11, 2000, "java.lang.OutOfMemoryError: Java heap space", SubmissionStatus.MEMORY_LIMIT_EXCEEDED),
        (13, None, "", SubmissionStatus.SYSTEM_ERROR),
        (14, None, "", SubmissionStatus.SYSTEM_ERROR),
        (99, None, "", SubmissionStatus.SYSTEM_ERROR),
    ],
)
def test_judge0_status_mapping(status_id, memory, stderr, expected):
    result = JudgeResult(status_id=status_id, stdout="", stderr=stderr, compile_output="", message="", time_ms=1, memory_kb=memory)
    assert result.verdict(memory_limit_kb=65536) == expected


def test_language_mapping_and_limits():
    assert {lang: spec.judge0_id for lang, spec in LANGUAGES.items()} == {
        ProgrammingLanguage.CPP: 54, ProgrammingLanguage.JAVA: 62, ProgrammingLanguage.PYTHON: 71,
    }
    cpp = limits_for(LANGUAGES[ProgrammingLanguage.CPP], 1000, 65536, 1024)
    py = limits_for(LANGUAGES[ProgrammingLanguage.PYTHON], 1000, 65536, 1024)
    assert (cpp.cpu_time_s, cpp.memory_kb) == (1.0, 65536) and py.cpu_time_s == 3.0
    huge = limits_for(LANGUAGES[ProgrammingLanguage.JAVA], 10_000, 10**9, 1024)
    assert huge.cpu_time_s == 15.0 and huge.wall_time_s == 20.0 and huge.memory_kb == 512_000


# ------------------------------------------------------------------ RUN
def test_run_accepted_with_public_details(client, env, judge):
    res = run(client, env)
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["verdict"] == "ACCEPTED" and (data["passed_tests"], data["total_tests"]) == (2, 2)
    assert [(r["kind"], r["index"], r["status"]) for r in data["results"]] == [("public", 1, "PASSED"), ("public", 2, "PASSED")]
    first = data["results"][0]
    assert (first["input"], first["expected_output"], first["actual_output"]) == ("2 3", "5", "5\n")
    sent = judge["fake"].submissions
    # RUN sends only public inputs to the judge, never expected outputs.
    assert [s["stdin"] for s in sent] == ["2 3", "10 20"]
    assert all("expected_output" not in s for s in sent)
    assert all(s["language_id"] == 71 and s["enable_network"] is False for s in sent)
    assert sent[0]["cpu_time_limit"] == 3.0 and sent[0]["memory_limit"] == 65536  # problem limit x Python factor
    assert sent[0]["headers"]["x-auth-token"] == "judge-secret"
    assert not any(marker in res.text for marker in HIDDEN_MARKERS)


def test_run_wrong_answer_shows_public_diff(client, env, judge):
    judge["use"](prints_ten)
    data = run(client, env).json()["data"]
    assert data["verdict"] == "WRONG_ANSWER" and data["passed_tests"] == 0
    assert data["results"][0]["actual_output"] == "10\n" and data["results"][0]["expected_output"] == "5"


def test_run_compile_error_stops_after_one_execution(client, env, judge):
    fake = judge["use"](compile_error)
    data = run(client, env, language="CPP", source_code="int main() { return 0 }").json()["data"]
    assert data["verdict"] == "COMPILE_ERROR"
    assert "expected ';'" in data["compile_output"]
    assert len(fake.submissions) == 1 and fake.submissions[0]["language_id"] == 54


@pytest.mark.parametrize(
    "behaviour, verdict",
    [
        (runtime_error_echoing_input, "RUNTIME_ERROR"),
        (by_status(5), "TIME_LIMIT_EXCEEDED"),
        (by_status(12, memory=65536), "MEMORY_LIMIT_EXCEEDED"),
        (by_status(8), "OUTPUT_LIMIT_EXCEEDED"),
    ],
)
def test_run_error_verdicts(client, env, judge, behaviour, verdict):
    judge["use"](behaviour)
    data = run(client, env).json()["data"]
    assert data["verdict"] == verdict and data["passed_tests"] == 0


def test_run_custom_cases_are_not_official(client, env, judge):
    data = run(client, env, custom_cases=[{"input": "4 4", "expected_output": "8"}, {"input": "1 1"}]).json()["data"]
    assert (data["verdict"], data["passed_tests"], data["total_tests"]) == ("ACCEPTED", 2, 2)
    custom = [r for r in data["results"] if r["kind"] == "custom"]
    assert [(r["index"], r["status"], r["actual_output"]) for r in custom] == [(1, "PASSED", "8\n"), (2, "EXECUTED", "2\n")]
    judge["use"](prints_ten)
    data = run(client, env, custom_cases=[{"input": "5 5", "expected_output": "10"}]).json()["data"]
    assert data["verdict"] == "WRONG_ANSWER"  # custom passing never makes the run accepted


# ------------------------------------------------------------------ SUBMIT
def test_submit_accepted_is_stored_and_solves(client, env, judge, db_session):
    res = submit(client, env)
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["status"] == "ACCEPTED" and (data["passed_tests"], data["total_tests"]) == (4, 4)
    assert data["problem"]["slug"] == "add-two-numbers" and data["language"] == "PYTHON"
    assert data["runtime_ms"] == 10 and data["memory_kb"] == 3000 and data["finished_at"]
    row = db_session.get(Submission, data["id"])
    assert row.status == SubmissionStatus.ACCEPTED and row.user_id is not None and row.finished_at is not None
    # All four inputs went to the judge; none of the hidden data comes back.
    assert [s["stdin"] for s in judge["fake"].submissions] == [i for i, _ in PUBLIC + HIDDEN]
    assert not any(marker in res.text for marker in HIDDEN_MARKERS)
    hidden = [r for r in data["results"] if r["kind"] == "hidden"]
    assert len(hidden) == 2 and all(r["input"] is r["expected_output"] is r["actual_output"] is r["stderr"] is None for r in hidden)

    h = env["h"]["ASHA"]
    assert client.get("/api/problems/add-two-numbers", headers=h).json()["data"]["user_status"] == "SOLVED"
    stats = client.get("/api/student/dashboard", headers=h).json()["data"]
    assert stats["statistics"]["problems_solved"] == 1 and stats["statistics"]["acceptance_rate"] == 100
    assert stats["statistics"]["current_streak"] == 1 and stats["statistics"]["total_attempts"] == 1
    heatmap = client.get("/api/progress/heatmap", headers=h).json()["data"]
    assert heatmap["total_submissions"] == 1 and heatmap["days"][-1]["submission_count"] == 1


def test_submit_passes_public_fails_hidden_without_leaking(client, env, judge):
    judge["use"](overflows_on_hidden)
    res = submit(client, env, language="CPP", source_code="int main(){int a,b;std::cin>>a>>b;std::cout<<a+b;}")
    data = res.json()["data"]
    assert data["status"] == "WRONG_ANSWER" and data["passed_tests"] == 2
    failed = data["results"][-1]
    # Official tests are numbered by position: two public tests, then hidden test 3.
    assert (failed["kind"], failed["index"], failed["status"]) == ("hidden", 3, "FAILED")
    assert failed["input"] is None and failed["expected_output"] is None and failed["actual_output"] is None
    assert data["error_message"] is None
    assert not any(marker in res.text for marker in HIDDEN_MARKERS + ("-294967296",))
    # Stopped at the first failure: the second hidden test was never executed.
    assert len(judge["fake"].submissions) == 3


def test_hidden_runtime_error_never_returns_stderr(client, env, judge):
    judge["use"](lambda s, stdin, lang: adds_correctly(s, stdin, lang) if stdin in dict(PUBLIC) else runtime_error_echoing_input(s, stdin, lang))
    res = submit(client, env)
    data = res.json()["data"]
    assert data["status"] == "RUNTIME_ERROR"
    assert data["error_message"] == execution_service.HIDDEN_RUNTIME_MESSAGE
    assert "crashed on input" not in res.text and not any(m in res.text for m in HIDDEN_MARKERS)
    detail = client.get(f"/api/submissions/{data['id']}", headers=env["h"]["ASHA"])
    assert "crashed on input" not in detail.text and not any(m in detail.text for m in HIDDEN_MARKERS)


def test_public_runtime_error_shows_stderr(client, env, judge):
    judge["use"](runtime_error_echoing_input)
    data = submit(client, env).json()["data"]
    assert data["status"] == "RUNTIME_ERROR" and "crashed on input 2 3" in data["error_message"]


def test_submit_compile_error_message(client, env, judge):
    judge["use"](compile_error)
    data = submit(client, env, language="CPP", source_code="int main() { return 0 }").json()["data"]
    assert data["status"] == "COMPILE_ERROR" and data["passed_tests"] == 0 and "expected ';'" in data["error_message"]


@pytest.mark.parametrize(
    "flags, status",
    [({"down": True}, "SYSTEM_ERROR"), ({"http_status": 503}, "SYSTEM_ERROR"), ({"http_status": 401}, "SYSTEM_ERROR")],
)
def test_judge_failures_are_system_errors_not_wrong_answers(client, env, judge, flags, status):
    judge["use"](**flags)
    sub = submit(client, env).json()["data"]
    assert sub["status"] == status and sub["error_message"] == "Code execution service is temporarily unavailable."
    run_data = run(client, env).json()["data"]
    assert run_data["verdict"] == status and run_data["message"] == "Code execution service is temporarily unavailable."
    # An infrastructure failure is neither "solved" nor "attempted".
    assert client.get("/api/problems/add-two-numbers", headers=env["h"]["ASHA"]).json()["data"]["user_status"] == "UNSOLVED"


def test_judge_internal_error_is_system_error(client, env, judge):
    judge["use"](by_status(13))
    assert submit(client, env).json()["data"]["status"] == "SYSTEM_ERROR"


def test_judge_that_never_finishes_times_out(client, env, judge, monkeypatch, db_session):
    monkeypatch.setattr(settings, "JUDGE0_TIMEOUT", 0.05)
    judge["use"](never_finishes=True)
    data = submit(client, env).json()["data"]
    assert data["status"] == "EXECUTION_TIMEOUT"
    assert db_session.query(Submission).filter(Submission.status.in_(["PENDING", "RUNNING"])).count() == 0
    assert run(client, env).json()["data"]["verdict"] == "EXECUTION_TIMEOUT"


def test_not_configured_is_503_and_nothing_stored(client, env, monkeypatch, db_session):
    monkeypatch.setattr(settings, "JUDGE0_BASE_URL", None)
    for res in (run(client, env), submit(client, env)):
        assert res.status_code == 503 and res.json()["error"]["code"] == "EXECUTION_UNAVAILABLE"
    assert db_session.query(Submission).count() == 0


def test_stuck_submissions_are_resolved(client, env, judge, db_session):
    from app.models.user import User

    asha = db_session.query(User).filter_by(email="asha@college.edu").one()
    old = Submission(user_id=asha.id, problem_id=env["add"]["id"], language="PYTHON", source_code="x",
                     status=SubmissionStatus.RUNNING,
                     submitted_at=datetime.now(UTC) - timedelta(seconds=settings.JUDGE0_TIMEOUT + 120))
    db_session.add(old)
    db_session.commit()
    items = client.get("/api/submissions", headers=env["h"]["ASHA"]).json()["data"]["items"]
    assert items[0]["status"] == "EXECUTION_TIMEOUT"
    db_session.refresh(old)
    assert old.finished_at is not None


# ------------------------------------------------------------------ validation
@pytest.mark.parametrize("language", ["javascript", "rust", "random", None, "", "C"])
def test_unsupported_language_is_400(client, env, judge, language):
    for res in (run(client, env, language=language), submit(client, env, language=language)):
        assert res.status_code == 400 and res.json()["error"]["code"] == "INVALID_LANGUAGE"
    assert judge["fake"].submissions == []


def test_language_is_case_insensitive(client, env, judge):
    assert run(client, env, language="python").json()["data"]["verdict"] == "ACCEPTED"


def test_problem_language_restriction_enforced(client, env, judge):
    py_only = env["problem"]("Python Only", starters=[{"language": "PYTHON", "starter_code": "# py"}])
    res = run(client, env, problem_id=py_only["id"], language="JAVA")
    assert res.status_code == 400 and res.json()["error"]["code"] == "LANGUAGE_NOT_AVAILABLE"
    assert submit(client, env, problem_id=py_only["id"], language="CPP").status_code == 400


@pytest.mark.parametrize(
    "field",
    [{"status": "ACCEPTED"}, {"passed": True}, {"accepted": True}, {"score": 100}, {"runtime_ms": 1},
     {"time_limit_ms": 99999}, {"memory_limit_kb": 1}, {"user_id": 2}, {"stdin": "x"}],
)
def test_client_cannot_send_verdicts_or_limits(client, env, judge, field):
    assert run(client, env, **field).status_code == 422
    assert submit(client, env, **field).status_code == 422
    assert judge["fake"].submissions == []


def test_source_size_and_empty_source(client, env, judge, monkeypatch):
    monkeypatch.setattr(settings, "EXECUTION_MAX_SOURCE_BYTES", 1000)
    res = submit(client, env, source_code="#" * 1001)
    assert res.status_code == 413 and res.json()["error"]["code"] == "SOURCE_TOO_LARGE"
    res = run(client, env, source_code="   \n")
    assert res.status_code == 400 and res.json()["error"]["code"] == "EMPTY_SOURCE"
    assert judge["fake"].submissions == []


def test_unpublished_and_testless_problems(client, env, judge):
    draft = env["problem"]("Secret Draft", published=False)
    for res in (run(client, env, problem_id=draft["id"]), submit(client, env, problem_id=draft["id"])):
        assert res.status_code == 404 and res.json()["message"] == "Problem not found."
    empty = env["problem"]("No Tests", tests=[])
    res = submit(client, env, problem_id=empty["id"])
    assert res.status_code == 400 and res.json()["error"]["code"] == "NO_TEST_CASES"
    assert run(client, env, problem_id=empty["id"], custom_cases=[{"input": "1 2"}]).status_code == 200


# ------------------------------------------------------------------ access control
@pytest.mark.parametrize("who", ["STAFF", "ADMIN"])
def test_only_students_execute(client, env, judge, who):
    assert run(client, env, who=who).status_code == 403
    assert submit(client, env, who=who).status_code == 403
    assert client.get("/api/submissions", headers=env["h"][who]).status_code == 403
    assert judge["fake"].submissions == []


def test_execution_requires_login(client, env, judge):
    body = {"problem_id": env["add"]["id"], "language": "PYTHON", "source_code": "x"}
    assert client.post("/api/executions/run", json=body).status_code == 401
    assert client.post("/api/submissions", json=body).status_code == 401
    assert client.get("/api/submissions").status_code == 401
    assert client.get("/api/submissions/1").status_code == 401


def test_submissions_are_private(client, env, judge):
    mine = submit(client, env, source_code="print('ASHA-PRIVATE-CODE')").json()["data"]
    ravi = env["h"]["RAVI"]
    res = client.get(f"/api/submissions/{mine['id']}", headers=ravi)
    assert res.status_code == 404 and "ASHA-PRIVATE-CODE" not in res.text
    assert client.get("/api/submissions", headers=ravi).json()["data"]["total"] == 0
    for path in ("/api/problems/add-two-numbers", "/api/problems", "/api/learning-path"):
        assert "ASHA-PRIVATE-CODE" not in client.get(path, headers=ravi).text
    own = client.get(f"/api/submissions/{mine['id']}", headers=env["h"]["ASHA"]).json()["data"]
    assert own["source_code"] == "print('ASHA-PRIVATE-CODE')"


def test_history_filters_and_pagination(client, env, judge):
    submit(client, env)
    judge["use"](prints_ten)
    submit(client, env, language="CPP", source_code="int main(){}")
    h = env["h"]["ASHA"]
    def get(q):
        return client.get(f"/api/submissions?{q}", headers=h).json()["data"]

    assert [s["status"] for s in get("")["items"]] == ["WRONG_ANSWER", "ACCEPTED"]  # newest first
    assert [s["language"] for s in get("language=CPP")["items"]] == ["CPP"]
    assert [s["status"] for s in get("status=ACCEPTED")["items"]] == ["ACCEPTED"]
    assert get("problem=add-two-numbers")["total"] == 2 and get("problem=other")["total"] == 0
    page = get("page=2&page_size=1")
    assert page["total_pages"] == 2 and [s["status"] for s in page["items"]] == ["ACCEPTED"]
    assert client.get("/api/submissions?status=BOGUS", headers=h).status_code == 422
    assert client.get("/api/submissions/99999999999", headers=h).status_code == 422


# ------------------------------------------------------------------ abuse protection
def test_rate_limits(client, env, judge, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    codes = [run(client, env).status_code for _ in range(settings.RUN_RATE_LIMIT_PER_MINUTE + 1)]
    assert codes[:-1] == [200] * settings.RUN_RATE_LIMIT_PER_MINUTE
    last = run(client, env)
    assert last.status_code == 429 and last.json()["error"]["code"] == "RATE_LIMITED"
    sub_codes = [submit(client, env).status_code for _ in range(settings.SUBMIT_RATE_LIMIT_PER_MINUTE + 1)]
    assert sub_codes[-1] == 429 and sub_codes[:-1] == [200] * settings.SUBMIT_RATE_LIMIT_PER_MINUTE
    # Limits are per student.
    assert run(client, env, who="RAVI").status_code == 200


def test_duplicate_submission_while_judging_is_rejected(client, env, judge, db_session):
    from app.models.user import User

    asha = db_session.query(User).filter_by(email="asha@college.edu").one()
    execution_service._active.add(("submission", asha.id))
    try:
        res = submit(client, env)
        assert res.status_code == 409 and res.json()["error"]["code"] == "SUBMISSION_IN_PROGRESS"
    finally:
        execution_service._active.discard(("submission", asha.id))
    db_session.add(Submission(user_id=asha.id, problem_id=env["add"]["id"], language="PYTHON", source_code="x",
                              status=SubmissionStatus.RUNNING))
    db_session.commit()
    res = submit(client, env)
    assert res.status_code == 409
    assert db_session.query(Submission).count() == 1 and judge["fake"].submissions == []


# ------------------------------------------------------------------ harness + limits from the problem
def test_function_style_problem_uses_hidden_driver(client, env, judge):
    driver = "import sys\n{{USER_CODE}}\na, b = map(int, sys.stdin.read().split())\nprint(Solution().add(a, b))\n"
    p = env["problem"](
        "Add Function",
        starters=[{"language": "PYTHON", "starter_code": "class Solution:\n    def add(self, a, b):\n        pass", "driver_code": driver}],
        time_limit_ms=500,
    )
    student = client.get("/api/problems/add-function", headers=env["h"]["ASHA"])
    assert "driver_code" not in student.text and "sys.stdin.read" not in student.text
    admin = client.get(f"/api/admin/problems/{p['id']}", headers=env["h"]["ADMIN"]).json()["data"]
    assert admin["starter_codes"][0]["driver_code"] == driver and admin["time_limit_ms"] == 500
    run(client, env, problem_id=p["id"], source_code="class Solution:\n    def add(self, a, b):\n        return a + b\n")
    sent = judge["fake"].submissions[0]
    assert sent["source_code"].startswith("import sys\nclass Solution:") and "print(Solution().add(a, b))" in sent["source_code"]
    assert sent["cpu_time_limit"] == 1.5  # 500 ms x Python factor 3


def test_admin_driver_validation(client, env):
    res = client.post("/api/admin/problems", json={
        "title": "Bad Driver", "description": "Driver without the marker.", "difficulty": "EASY",
        "topic_id": env["add"]["topic"]["id"],
        "starter_codes": [{"language": "PYTHON", "starter_code": "x", "driver_code": "print(1)"}],
    }, headers=env["h"]["ADMIN"])
    assert res.status_code == 422 and "{{USER_CODE}}" in res.json()["message"]
    res = client.post("/api/admin/problems", json={
        "title": "Bad Limits", "description": "Limits out of range.", "difficulty": "EASY",
        "topic_id": env["add"]["topic"]["id"], "time_limit_ms": 50,
    }, headers=env["h"]["ADMIN"])
    assert res.status_code == 422


def test_student_problem_detail_shows_limits(client, env):
    data = client.get("/api/problems/add-two-numbers", headers=env["h"]["ASHA"]).json()["data"]
    assert (data["time_limit_ms"], data["memory_limit_kb"]) == (1000, 65536)


# ------------------------------------------------------------------ health / admin status
def test_execution_health(client, env, judge, monkeypatch):
    assert client.get("/api/health/execution").json()["data"] == {"available": True}
    judge["use"](down=True)
    execution_service._health_cache.update(checked_at=0.0)
    body = client.get("/api/health/execution").json()
    assert body["data"] == {"available": False} and "judge0.test" not in str(body)
    monkeypatch.setattr(settings, "JUDGE0_BASE_URL", None)
    assert client.get("/api/health/execution").json()["data"] == {"available": False}


def test_admin_dashboard_judge_status(client, env, judge, monkeypatch):
    def status():
        return {s["key"]: s["status"] for s in client.get("/api/admin/dashboard", headers=env["h"]["ADMIN"]).json()["data"]["system_status"]}["judge"]
    assert status() == "online"
    judge["use"](down=True)
    execution_service._health_cache.update(checked_at=0.0)
    assert status() == "offline"
    monkeypatch.setattr(settings, "JUDGE0_BASE_URL", None)
    assert status() == "not_connected"


def test_base64_roundtrip_unicode(client, env, judge):
    judge["use"](lambda s, stdin, lang: Outcome(stdout="héllo ✓ 世界\n"))
    data = run(client, env, custom_cases=[{"input": "ünïcødé ✓", "expected_output": "héllo ✓ 世界"}]).json()["data"]
    custom = [r for r in data["results"] if r["kind"] == "custom"][0]
    assert custom["status"] == "PASSED" and custom["input"] == "ünïcødé ✓"
    assert judge["fake"].submissions[-1]["stdin"] == "ünïcødé ✓"
    assert base64.b64decode(base64.b64encode("✓".encode())).decode() == "✓"
