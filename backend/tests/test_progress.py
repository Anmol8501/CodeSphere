"""Phase 6: progress, solved state, statistics, streaks, heatmap, activity,
leaderboard, staff analytics, history filters and their security.

Two ways of creating submissions are used:
  * through the API with the Judge0 test double (the real SUBMIT path), and
  * `record()`, which stores a judged submission and applies the exact same
    progress update the SUBMIT path uses (for dates, volumes and edge cases).
"""

import random
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.clock import local_today, start_of_day_utc
from app.models.problem import Problem, ProblemDifficulty, ProblemStatus, ProgrammingLanguage, TestCase
from app.models.progress import UserProblemProgress
from app.models.submission import Submission, SubmissionStatus, SubmissionTestResult
from app.models.user import UserRole
from app.services import progress_service, topic_service
from app.services.progress_service import compute_streaks
from tests.conftest import auth_header
from tests.judge_support import (  # noqa: F401  (fixtures are used by name)
    HIDDEN_MARKERS,
    adds_correctly,
    compile_error,
    env,
    judge,
    overflows_on_hidden,
    prints_ten,
    run,
    submit,
)

AC = SubmissionStatus.ACCEPTED
WA = SubmissionStatus.WRONG_ANSWER
TODAY = local_today()


def noon(day: date) -> datetime:
    """Midday of a calendar day in the application timezone, as UTC."""
    return start_of_day_utc(day) + timedelta(hours=12)


# ------------------------------------------------------------------ world (direct data)
@pytest.fixture()
def world(client, make_user, db_session):
    students = {
        name: make_user(f"{name.lower()}@college.edu", UserRole.STUDENT, name=name)
        for name in ("Asha", "Ravi", "Meena", "Kiran")
    }
    staff = make_user("prof@college.edu", UserRole.STAFF, name="Prof")
    admin = make_user("root@college.edu", UserRole.ADMIN, name="Root")
    topics = {
        slug: topic_service.create_topic(db_session, name=slug.title(), slug=slug, order_index=i)
        for i, slug in enumerate(("arrays", "strings", "graphs"), start=1)
    }

    def problem(title, difficulty="EASY", topic="arrays", status=ProblemStatus.PUBLISHED):
        p = Problem(
            title=title,
            slug=title.lower().replace(" ", "-"),
            description="Original practice problem.",
            difficulty=ProblemDifficulty(difficulty),
            topic_id=topics[topic].id,
            status=status,
        )
        p.test_cases = [
            TestCase(input_data="1", expected_output="1", is_hidden=False, order_index=0),
            TestCase(input_data="SECRET-IN", expected_output="SECRET-OUT", is_hidden=True, order_index=1),
        ]
        db_session.add(p)
        db_session.commit()
        return p

    def record(user, prob, status=AC, at=None, runtime=10, memory=3000, language=ProgrammingLanguage.PYTHON):
        submission = Submission(
            user_id=user.id, problem_id=prob.id, language=language, source_code="code", status=status,
            runtime_ms=runtime, memory_kb=memory, submitted_at=at or datetime.now(UTC),
        )
        db_session.add(submission)
        db_session.flush()
        progress_service.record_judged_submission(db_session, submission)
        db_session.commit()
        return submission

    def headers(user):
        return auth_header(client, user.email)

    return {"students": students, "staff": staff, "admin": admin, "topics": topics, "problem": problem,
            "record": record, "headers": headers}


def get(client, path, headers):
    res = client.get(path, headers=headers)
    assert res.status_code == 200, (path, res.status_code, res.text)
    return res.json()["data"]


# ================================================================== solved state / attempts (real SUBMIT path)
def test_wrong_then_accepted_then_accepted_again(client, env, judge, db_session):
    h = env["h"]["ASHA"]
    slug = env["add"]["slug"]

    judge["use"](prints_ten)
    assert submit(client, env).json()["data"]["status"] == "WRONG_ANSWER"
    progress = get(client, f"/api/problems/{slug}", h)["progress"]
    assert (progress["status"], progress["attempts"], progress["accepted_submissions"]) == ("ATTEMPTED", 1, 0)
    assert get(client, "/api/progress/overview", h)["solved_problems"] == 0

    judge["use"](adds_correctly)
    first = submit(client, env).json()["data"]
    assert first["status"] == "ACCEPTED" and first["is_first_accepted"] is True
    progress = get(client, f"/api/problems/{slug}", h)["progress"]
    assert (progress["status"], progress["attempts"], progress["accepted_submissions"]) == ("SOLVED", 2, 1)
    assert progress["solved_at"] and progress["best_runtime_ms"] == 10

    again = submit(client, env).json()["data"]
    assert again["status"] == "ACCEPTED" and again["is_first_accepted"] is False
    overview = get(client, "/api/progress/overview", h)
    assert overview["solved_problems"] == 1  # the same problem is never counted twice
    assert (overview["total_submissions"], overview["accepted_submissions"]) == (3, 2)
    assert overview["acceptance_rate"] == 66.7
    row = db_session.query(UserProblemProgress).one()
    assert (row.attempt_count, row.accepted_count) == (3, 2)
    assert progress_service.audit_progress(db_session) == []


