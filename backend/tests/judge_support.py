"""Shared Judge0 test-double fixtures for execution and progress tests.

The fake Judge0 never executes code: each test picks the canned outcome
("behaviour") a solution would produce. See tests/fake_judge0.py.
"""

import pytest

from app.core.config import settings
from app.models.user import UserRole
from app.services import execution_service, topic_service
from app.services.judging.judge0 import Judge0Client
from app.utils.rate_limiter import run_rate_limiter, submit_rate_limiter
from tests.conftest import auth_header
from tests.fake_judge0 import FakeJudge0, Outcome

PUBLIC = [("2 3", "5"), ("10 20", "30")]
HIDDEN = [("2000000000 2000000000", "4000000000"), ("-7 7", "0")]
HIDDEN_MARKERS = ("2000000000 2000000000", "4000000000", "-7 7")


# ------------------------------------------------------------------ behaviours (canned outcomes)
def adds_correctly(source, stdin, language_id):
    """Outcome a correct solution would produce (decided by the test, not executed)."""
    a, b = map(int, stdin.split())
    return Outcome(stdout=f"{a + b}\n")


def prints_ten(source, stdin, language_id):
    return Outcome(stdout="10\n")


def overflows_on_hidden(source, stdin, language_id):
    a, b = map(int, stdin.split())
    total = a + b
    if total > 2**31 - 1:  # what a 32-bit int solution would print
        total -= 2**32
    return Outcome(stdout=f"{total}\n")


def compile_error(source, stdin, language_id):
    return Outcome(status_id=6, compile_output="main.cpp:3:5: error: expected ';' before 'return'", time=None, memory=None)


def runtime_error_echoing_input(source, stdin, language_id):
    return Outcome(status_id=11, stderr=f"Traceback: crashed on input {stdin}")


def by_status(status_id, **extra):
    return lambda source, stdin, language_id: Outcome(status_id=status_id, **extra)


# ------------------------------------------------------------------ fixtures
@pytest.fixture()
def judge(monkeypatch):
    holder = {"fake": FakeJudge0(behaviour=adds_correctly)}
    monkeypatch.setattr(settings, "JUDGE0_BASE_URL", "http://judge0.test")
    monkeypatch.setattr(settings, "JUDGE0_TIMEOUT", 5.0)
    monkeypatch.setattr(
        execution_service,
        "get_judge_client",
        lambda: Judge0Client("http://judge0.test", api_key="judge-secret", poll_interval=0, transport=holder["fake"].transport),
    )
    execution_service._health_cache.update(checked_at=0.0, available=False)
    run_rate_limiter.reset()
    submit_rate_limiter.reset()

    def use(behaviour=None, **flags):
        holder["fake"] = FakeJudge0(behaviour=behaviour or adds_correctly, **flags)
        return holder["fake"]

    holder["use"] = use
    return holder


@pytest.fixture()
def env(client, make_user, db_session):
    make_user("asha@college.edu", UserRole.STUDENT, name="Asha")
    make_user("ravi@college.edu", UserRole.STUDENT, name="Ravi")
    make_user("staff@college.edu", UserRole.STAFF)
    make_user("admin@college.edu", UserRole.ADMIN)
    h = {k: auth_header(client, f"{k.lower()}@college.edu") for k in ("ASHA", "RAVI", "STAFF", "ADMIN")}
    topic = topic_service.create_topic(db_session, name="Basics", slug="basics", order_index=1)

    def problem(title, *, published=True, starters=None, tests=None, **extra):
        body = {
            "title": title,
            "description": "Read two integers and print their sum.",
            "difficulty": "EASY",
            "topic_id": topic.id,
            "starter_codes": starters
            if starters is not None
            else [{"language": lang, "starter_code": f"// {lang}"} for lang in ("CPP", "JAVA", "PYTHON")],
            "test_cases": tests
            if tests is not None
            else [{"input_data": i, "expected_output": o, "is_hidden": False} for i, o in PUBLIC]
            + [{"input_data": i, "expected_output": o, "is_hidden": True} for i, o in HIDDEN],
            "is_published": published,
            **extra,
        }
        res = client.post("/api/admin/problems", json=body, headers=h["ADMIN"])
        assert res.status_code == 201, res.text
        return res.json()["data"]

    return {"h": h, "problem": problem, "add": problem("Add Two Numbers", time_limit_ms=1000, memory_limit_kb=65536)}


def run(client, env, who="ASHA", **body):
    data = {"problem_id": env["add"]["id"], "language": "PYTHON", "source_code": "print(sum(map(int, input().split())))", **body}
    return client.post("/api/executions/run", json=data, headers=env["h"][who])


def submit(client, env, who="ASHA", **body):
    data = {"problem_id": env["add"]["id"], "language": "PYTHON", "source_code": "print(sum(map(int, input().split())))", **body}
    return client.post("/api/submissions", json=data, headers=env["h"][who])
