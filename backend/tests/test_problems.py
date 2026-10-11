"""Phase 3: topics, tags, problems, search/filter/pagination, admin management, security."""

import pytest

from app.models.problem import Problem, ProblemStatus, StarterCode, TestCase
from app.models.submission import Submission, SubmissionStatus
from app.models.user import UserRole
from app.services import topic_service
from tests.conftest import auth_header

HIDDEN_MARKER = "HIDDEN-EXPECTED-9137"


@pytest.fixture()
def world(client, make_user, db_session):
    make_user("student@college.edu", UserRole.STUDENT, name="Asha Kumar")
    make_user("student2@college.edu", UserRole.STUDENT, name="Ravi Iyer")
    make_user("staff@college.edu", UserRole.STAFF, name="Prof Mehta")
    make_user("admin@college.edu", UserRole.ADMIN, name="Main Admin")
    headers = {
        "STUDENT": auth_header(client, "student@college.edu"),
        "STUDENT2": auth_header(client, "student2@college.edu"),
        "STAFF": auth_header(client, "staff@college.edu"),
        "ADMIN": auth_header(client, "admin@college.edu"),
    }
    # Inserted out of order on purpose: the API must sort by order_index.
    topics = {
        "arrays": topic_service.create_topic(db_session, name="Arrays", slug="arrays", order_index=2,
                                             learning_outcomes=["Two pointers"]),
        "programming-basics": topic_service.create_topic(db_session, name="Programming Basics",
                                                         slug="programming-basics", order_index=1),
        "strings": topic_service.create_topic(db_session, name="Strings", slug="strings", order_index=3),
    }
    tags = {}
    for name in ("Array", "HashMap", "Two Pointer", "String"):
        res = client.post("/api/admin/tags", json={"name": name}, headers=headers["ADMIN"])
        assert res.status_code == 201, res.text
        tags[name] = res.json()["data"]
    return {"headers": headers, "topics": topics, "tags": tags}


def payload(world, **overrides):
    data = {
        "title": "Two Sum",
        "description": "Find two indices whose values add up to the target.",
        "difficulty": "EASY",
        "topic_id": world["topics"]["arrays"].id,
        "tag_ids": [world["tags"]["Array"]["id"], world["tags"]["HashMap"]["id"]],
        "constraints": "2 <= n <= 10^4",
        "input_format": "n, then n integers, then target",
        "output_format": "two indices",
        "examples": [{"input": "nums = [2,7,11,15]\ntarget = 9", "output": "[0,1]", "explanation": "2 + 7 = 9"}],
        "starter_codes": [
            {"language": "CPP", "starter_code": "class Solution {\npublic:\n};"},
            {"language": "JAVA", "starter_code": "class Solution {\n}"},
            {"language": "PYTHON", "starter_code": "class Solution:\n    def solve(self):\n        pass"},
        ],
        "test_cases": [
            {"input_data": "4\n2 7 11 15\n9", "expected_output": "0 1", "is_hidden": False},
            {"input_data": "3\n3 2 4\n6", "expected_output": HIDDEN_MARKER, "is_hidden": True},
        ],
        "is_published": True,
    }
    data.update(overrides)
    return data


def create(client, world, **overrides):
    res = client.post("/api/admin/problems", json=payload(world, **overrides), headers=world["headers"]["ADMIN"])
    assert res.status_code == 201, res.text
    return res.json()["data"]


def student_get(client, world, path, who="STUDENT"):
    return client.get(path, headers=world["headers"][who])


# ------------------------------------------------------------------ topics & tags
def test_topics_ordered_with_published_counts(client, world):
    create(client, world)
    create(client, world, title="Draft One", is_published=False)
    res = student_get(client, world, "/api/topics")
    assert res.status_code == 200
    topics = res.json()["data"]
    assert [t["slug"] for t in topics] == ["programming-basics", "arrays", "strings"]
    assert [t["order_index"] for t in topics] == [1, 2, 3]
    arrays = topics[1]
    assert arrays["problem_count"] == 1  # the draft is not counted
    assert arrays["parent_topic_id"] is None
    assert arrays["learning_outcomes"] == ["Two pointers"]