def test_run_never_counts_as_an_attempt(client, env, judge, db_session):
    assert run(client, env).json()["data"]["verdict"] == "ACCEPTED"
    assert db_session.query(UserProblemProgress).count() == 0 and db_session.query(Submission).count() == 0
    overview = get(client, "/api/progress/overview", env["h"]["ASHA"])
    assert (overview["solved_problems"], overview["total_submissions"]) == (0, 0)
    assert get(client, f"/api/problems/{env['add']['slug']}", env["h"]["ASHA"])["user_status"] == "UNSOLVED"


def test_judge_failure_is_not_an_attempt(client, env, judge, db_session):
    judge["use"](down=True)
    data = submit(client, env).json()["data"]
    assert data["status"] == "SYSTEM_ERROR"
    h = env["h"]["ASHA"]
    assert get(client, "/api/progress/overview", h)["total_submissions"] == 0
    assert get(client, "/api/progress/streak", h)["current_streak"] == 0
    assert get(client, "/api/progress/activity", h) == []
    assert db_session.query(UserProblemProgress).count() == 0


def test_per_test_results_are_stored_without_hidden_data(client, env, judge, db_session):
    judge["use"](overflows_on_hidden)
    res = submit(client, env, language="CPP", source_code="int main(){}")
    data = res.json()["data"]
    rows = db_session.query(SubmissionTestResult).filter_by(submission_id=data["id"]).order_by(SubmissionTestResult.position).all()
    assert [(r.position, r.is_hidden, r.status.value) for r in rows] == [(1, False, "PASSED"), (2, False, "PASSED"), (3, True, "FAILED")]
    assert all(r.test_case_id is not None for r in rows)
    hidden = rows[2]
    assert hidden.input_data is hidden.expected_output is hidden.actual_output is hidden.error_message is None
    assert rows[0].input_data == "2 3" and rows[0].expected_output == "5" and rows[0].actual_output == "5\n"

    detail = get(client, f"/api/submissions/{data['id']}", env["h"]["ASHA"])
    assert detail["not_run_tests"] == 1  # judging stopped at the first failure
    assert detail["results"][2] == {"index": 3, "kind": "hidden", "status": "FAILED", "runtime_ms": 10, "memory_kb": 3000,
                                    "input": None, "expected_output": None, "actual_output": None, "stderr": None}
    assert (detail["time_limit_ms"], detail["memory_limit_kb"]) == (1000, 65536)  # C++ time factor 1
    text = client.get(f"/api/submissions/{data['id']}", headers=env["h"]["ASHA"]).text
    assert not any(m in text for m in HIDDEN_MARKERS)


def test_compile_error_stores_no_test_rows(client, env, judge, db_session):
    judge["use"](compile_error)
    data = submit(client, env).json()["data"]
    assert data["status"] == "COMPILE_ERROR" and data["results"] == [] and data["not_run_tests"] == 0
    assert "expected ';'" in data["error_message"]
    assert db_session.query(SubmissionTestResult).count() == 0
    # A compile error is still a judged attempt.
    assert get(client, "/api/progress/overview", env["h"]["ASHA"])["total_submissions"] == 1


def test_time_limit_is_scaled_for_the_language(client, env, judge):
    data = submit(client, env, language="PYTHON").json()["data"]
    assert (data["time_limit_ms"], data["memory_limit_kb"]) == (3000, 65536)  # 1000 ms x Python factor 3


def test_client_cannot_send_progress_or_verdict_fields(client, env, judge, db_session):
    for field, value in [("status", "ACCEPTED"), ("passed", True), ("runtime_ms", 1), ("memory_kb", 1),
                         ("is_first_accepted", True), ("attempt_count", 99), ("solved", True), ("user_id", 2)]:
        res = submit(client, env, **{field: value})
        assert res.status_code == 422, field
    assert db_session.query(Submission).count() == 0


# ================================================================== best runtime / memory, first accepted
def test_best_runtime_and_memory_use_valid_accepted_submissions(world, db_session, client):
    asha, p = world["students"]["Asha"], world["problem"]("Two Sum")
    rec = world["record"]
    rec(asha, p, WA, runtime=1, memory=1)  # wrong answers never count as "best"
    rec(asha, p, AC, runtime=100, memory=5000)
    rec(asha, p, AC, runtime=80, memory=7000)
    rec(asha, p, AC, runtime=120, memory=4000)
    rec(asha, p, AC, runtime=None, memory=-5)  # malformed values are ignored
    progress = get(client, "/api/problems/two-sum", world["headers"](asha))["progress"]
    assert (progress["best_runtime_ms"], progress["best_memory_kb"]) == (80, 4000)
    assert (progress["attempts"], progress["accepted_submissions"]) == (5, 4)
    firsts = db_session.query(Submission).filter_by(is_first_accepted=True).all()
    assert len(firsts) == 1 and firsts[0].runtime_ms == 100


