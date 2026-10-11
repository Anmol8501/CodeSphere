"""The learning-path seed is valid, complete and idempotent."""

from app.models.problem import Problem, ProblemExample, StarterCode, TestCase
from app.models.tag import Tag
from app.models.topic import Topic
from app.seed_data.problems import PROBLEMS
from app.seed_data.tags import TAGS
from app.seed_data.topics import TOPICS
from app.utils.seed_learning import seed_learning

EXPECTED_ORDER = [
    "programming-basics", "arrays", "strings", "searching", "sorting", "linked-list", "stack", "queue",
    "hashing", "recursion", "trees", "binary-search-tree", "heap", "graphs", "greedy", "backtracking",
    "dynamic-programming",
]


def counts(db):
    return tuple(db.query(model).count() for model in (Topic, Tag, Problem, ProblemExample, StarterCode, TestCase))


def test_seed_creates_everything_once(db_session):
    first = seed_learning(db_session)
    assert first == {"topics": len(TOPICS), "tags": len(TAGS), "problems": len(PROBLEMS)}
    after_first = counts(db_session)

    second = seed_learning(db_session)
    assert second == {"topics": 0, "tags": 0, "problems": 0}
    assert counts(db_session) == after_first


def test_seed_content_is_complete(db_session):
    seed_learning(db_session)
    topics = db_session.query(Topic).order_by(Topic.order_index).all()
    assert [t.slug for t in topics] == EXPECTED_ORDER
    assert [t.order_index for t in topics] == list(range(1, 18))
    assert all(t.icon and t.description and t.learning_outcomes for t in topics)

    problems = db_session.query(Problem).all()
    assert 15 <= len(problems) <= 21
    assert {p.difficulty.value for p in problems} == {"EASY", "MEDIUM", "HARD"}
    for p in problems:
        assert p.is_published and p.tags and p.examples and p.constraints and p.input_format and p.output_format
        assert {s.language.value for s in p.starter_codes} == {"CPP", "JAVA", "PYTHON"}
        assert p.test_cases[0].is_hidden is False, p.slug  # first case is the visible sample
        assert all(tc.is_hidden for tc in p.test_cases[1:]), p.slug


def test_seed_keeps_admin_edits(db_session):
    seed_learning(db_session)
    problem = db_session.query(Problem).filter_by(slug="two-sum").one()
    problem.title = "Two Sum (edited by admin)"
    db_session.commit()
    seed_learning(db_session)
    assert db_session.query(Problem).filter_by(slug="two-sum").one().title == "Two Sum (edited by admin)"


def test_seed_attaches_hidden_harnesses(db_session):
    seed_learning(db_session)
    rows = db_session.query(StarterCode).join(Problem).all()
    with_driver = {(r.problem_id, r.language.value) for r in rows if r.driver_code}
    assert len(with_driver) == 19 * 3  # every function-style problem, every language
    for row in rows:
        if row.driver_code:
            assert row.driver_code.count("{{USER_CODE}}") == 1
    program_style = db_session.query(Problem).filter(Problem.slug.in_(["hello-world", "sum-of-two-numbers"])).all()
    assert all(not s.driver_code for p in program_style for s in p.starter_codes)


def test_execution_backfill_is_idempotent_and_conservative(db_session):
    from app.utils.seed_execution import backfill

    seed_learning(db_session)
    for row in db_session.query(StarterCode).all():
        row.driver_code = None
    edited = db_session.query(StarterCode).join(Problem).filter(Problem.slug == "two-sum", StarterCode.language == "PYTHON").one()
    edited.starter_code = "# an admin rewrote this starter\n"
    db_session.commit()

    first = backfill(db_session)
    assert first == {"added": 19 * 3 - 1, "already_set": 0, "skipped_edited": 1}
    assert edited.driver_code is None  # starter changed: harness not forced onto it
    assert backfill(db_session) == {"added": 0, "already_set": 19 * 3 - 1, "skipped_edited": 1}