def test_get_topic_detail_and_not_found(client, world):
    create(client, world)
    create(client, world, title="Hard One", difficulty="HARD")
    data = student_get(client, world, "/api/topics/arrays").json()["data"]
    assert data["name"] == "Arrays"
    assert data["problem_count"] == 2
    assert data["difficulty_counts"] == {"EASY": 1, "MEDIUM": 0, "HARD": 1}
    assert data["solved_count"] == 0 and data["progress"] == 0 and data["status"] == "NOT_STARTED"

    res = student_get(client, world, "/api/topics/does-not-exist")
    assert res.status_code == 404
    assert res.json() == {"success": False, "message": "Topic not found.", "error": {"code": "NOT_FOUND", "message": "Topic not found."}}


def test_tags_listed_and_duplicates_rejected(client, world):
    tags = student_get(client, world, "/api/tags").json()["data"]
    assert [t["slug"] for t in tags] == ["array", "hashmap", "string", "two-pointer"]
    dup = client.post("/api/admin/tags", json={"name": "hashmap"}, headers=world["headers"]["ADMIN"])
    assert dup.status_code == 409


# ------------------------------------------------------------------ admin create / read / update
def test_admin_creates_full_problem(client, world, db_session):
    data = create(client, world)
    assert data["slug"] == "two-sum"  # generated from the title
    assert data["status"] == "PUBLISHED" and data["is_published"] is True
    assert data["topic"]["slug"] == "arrays"
    assert [t["name"] for t in data["tags"]] == ["Array", "HashMap"]
    assert data["examples"][0]["explanation"] == "2 + 7 = 9"
    assert {s["language"] for s in data["starter_codes"]} == {"CPP", "JAVA", "PYTHON"}
    assert [tc["is_hidden"] for tc in data["test_cases"]] == [False, True]
    assert data["test_case_count"] == 2 and data["hidden_test_case_count"] == 1
    assert data["created_by_name"] == "Main Admin"

    problem = db_session.get(Problem, data["id"])
    assert problem.status == ProblemStatus.PUBLISHED
    assert len(problem.test_cases) == 2 and len(problem.starter_codes) == 3


def test_admin_get_problem_includes_hidden_cases(client, world):
    created = create(client, world)
    res = client.get(f"/api/admin/problems/{created['id']}", headers=world["headers"]["ADMIN"])
    assert res.status_code == 200
    assert HIDDEN_MARKER in res.text
    assert client.get("/api/admin/problems/999999", headers=world["headers"]["ADMIN"]).status_code == 404
    # Out-of-range ids are rejected cleanly instead of overflowing the database integer.
    assert client.get("/api/admin/problems/99999999999", headers=world["headers"]["ADMIN"]).status_code == 422


@pytest.mark.parametrize(
    "overrides, status, message_part",
    [
        ({"slug": "Bad Slug!"}, 422, "Slug may only contain"),
        ({"difficulty": "IMPOSSIBLE"}, 422, "Invalid difficulty"),
        ({"topic_id": 9999}, 400, "Selected topic does not exist."),
        ({"tag_ids": [9999]}, 400, "One or more selected tags do not exist."),
        ({"title": "ab"}, 422, "at least 3"),
        ({"description": "   short   "}, 422, "at least 10"),
        ({"status": "PUBLISHED"}, 422, "Unexpected field: status."),
        ({"created_by": 1}, 422, "Unexpected field: created_by."),
        (
            {"starter_codes": [{"language": "CPP", "starter_code": "a"}, {"language": "CPP", "starter_code": "b"}]},
            422,
            "one starter code",
        ),
        ({"starter_codes": [{"language": "RUBY", "starter_code": "x"}]}, 422, "Invalid language"),
        ({"test_cases": [{"input_data": "1", "expected_output": ""}]}, 422, None),
    ],
)
def test_create_problem_validation(client, world, overrides, status, message_part):
    res = client.post("/api/admin/problems", json=payload(world, **overrides), headers=world["headers"]["ADMIN"])
    assert res.status_code == status, res.text
    body = res.json()
    assert body["success"] is False
    if message_part:
        assert message_part in body["message"]


def test_duplicate_slug_conflict(client, world):
    create(client, world)
    res = client.post("/api/admin/problems", json=payload(world), headers=world["headers"]["ADMIN"])
    assert res.status_code == 409
    assert res.json()["message"] == "A problem with this slug already exists."