def test_only_one_first_accepted_per_student_and_problem(world, db_session):
    asha, p = world["students"]["Asha"], world["problem"]("Two Sum")
    world["record"](asha, p, AC)
    db_session.add(Submission(user_id=asha.id, problem_id=p.id, language=ProgrammingLanguage.CPP, source_code="x",
                              status=AC, is_first_accepted=True))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_percentiles_need_enough_real_data(world, db_session, client, make_user):
    p = world["problem"]("Two Sum")
    me = world["students"]["Asha"]
    mine = world["record"](me, p, AC, runtime=50, memory=4000)
    detail = get(client, f"/api/submissions/{mine.id}", world["headers"](me))
    assert detail["performance"]["runtime_percentile"] is None and detail["performance"]["min_sample"] == 10

    others = [make_user(f"peer{i}@college.edu", UserRole.STUDENT, name=f"Peer {i}") for i in range(10)]
    for i, peer in enumerate(others):  # runtimes 10, 20, ... 100: six of them slower than 50
        world["record"](peer, p, AC, runtime=(i + 1) * 10, memory=3000 + i * 300)
    world["record"](others[0], p, AC, runtime=500)  # a peer's slower retry does not change its best
    world["record"](others[1], p, AC, runtime=60, language=ProgrammingLanguage.CPP)  # other languages excluded
    perf = get(client, f"/api/submissions/{mine.id}", world["headers"](me))["performance"]
    assert perf["compared_with"] == 10 and perf["runtime_percentile"] == 50.0
    # Memory 4000 KB: peers 3000..5700 -> 3000, 3300, 3600, 3900 are lower, 6 are heavier.
    assert perf["memory_percentile"] == 60.0
    wrong = world["record"](me, p, WA)
    assert get(client, f"/api/submissions/{wrong.id}", world["headers"](me))["performance"] is None


# ================================================================== progress by difficulty / topic
def test_difficulty_progress(world, client):
    asha = world["students"]["Asha"]
    probs = {d: [world["problem"](f"{d} {i}", difficulty=d) for i in range(5)] for d in ("EASY", "MEDIUM", "HARD")}
    world["problem"]("Draft Easy", difficulty="EASY", status=ProblemStatus.DRAFT)  # never counted
    for p in probs["EASY"][:3] + probs["MEDIUM"][:2]:
        world["record"](asha, p, AC)
    world["record"](asha, probs["HARD"][0], WA)
    data = get(client, "/api/progress/difficulty", world["headers"](asha))
    assert data == {
        "easy": {"total": 5, "solved": 3, "percentage": 60.0},
        "medium": {"total": 5, "solved": 2, "percentage": 40.0},
        "hard": {"total": 5, "solved": 0, "percentage": 0.0},
    }


def test_topic_progress(world, client):
    asha = world["students"]["Asha"]
    arrays = [world["problem"](f"Array {i}") for i in range(10)]
    world["problem"]("String 1", topic="strings")
    for p in arrays[:4]:
        world["record"](asha, p, AC)
    world["record"](asha, arrays[5], WA)
    topics = {t["topic"]["slug"]: t for t in get(client, "/api/progress/topics", world["headers"](asha))}
    assert (topics["arrays"]["solved_problems"], topics["arrays"]["total_problems"], topics["arrays"]["percentage"]) == (4, 10, 40.0)
    assert topics["arrays"]["attempted_problems"] == 1
    assert (topics["strings"]["solved_problems"], topics["strings"]["total_problems"]) == (0, 1)
    assert (topics["graphs"]["total_problems"], topics["graphs"]["percentage"]) == (0, 0.0)
    # The learning path agrees with the progress API.
    arrays_topic = get(client, "/api/topics/arrays", world["headers"](asha))
    assert (arrays_topic["solved_count"], arrays_topic["progress"]) == (4, 40)


def test_overview_and_language_stats(world, client):
    asha = world["students"]["Asha"]
    a, b, c = world["problem"]("A"), world["problem"]("B"), world["problem"]("C")
    world["record"](asha, a, WA, language=ProgrammingLanguage.CPP)
    world["record"](asha, a, AC, language=ProgrammingLanguage.CPP)
    world["record"](asha, b, WA, language=ProgrammingLanguage.JAVA)
    world["record"](asha, b, SubmissionStatus.SYSTEM_ERROR)  # judge failure: ignored everywhere
    overview = get(client, "/api/progress/overview", world["headers"](asha))
    assert overview == {"total_problems": 3, "solved_problems": 1, "attempted_problems": 1, "total_submissions": 3,
                        "accepted_submissions": 1, "acceptance_rate": 33.3}
    langs = {row["language"]: row for row in get(client, "/api/progress/languages", world["headers"](asha))}
    assert (langs["CPP"]["submissions"], langs["CPP"]["accepted"], langs["CPP"]["acceptance_rate"]) == (2, 1, 50.0)
    assert (langs["JAVA"]["submissions"], langs["JAVA"]["acceptance_rate"]) == (1, 0.0)
    assert (langs["PYTHON"]["submissions"], langs["PYTHON"]["acceptance_rate"]) == (0, None)
    assert c.id  # untouched problem: counted only in the total


# ================================================================== streaks
D = date


@pytest.mark.parametrize(
    "days, today, expected",
    [
        ([D(2026, 10, 10)], D(2026, 10, 10), (1, 1, True)),
        ([D(2026, 10, 9), D(2026, 10, 10)], D(2026, 10, 10), (2, 2, True)),
        ([D(2026, 10, d) for d in range(6, 11)], D(2026, 10, 10), (5, 5, True)),
        # No submission yet today: the streak ending yesterday is still alive.
        ([D(2026, 10, d) for d in range(5, 10)], D(2026, 10, 10), (5, 5, False)),
        # A missing day breaks the run.
        ([D(2026, 10, 6), D(2026, 10, 7), D(2026, 10, 9), D(2026, 10, 10)], D(2026, 10, 10), (2, 2, True)),
        # Two days without a submission: current streak is 0, the longest is kept.
        ([D(2026, 10, 1), D(2026, 10, 2), D(2026, 10, 3)], D(2026, 10, 10), (0, 3, False)),
        # Month boundary (30-day month) and leap-year February.
        ([D(2026, 9, 29), D(2026, 9, 30), D(2026, 10, 1), D(2026, 10, 2)], D(2026, 10, 2), (4, 4, True)),
        ([D(2028, 2, 28), D(2028, 2, 29), D(2028, 3, 1)], D(2028, 3, 1), (3, 3, True)),
        # Year boundary.
        ([D(2026, 12, 30), D(2026, 12, 31), D(2027, 1, 1), D(2027, 1, 2)], D(2027, 1, 2), (4, 4, True)),
        ([], D(2026, 10, 10), (0, 0, False)),
    ],
)
def test_streak_rules(days, today, expected):
    assert compute_streaks(set(days), today) == expected


def test_streak_api_counts_calendar_days_in_app_timezone(world, client):
    asha, p = world["students"]["Asha"], world["problem"]("Two Sum")
    # One minute after local midnight today is still "yesterday" in UTC for
    # timezones ahead of UTC: it must count as TODAY.
    world["record"](asha, p, WA, at=start_of_day_utc(TODAY) + timedelta(minutes=1))
    world["record"](asha, p, WA, at=noon(TODAY - timedelta(days=1)))
    for back in (10, 11, 12):  # an older 3-day run
        world["record"](asha, p, AC, at=noon(TODAY - timedelta(days=back)))
    streak = get(client, "/api/progress/streak", world["headers"](asha))
    assert (streak["current_streak"], streak["longest_streak"], streak["active_today"]) == (2, 3, True)
    assert streak["last_active_date"] == TODAY.isoformat() and streak["timezone"] == "Asia/Kolkata"
    assert len(streak["activity_dates"]) == 5 and streak["activity_dates"] == sorted(streak["activity_dates"])


def test_heatmap_groups_by_day(world, client):
    asha, p = world["students"]["Asha"], world["problem"]("Two Sum")
    for _ in range(3):
        world["record"](asha, p, WA, at=noon(TODAY))
    world["record"](asha, p, AC, at=noon(TODAY - timedelta(days=2)))
    world["record"](asha, p, SubmissionStatus.SYSTEM_ERROR, at=noon(TODAY - timedelta(days=1)))  # not counted
    world["record"](asha, p, AC, at=noon(TODAY - timedelta(days=400)))  # outside the window
    h = world["headers"](asha)
    data = get(client, "/api/progress/heatmap?days=30", h)
    assert len(data["days"]) == 30 and data["end_date"] == TODAY.isoformat()
    counts = {d["date"]: d["submission_count"] for d in data["days"]}
    assert counts[TODAY.isoformat()] == 3 and counts[(TODAY - timedelta(days=2)).isoformat()] == 1
    assert counts[(TODAY - timedelta(days=1)).isoformat()] == 0
    assert (data["total_submissions"], data["active_days"]) == (4, 2)
    assert len(get(client, "/api/progress/heatmap", h)["days"]) == 365
    for bad in (6, 372, "abc"):
        assert client.get(f"/api/progress/heatmap?days={bad}", headers=h).status_code == 422