def test_admin_updates_problem(client, world, db_session):
    created = create(client, world)
    other = create(client, world, title="Other Problem")
    body = payload(
        world,
        title="Two Sum Classic",
        slug="two-sum-classic",
        difficulty="MEDIUM",
        topic_id=world["topics"]["strings"].id,
        tag_ids=[world["tags"]["Two Pointer"]["id"]],
        examples=[{"input": "a", "output": "b"}, {"input": "c", "output": "d", "explanation": "x"}],
        starter_codes=[
            {"language": "PYTHON", "starter_code": "print('updated')"},
            {"language": "JAVA", "starter_code": "class Solution { int x; }"},
        ],
    )
    body.pop("test_cases")
    res = client.put(f"/api/admin/problems/{created['id']}", json=body, headers=world["headers"]["ADMIN"])
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["title"] == "Two Sum Classic" and data["slug"] == "two-sum-classic"
    assert data["difficulty"] == "MEDIUM" and data["topic"]["slug"] == "strings"
    assert [t["slug"] for t in data["tags"]] == ["two-pointer"]
    assert [e["input"] for e in data["examples"]] == ["a", "c"]
    assert {s["language"]: s["starter_code"] for s in data["starter_codes"]} == {
        "JAVA": "class Solution { int x; }\n",
        "PYTHON": "print('updated')\n",
    }
    assert data["test_case_count"] == 2  # PUT never touches test cases
    assert db_session.query(StarterCode).filter_by(problem_id=created["id"]).count() == 2

    # Renaming to another problem's slug is a conflict.
    body["slug"] = other["slug"]
    res = client.put(f"/api/admin/problems/{created['id']}", json=body, headers=world["headers"]["ADMIN"])
    assert res.status_code == 409
    # Test cases cannot be smuggled through PUT.
    body["slug"] = "two-sum-classic"
    body["test_cases"] = []
    assert client.put(f"/api/admin/problems/{created['id']}", json=body, headers=world["headers"]["ADMIN"]).status_code == 422


# ------------------------------------------------------------------ publish lifecycle
def test_publish_unpublish_archive_visibility(client, world):
    problem = create(client, world, is_published=False)
    admin = world["headers"]["ADMIN"]
    url = f"/api/problems/{problem['slug']}"

    assert problem["status"] == "DRAFT"
    assert student_get(client, world, url).status_code == 404
    assert student_get(client, world, "/api/problems").json()["data"]["total"] == 0

    res = client.patch(f"/api/admin/problems/{problem['id']}/publish", json={"is_published": True}, headers=admin)
    assert res.status_code == 200 and res.json()["data"]["status"] == "PUBLISHED"
    assert student_get(client, world, url).status_code == 200
    assert student_get(client, world, "/api/problems").json()["data"]["total"] == 1

    res = client.patch(f"/api/admin/problems/{problem['id']}/publish", json={"is_published": False}, headers=admin)
    assert res.json()["data"]["status"] == "DRAFT"
    missing = student_get(client, world, url)
    assert missing.status_code == 404
    # Same response as a slug that never existed: nothing reveals the draft.
    assert missing.json() == student_get(client, world, "/api/problems/never-existed").json()

    client.patch(f"/api/admin/problems/{problem['id']}/publish", json={"is_published": True}, headers=admin)
    res = client.delete(f"/api/admin/problems/{problem['id']}", headers=admin)
    assert res.status_code == 200 and res.json()["data"]["status"] == "ARCHIVED"
    assert student_get(client, world, url).status_code == 404
    # Archiving is a soft delete: admin still sees it.
    listed = client.get("/api/admin/problems?status=ARCHIVED", headers=admin).json()["data"]
    assert [p["id"] for p in listed["items"]] == [problem["id"]]


def test_admin_list_status_filters(client, world):
    create(client, world, title="Published One")
    create(client, world, title="Draft One", is_published=False)
    admin = world["headers"]["ADMIN"]
    everything = client.get("/api/admin/problems", headers=admin).json()["data"]
    assert everything["total"] == 2
    published = client.get("/api/admin/problems?published=true", headers=admin).json()["data"]
    assert [p["title"] for p in published["items"]] == ["Published One"]
    drafts = client.get("/api/admin/problems?status=DRAFT", headers=admin).json()["data"]
    assert [p["title"] for p in drafts["items"]] == ["Draft One"]
    assert drafts["items"][0]["test_case_count"] == 2