# ================================================================== activity / recommendations / problem stats
def test_activity_feed_is_real_and_newest_first(world, client):
    asha, a, b = world["students"]["Asha"], world["problem"]("Two Sum"), world["problem"]("Three Sum")
    world["record"](asha, a, WA, at=noon(TODAY - timedelta(days=3)))
    world["record"](asha, a, AC, at=noon(TODAY - timedelta(days=2)))
    world["record"](asha, a, AC, at=noon(TODAY - timedelta(days=1)))
    world["record"](asha, b, SubmissionStatus.EXECUTION_TIMEOUT, at=noon(TODAY))  # judge problem: hidden
    items = get(client, "/api/progress/activity", world["headers"](asha))
    assert [(i["type"], i["problem"]["slug"]) for i in items] == [
        ("ACCEPTED", "two-sum"), ("SOLVED", "two-sum"), ("ATTEMPTED", "two-sum"),
    ]
    assert items[2]["verdict"] == "WRONG_ANSWER"
    assert len(get(client, "/api/progress/activity?limit=1", world["headers"](asha))) == 1
    assert client.get("/api/progress/activity?limit=51", headers=world["headers"](asha)).status_code == 422


def test_problem_statistics(world, client):
    asha, ravi, p = world["students"]["Asha"], world["students"]["Ravi"], world["problem"]("Two Sum")
    world["record"](asha, p, WA)
    world["record"](asha, p, AC)
    world["record"](ravi, p, WA)
    world["record"](ravi, p, SubmissionStatus.SYSTEM_ERROR)
    h = world["headers"](world["students"]["Meena"])
    expected = {"solved_by": 1, "attempts": 3, "accepted": 1, "acceptance_rate": 33.3}
    assert get(client, "/api/problems/two-sum", h)["stats"] == expected
    assert get(client, "/api/problems", h)["items"][0]["stats"] == expected
    assert get(client, "/api/problems/two-sum", world["headers"](world["staff"]))["progress"] is None


def test_recommendations_follow_real_progress(world, client):
    asha = world["students"]["Asha"]
    a_easy, a_medium = world["problem"]("Arr Easy"), world["problem"]("Arr Medium", difficulty="MEDIUM")
    s_easy = world["problem"]("Str Easy", topic="strings")
    h = world["headers"](asha)

    recs = get(client, "/api/student/dashboard", h)["continue_learning"]
    assert [(r["reason"], r["problem"]["slug"]) for r in recs] == [("START_TOPIC", "arr-easy"), ("START_TOPIC", "str-easy")]

    world["record"](asha, a_easy, AC)
    world["record"](asha, s_easy, WA)
    recs = get(client, "/api/student/dashboard", h)["continue_learning"]
    assert [(r["reason"], r["problem"]["slug"]) for r in recs] == [("RESUME", "str-easy"), ("CONTINUE_TOPIC", "arr-medium")]

    world["record"](asha, a_medium, AC)
    world["record"](asha, s_easy, AC)
    assert get(client, "/api/student/dashboard", h)["continue_learning"] == []


# ================================================================== dashboard consistency (spec 115)
def test_accepted_submission_updates_every_view(client, env, judge, db_session):
    h = env["h"]["ASHA"]
    data = submit(client, env).json()["data"]
    assert db_session.get(Submission, data["id"]).status == SubmissionStatus.ACCEPTED
    problem = get(client, f"/api/problems/{env['add']['slug']}", h)
    assert problem["user_status"] == "SOLVED" and problem["progress"]["attempts"] == 1
    dashboard = get(client, "/api/student/dashboard", h)
    stats = dashboard["statistics"]
    assert (stats["problems_solved"], stats["total_attempts"], stats["accepted_submissions"]) == (1, 1, 1)
    assert (stats["current_streak"], stats["longest_streak"], stats["active_today"]) == (1, 1, True)
    assert dashboard["difficulty"]["easy"] == {"total": 1, "solved": 1, "percentage": 100.0}
    assert get(client, "/api/progress/topics", h)[0]["solved_problems"] == 1
    assert get(client, "/api/progress/activity", h)[0]["type"] == "SOLVED"
    assert get(client, "/api/submissions?limit=5", h)["items"][0]["status"] == "ACCEPTED"
    assert get(client, "/api/problems?status=solved", h)["total"] == 1
    assert progress_service.audit_progress(db_session) == []


def test_new_student_sees_honest_zeros(world, client):
    world["problem"]("Two Sum")
    h = world["headers"](world["students"]["Kiran"])
    stats = get(client, "/api/student/dashboard", h)["statistics"]
    assert stats["problems_solved"] == 0 and stats["total_attempts"] == 0 and stats["acceptance_rate"] == 0
    assert stats["current_streak"] == stats["longest_streak"] == 0 and stats["total_problems"] == 1
    assert get(client, "/api/progress/heatmap?days=7", h)["total_submissions"] == 0
    assert get(client, "/api/progress/activity", h) == []


# ================================================================== leaderboard
def _solve_many(world, user, problems, wrong=0):
    for p in problems:
        world["record"](user, p, AC)
    for _ in range(wrong):
        world["record"](user, problems[0], WA)


def test_leaderboard_ranking_and_ties(world, client, make_user):
    probs = [world["problem"](f"P{i}") for i in range(10)]
    s = world["students"]
    _solve_many(world, s["Asha"], probs[:10])
    _solve_many(world, s["Ravi"], probs[:7])
    _solve_many(world, s["Meena"], probs[:3])
    board = get(client, "/api/leaderboard", world["headers"](s["Ravi"]))
    assert [(e["rank"], e["name"], e["solved"]) for e in board["items"]] == [(1, "Asha", 10), (2, "Ravi", 7), (3, "Meena", 3)]
    assert board["current_user"] == {"rank": 2, "name": "Ravi", "solved": 7, "acceptance_rate": 100.0, "is_current_user": True}
    assert "ranking_rule" in board and board["scope"] == "global"

    # Kiran ties Ravi exactly (7 solved, 100%): shared rank 2, Meena drops to rank 4.
    _solve_many(world, s["Kiran"], probs[:7])
    board = get(client, "/api/leaderboard", world["headers"](s["Asha"]))
    assert [(e["rank"], e["name"]) for e in board["items"]] == [(1, "Asha"), (2, "Ravi"), (2, "Kiran"), (4, "Meena")]
    # Same solved count but a lower acceptance rate ranks below.
    world["record"](s["Kiran"], probs[0], WA)
    board = get(client, "/api/leaderboard", world["headers"](s["Asha"]))
    assert [(e["rank"], e["name"], e["acceptance_rate"]) for e in board["items"]][1:3] == [(2, "Ravi", 100.0), (3, "Kiran", 87.5)]

    # Privacy: only approved public fields.
    text = client.get("/api/leaderboard", headers=world["headers"](s["Asha"])).text
    assert "@college.edu" not in text and "email" not in text and "user_id" not in text


def test_leaderboard_excludes_inactive_and_unsolved_and_paginates(world, client, db_session):
    p = world["problem"]("P")
    s = world["students"]
    world["record"](s["Asha"], p, AC)
    world["record"](s["Ravi"], p, AC)
    world["record"](s["Meena"], p, WA)  # attempted but nothing solved: not ranked
    s["Ravi"].is_active = False
    db_session.commit()
    h = world["headers"](s["Meena"])
    board = get(client, "/api/leaderboard", h)
    assert [e["name"] for e in board["items"]] == ["Asha"] and board["current_user"] is None
    assert get(client, "/api/leaderboard?limit=1&page=2", h)["items"] == []
    assert client.get("/api/leaderboard?limit=101", headers=h).status_code == 422
    assert client.get("/api/leaderboard?scope=classroom", headers=h).status_code == 422
    assert get(client, "/api/leaderboard", world["headers"](world["staff"]))["total"] == 1


# ================================================================== authorization & isolation
STUDENT_ENDPOINTS = [
    "/api/progress/overview", "/api/progress/topics", "/api/progress/difficulty", "/api/progress/languages",
    "/api/progress/activity", "/api/progress/heatmap", "/api/progress/streak", "/api/submissions",
]
STAFF_ENDPOINTS = ["/api/analytics/overview", "/api/analytics/students"]


def test_auth_matrix(world, client):
    student = world["headers"](world["students"]["Asha"])
    staff = world["headers"](world["staff"])
    admin = world["headers"](world["admin"])
    for path in STUDENT_ENDPOINTS + STAFF_ENDPOINTS + ["/api/leaderboard"]:
        res = client.get(path)
        assert res.status_code == 401 and res.json()["error"]["code"] == "UNAUTHORIZED", path
    for path in STUDENT_ENDPOINTS:
        assert client.get(path, headers=student).status_code == 200, path
        for other in (staff, admin):
            res = client.get(path, headers=other)
            assert res.status_code == 403 and res.json()["error"]["code"] == "FORBIDDEN", path
    for path in STAFF_ENDPOINTS:
        assert client.get(path, headers=student).status_code == 403, path
        assert client.get(path, headers=staff).status_code == 200, path
        assert client.get(path, headers=admin).status_code == 200, path
    student_id = world["students"]["Ravi"].id
    assert client.get(f"/api/analytics/students/{student_id}", headers=student).status_code == 403
    assert client.get(f"/api/analytics/students/{student_id}", headers=staff).status_code == 200
    assert client.get(f"/api/analytics/students/{student_id}", headers=admin).status_code == 200