# ------------------------------------------------------------------ student detail security
def test_student_detail_has_public_data_only(client, world):
    create(client, world)
    res = student_get(client, world, "/api/problems/two-sum")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["title"] == "Two Sum" and data["difficulty"] == "EASY"
    assert data["topic"] == {"id": world["topics"]["arrays"].id, "name": "Arrays", "slug": "arrays"}
    assert [t["name"] for t in data["tags"]] == ["Array", "HashMap"]
    assert data["examples"][0]["output"] == "[0,1]"
    assert {s["language"] for s in data["starter_codes"]} == {"CPP", "JAVA", "PYTHON"}
    assert data["sample_test_cases"] == [{"input_data": "4\n2 7 11 15\n9", "expected_output": "0 1", "order_index": 0}]
    assert data["user_status"] == "UNSOLVED"

    # Hidden test data and admin metadata never appear anywhere in the response.
    # (The only "status" is the student's own progress, never the problem's lifecycle.)
    for forbidden in (HIDDEN_MARKER, "is_hidden", "\"test_cases\"", "created_by", "PUBLISHED", "DRAFT", "hidden_test_case_count"):
        assert forbidden not in res.text, forbidden
    assert "status" not in data and data["progress"]["status"] == "UNSOLVED" and data["progress"]["attempts"] == 0
    assert data["stats"] == {"solved_by": 0, "attempts": 0, "accepted": 0, "acceptance_rate": None}


def test_staff_can_read_published_problems(client, world):
    create(client, world)
    assert student_get(client, world, "/api/problems", who="STAFF").json()["data"]["total"] == 1
    res = student_get(client, world, "/api/problems/two-sum", who="STAFF")
    assert res.status_code == 200 and HIDDEN_MARKER not in res.text


# ------------------------------------------------------------------ search / filter / pagination
@pytest.fixture()
def library(client, world):
    create(client, world, title="Two Sum")
    create(client, world, title="Binary Search", topic_id=world["topics"]["arrays"].id,
           tag_ids=[world["tags"]["Array"]["id"]], difficulty="EASY")
    create(client, world, title="Three Sum", difficulty="MEDIUM",
           tag_ids=[world["tags"]["Array"]["id"], world["tags"]["Two Pointer"]["id"]])
    create(client, world, title="Valid Palindrome", topic_id=world["topics"]["strings"].id,
           tag_ids=[world["tags"]["String"]["id"], world["tags"]["Two Pointer"]["id"]])
    create(client, world, title="Hard Thing", difficulty="HARD", tag_ids=[])
    create(client, world, title="Secret Draft", is_published=False)
    return world


def titles(res):
    return [p["title"] for p in res.json()["data"]["items"]]


@pytest.mark.parametrize(
    "query, expected",
    [
        ("search=binary", ["Binary Search"]),
        ("search=BINARY", ["Binary Search"]),
        ("search=three-sum", ["Three Sum"]),  # slug
        ("search=hashmap", ["Two Sum"]),  # tag name
        ("search=two pointer", ["Three Sum", "Valid Palindrome"]),  # tag
        ("search=secret", []),  # drafts are never searchable by students
        ("search=%25", []),  # LIKE wildcard is escaped
        ("difficulty=MEDIUM", ["Three Sum"]),
        ("difficulty=HARD", ["Hard Thing"]),
        ("topic=strings", ["Valid Palindrome"]),
        ("topic=arrays&difficulty=EASY", ["Two Sum", "Binary Search"]),
        ("tags=two-pointer", ["Three Sum", "Valid Palindrome"]),
        ("tags=array,two-pointer", ["Three Sum"]),
        ("topic=unknown-topic", []),
    ],
)
def test_search_and_filters(client, library, query, expected):
    res = student_get(client, library, f"/api/problems?{query}")
    assert res.status_code == 200, res.text
    assert titles(res) == expected


def test_list_order_topic_then_difficulty(client, library):
    assert titles(student_get(client, library, "/api/problems")) == [
        "Two Sum", "Binary Search", "Three Sum", "Hard Thing", "Valid Palindrome",
    ]