def test_students_only_ever_see_their_own_progress(world, client):
    s = world["students"]
    probs = [world["problem"](f"P{i}") for i in range(5)]
    _solve_many(world, s["Asha"], probs)
    _solve_many(world, s["Ravi"], probs[:2])
    ravi_sub = world["record"](s["Ravi"], probs[0], WA)
    a, r = world["headers"](s["Asha"]), world["headers"](s["Ravi"])
    assert get(client, "/api/progress/overview", a)["solved_problems"] == 5
    assert get(client, "/api/progress/overview", r)["solved_problems"] == 2
    # Query parameters cannot select another user.
    assert get(client, f"/api/progress/overview?user_id={s['Ravi'].id}", a)["solved_problems"] == 5
    assert get(client, f"/api/submissions?user_id={s['Ravi'].id}", a)["total"] == 5
    res = client.get(f"/api/submissions/{ravi_sub.id}", headers=a)
    assert res.status_code == 404 and res.json()["error"]["code"] == "NOT_FOUND"
    assert client.get(f"/api/analytics/students/{s['Ravi'].id}", headers=a).status_code == 403


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_progress_cannot_be_written(world, client, db_session, method):
    h = world["headers"](world["students"]["Asha"])
    body = {"solvedProblems": 99999, "streak": 9999, "solved_problems": 99999, "current_streak": 9999}
    for path in ("/api/progress", "/api/progress/overview", "/api/progress/streak", "/api/leaderboard",
                 "/api/progress/difficulty"):
        res = client.request(method, path, json=body, headers=h)
        assert res.status_code in (404, 405), (method, path, res.status_code)
        assert res.json()["success"] is False and "error" in res.json()
    assert db_session.query(UserProblemProgress).count() == 0
    assert get(client, "/api/progress/overview", h)["solved_problems"] == 0


# ================================================================== history: pagination, filters
def test_history_pagination_limits(world, client):
    asha, p = world["students"]["Asha"], world["problem"]("Two Sum")
    for _ in range(25):
        world["record"](asha, p, WA)
    h = world["headers"](asha)
    assert client.get("/api/submissions?limit=1000000", headers=h).status_code == 422
    assert client.get("/api/submissions?limit=0", headers=h).status_code == 422
    page = get(client, "/api/submissions?limit=10&page=3", h)
    assert (len(page["items"]), page["total"], page["total_pages"], page["page_size"]) == (5, 25, 3, 10)
    assert get(client, "/api/submissions?limit=100", h)["total"] == 25
    assert len(get(client, "/api/submissions?page_size=7", h)["items"]) == 7  # older parameter name still works
    assert len(get(client, "/api/submissions", h)["items"]) == 20


def test_history_filters(world, client):
    asha = world["students"]["Asha"]
    a, b = world["problem"]("Two Sum"), world["problem"]("Binary Search")
    world["record"](asha, a, AC, at=noon(TODAY), language=ProgrammingLanguage.CPP)
    world["record"](asha, a, WA, at=noon(TODAY - timedelta(days=3)))
    world["record"](asha, b, AC, at=noon(TODAY - timedelta(days=20)), language=ProgrammingLanguage.JAVA)
    world["record"](asha, b, WA, at=noon(TODAY - timedelta(days=90)))
    h = world["headers"](asha)

    def total(query):
        return get(client, f"/api/submissions?{query}", h)["total"]

    assert [total(f"period={p}") for p in ("today", "7d", "30d", "all")] == [1, 2, 3, 4]
    assert total(f"problem_id={a.id}") == 2 and total(f"problemId={b.id}") == 2 and total("problem=two-sum") == 2
    assert total("status=ACCEPTED") == 2 and total("language=JAVA") == 1
    assert total("search=binary") == 2 and total("search=SUM") == 2 and total("search=%25") == 0
    assert total("status=ACCEPTED&period=30d&search=two") == 1
    assert client.get("/api/submissions?period=year", headers=h).status_code == 422
    first = get(client, "/api/submissions?limit=1", h)["items"][0]
    assert first["problem"]["slug"] == "two-sum" and first["problem"]["difficulty"] == "EASY"


# ================================================================== consistency: incremental == rebuild
def test_incremental_progress_matches_a_full_rebuild(world, db_session):
    rng = random.Random(6)
    users = list(world["students"].values())
    probs = [world["problem"](f"P{i}", difficulty=rng.choice(["EASY", "MEDIUM", "HARD"])) for i in range(6)]
    statuses = [AC, WA, SubmissionStatus.COMPILE_ERROR, SubmissionStatus.RUNTIME_ERROR,
                SubmissionStatus.TIME_LIMIT_EXCEEDED, SubmissionStatus.SYSTEM_ERROR]
    for i in range(120):
        world["record"](rng.choice(users), rng.choice(probs), rng.choice(statuses),
                        at=noon(TODAY - timedelta(days=rng.randint(0, 60))) + timedelta(seconds=i),
                        runtime=rng.choice([None, -1, rng.randint(1, 500)]), memory=rng.randint(1000, 9000))
    assert progress_service.audit_progress(db_session) == []
    before = {(r.user_id, r.problem_id): (r.attempt_count, r.accepted_count, r.best_runtime_ms, r.best_memory_kb)
              for r in db_session.query(UserProblemProgress).all()}

    # Corrupt the stored progress, then rebuild it from the submissions table.
    row = db_session.query(UserProblemProgress).first()
    row.attempt_count += 7
    db_session.query(Submission).filter(Submission.is_first_accepted.is_(True)).first().is_first_accepted = False
    db_session.commit()
    assert progress_service.audit_progress(db_session) != []
    progress_service.rebuild_progress(db_session)
    assert progress_service.audit_progress(db_session) == []
    after = {(r.user_id, r.problem_id): (r.attempt_count, r.accepted_count, r.best_runtime_ms, r.best_memory_kb)
             for r in db_session.query(UserProblemProgress).all()}
    assert after == before
    count = db_session.query(UserProblemProgress).count()
    progress_service.rebuild_progress(db_session)  # idempotent: no duplicate rows
    assert db_session.query(UserProblemProgress).count() == count


# ================================================================== staff analytics
def test_staff_analytics_overview(world, client):
    s = world["students"]
    a, b = world["problem"]("Two Sum"), world["problem"]("Graph Walk", topic="graphs")
    world["record"](s["Asha"], a, AC, at=noon(TODAY))
    world["record"](s["Asha"], b, WA, at=noon(TODAY))
    for _ in range(3):  # stuck: 3 attempts, nothing solved
        world["record"](s["Ravi"], b, WA, at=noon(TODAY - timedelta(days=2)))
    world["record"](s["Meena"], a, AC, at=noon(TODAY - timedelta(days=30)))  # inactive for 30 days
    data = get(client, "/api/analytics/overview", world["headers"](world["staff"]))
    assert (data["total_students"], data["active_students"], data["students_with_submissions"]) == (4, 2, 3)
    assert (data["total_submissions"], data["submissions_today"], data["accepted_submissions"], data["accepted_today"]) == (6, 2, 2, 1)
    assert data["problems_solved"] == 2
    # Per-student acceptance: Asha 50%, Ravi 0%, Meena 100% -> mean 50%.
    assert data["average_acceptance_rate"] == 50.0
    # Same solved count; Meena's 100% acceptance ranks above Asha's 50%.
    assert [(t["rank"], t["full_name"], t["solved"]) for t in data["top_students"]] == [(1, "Meena", 1), (2, "Asha", 1)]
    attention = {i["full_name"]: i["reason"] for i in data["needs_attention"]}
    assert attention == {"Ravi": "STUCK", "Meena": "INACTIVE"}
    assert len(data["daily"]) == 14 and data["daily"][-1] == {"date": TODAY.isoformat(), "submissions": 2, "accepted": 1}
    insight = {i["problem"]["slug"]: i for i in data["problems"]}
    assert (insight["graph-walk"]["attempts"], insight["graph-walk"]["solved_by"], insight["graph-walk"]["acceptance_rate"]) == (4, 0, 0.0)


def test_staff_student_table_and_detail(world, client):
    s = world["students"]
    p, q = world["problem"]("Two Sum"), world["problem"]("Three Sum", difficulty="MEDIUM")
    world["record"](s["Asha"], p, AC, at=noon(TODAY))
    world["record"](s["Asha"], q, AC, at=noon(TODAY - timedelta(days=1)))
    world["record"](s["Ravi"], p, WA, at=noon(TODAY))
    staff = world["headers"](world["staff"])
    rows = get(client, "/api/analytics/students", staff)
    assert rows["total"] == 4
    first = rows["items"][0]
    assert (first["full_name"], first["solved"], first["attempts"], first["acceptance_rate"], first["current_streak"]) == ("Asha", 2, 2, 100.0, 2)
    by_name = {r["full_name"]: r for r in rows["items"]}
    assert by_name["Kiran"]["acceptance_rate"] is None and by_name["Kiran"]["last_active_at"] is None
    assert [r["full_name"] for r in get(client, "/api/analytics/students?sort=name&order=asc", staff)["items"]] == ["Asha", "Kiran", "Meena", "Ravi"]
    assert get(client, "/api/analytics/students?search=ravi@", staff)["items"][0]["full_name"] == "Ravi"
    assert get(client, "/api/analytics/students?sort=acceptance", staff)["items"][-1]["acceptance_rate"] is None
    assert client.get("/api/analytics/students?limit=1000", headers=staff).status_code == 422
    assert client.get("/api/analytics/students?sort=password", headers=staff).status_code == 422

    detail = get(client, f"/api/analytics/students/{s['Asha'].id}", staff)
    assert detail["student"]["full_name"] == "Asha" and detail["overview"]["solved_problems"] == 2
    assert detail["difficulty"]["medium"]["solved"] == 1 and detail["streak"]["current_streak"] == 2
    assert [x["problem"]["slug"] for x in detail["solved_problems"]] == ["two-sum", "three-sum"]
    assert len(detail["heatmap"]["days"]) == 182 and "source_code" not in str(detail)
    for missing in (world["staff"].id, world["admin"].id, 999999):
        res = client.get(f"/api/analytics/students/{missing}", headers=staff)
        assert res.status_code == 404 and res.json()["error"]["code"] == "NOT_FOUND"