def test_invalid_filters(client, library):
    res = student_get(client, library, "/api/problems?difficulty=EXTREME")
    assert res.status_code == 422
    assert res.json()["message"].startswith("Invalid difficulty.")
    assert student_get(client, library, "/api/problems?status=done").status_code == 422
    assert student_get(client, library, "/api/problems?page=0").status_code == 422
    assert student_get(client, library, "/api/problems?page_size=500").status_code == 422


def test_pagination(client, library):
    page1 = student_get(client, library, "/api/problems?page=1&page_size=2").json()["data"]
    assert page1["page"] == 1 and page1["page_size"] == 2
    assert page1["total"] == 5 and page1["total_pages"] == 3
    assert len(page1["items"]) == 2
    page3 = student_get(client, library, "/api/problems?page=3&page_size=2").json()["data"]
    assert [p["title"] for p in page3["items"]] == ["Valid Palindrome"]
    beyond = student_get(client, library, "/api/problems?page=9&page_size=2").json()["data"]
    assert beyond["items"] == [] and beyond["total"] == 5


# ------------------------------------------------------------------ test cases (admin)
def test_test_case_crud(client, world):
    problem = create(client, world)
    admin = world["headers"]["ADMIN"]
    base = f"/api/admin/problems/{problem['id']}/test-cases"

    listed = client.get(base, headers=admin).json()["data"]
    assert [tc["order_index"] for tc in listed] == [0, 1]

    res = client.post(base, json={"input_data": "2\n1 1\n2", "expected_output": "0 1"}, headers=admin)
    assert res.status_code == 201
    new = res.json()["data"]
    assert new["is_hidden"] is True and new["order_index"] == 2  # hidden by default, appended

    res = client.put(f"/api/admin/test-cases/{new['id']}",
                     json={"input_data": "x", "expected_output": "y", "is_hidden": False}, headers=admin)
    assert res.status_code == 200
    assert res.json()["data"]["is_hidden"] is False and res.json()["data"]["expected_output"] == "y"

    assert client.delete(f"/api/admin/test-cases/{new['id']}", headers=admin).status_code == 200
    assert client.delete(f"/api/admin/test-cases/{new['id']}", headers=admin).status_code == 404
    assert len(client.get(base, headers=admin).json()["data"]) == 2
    assert client.get("/api/admin/problems/424242/test-cases", headers=admin).status_code == 404


def test_deleting_problem_rows_keeps_users(client, world, db_session):
    """Cascades only flow downward: removing a problem never touches users."""
    from app.models.user import User

    problem = create(client, world)
    users_before = db_session.query(User).count()
    db_session.delete(db_session.get(Problem, problem["id"]))
    db_session.commit()
    assert db_session.query(User).count() == users_before
    assert db_session.query(TestCase).count() == 0


# ------------------------------------------------------------------ role security
ADMIN_ENDPOINTS = [
    ("get", "/api/admin/problems", None),
    ("get", "/api/admin/problems/1", None),
    ("post", "/api/admin/problems", {}),
    ("put", "/api/admin/problems/1", {}),
    ("patch", "/api/admin/problems/1/publish", {"is_published": True}),
    ("delete", "/api/admin/problems/1", None),
    ("get", "/api/admin/problems/1/test-cases", None),
    ("post", "/api/admin/problems/1/test-cases", {"input_data": "", "expected_output": "1"}),
    ("put", "/api/admin/test-cases/1", {"input_data": "", "expected_output": "1"}),
    ("delete", "/api/admin/test-cases/1", None),
    ("post", "/api/admin/tags", {"name": "Sneaky"}),
]


@pytest.mark.parametrize("method, path, body", ADMIN_ENDPOINTS)
@pytest.mark.parametrize("role", ["STUDENT", "STAFF"])
def test_non_admins_cannot_manage_problems(client, world, role, method, path, body):
    create(client, world)  # problem 1 with test cases exists
    kwargs = {"headers": world["headers"][role]}
    if body is not None:
        kwargs["json"] = payload(world) if body == {} else body
    res = getattr(client, method)(path, **kwargs)
    assert res.status_code == 403, (role, method, path, res.status_code)
    assert HIDDEN_MARKER not in res.text


@pytest.mark.parametrize("method, path, body", ADMIN_ENDPOINTS[:3])
def test_admin_endpoints_require_login(client, world, method, path, body):
    kwargs = {"json": body} if body is not None else {}
    assert getattr(client, method)(path, **kwargs).status_code == 401


@pytest.mark.parametrize("path", ["/api/problems", "/api/problems/two-sum", "/api/topics", "/api/topics/arrays",
                                  "/api/tags", "/api/learning-path"])
def test_read_endpoints_require_login(client, world, path):
    assert client.get(path).status_code == 401


def test_problems_unchanged_after_forbidden_attempts(client, world, db_session):
    create(client, world)
    student = world["headers"]["STUDENT"]
    client.post("/api/admin/problems", json=payload(world, title="Student Made"), headers=student)
    client.patch("/api/admin/problems/1/publish", json={"is_published": False}, headers=world["headers"]["STAFF"])
    assert db_session.query(Problem).count() == 1
    assert db_session.get(Problem, 1).status == ProblemStatus.PUBLISHED


# ------------------------------------------------------------------ solved status & learning path
def _accept(db_session, user_email, problem_id, status=SubmissionStatus.ACCEPTED):
    from app.models.user import User
    from app.services import progress_service

    user = db_session.query(User).filter_by(email=user_email).one()
    submission = Submission(user_id=user.id, problem_id=problem_id, language="PYTHON", source_code="pass", status=status)
    db_session.add(submission)
    db_session.flush()
    # Same path as a real judged submission: progress is updated in the verdict's transaction.
    progress_service.record_judged_submission(db_session, submission)
    db_session.commit()


def test_learning_path_counts_and_honest_progress(client, world):
    create(client, world)
    create(client, world, title="Another Array Problem", difficulty="MEDIUM")
    create(client, world, title="Draft Array Problem", is_published=False)
    student_get(client, world, "/api/problems/two-sum")  # opening a problem must not mark it solved

    data = student_get(client, world, "/api/learning-path").json()["data"]
    assert [t["slug"] for t in data["topics"]] == ["programming-basics", "arrays", "strings"]
    arrays = data["topics"][1]
    assert arrays["problem_count"] == 2
    assert arrays["solved_count"] == 0 and arrays["progress"] == 0 and arrays["status"] == "NOT_STARTED"
    assert data["total_problems"] == 2 and data["total_solved"] == 0 and data["progress"] == 0


def test_solved_status_comes_from_accepted_submissions(client, world, db_session):
    first = create(client, world)
    second = create(client, world, title="Second Problem")
    _accept(db_session, "student@college.edu", first["id"])
    _accept(db_session, "student@college.edu", second["id"], SubmissionStatus.WRONG_ANSWER)

    items = {p["slug"]: p["user_status"] for p in student_get(client, world, "/api/problems").json()["data"]["items"]}
    assert items == {"two-sum": "SOLVED", "second-problem": "ATTEMPTED"}
    assert titles(student_get(client, world, "/api/problems?status=solved")) == ["Two Sum"]
    assert titles(student_get(client, world, "/api/problems?status=attempted")) == ["Second Problem"]
    assert titles(student_get(client, world, "/api/problems?status=unsolved")) == ["Second Problem"]

    arrays = student_get(client, world, "/api/topics/arrays").json()["data"]
    assert arrays["solved_count"] == 1 and arrays["progress"] == 50 and arrays["status"] == "IN_PROGRESS"
    dashboard = student_get(client, world, "/api/student/dashboard").json()["data"]
    assert dashboard["statistics"]["problems_solved"] == 1
    assert dashboard["learning_progress"] == [
        {"slug": "arrays", "topic": "Arrays", "solved": 1, "total": 2, "percent": 50},
    ]

    # Progress is per user: the other student has solved nothing.
    other = student_get(client, world, "/api/learning-path", who="STUDENT2").json()["data"]
    assert other["total_solved"] == 0
    assert student_get(client, world, "/api/problems/two-sum", who="STUDENT2").json()["data"]["user_status"] == "UNSOLVED"


def test_admin_stats_count_published_problems(client, world):
    create(client, world)
    create(client, world, title="Draft", is_published=False)
    stats = client.get("/api/admin/stats", headers=world["headers"]["ADMIN"]).json()["data"]
    assert stats["total_problems"] == 1
