"""Problem management for administrators (all lifecycle states are visible)."""

from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AppError
from app.models.problem import (
    Problem,
    ProblemDifficulty,
    ProblemExample,
    ProblemStatus,
    StarterCode,
    TestCase,
)
from app.models.user import User
from app.schemas.admin_problem import (
    AdminProblemDetail,
    AdminProblemListItem,
    AdminStarterCodeOut,
    ProblemCreate,
    ProblemIn,
    ProblemUpdate,
    TestCaseIn,
    TestCaseOut,
)
from app.schemas.common import Page, total_pages
from app.schemas.problem import ProblemExampleOut
from app.services import problem_service, tag_service, topic_service
from app.utils.slug import slugify

SLUG_TAKEN = "A problem with this slug already exists."
TEST_CASE_NOT_FOUND = "Test case not found."


# ------------------------------------------------------------------ reads
def _test_case_counts(db: Session, problem_ids: list[int]) -> dict[int, tuple[int, int]]:
    if not problem_ids:
        return {}
    hidden = func.sum(case((TestCase.is_hidden.is_(True), 1), else_=0))
    rows: Any = db.execute(
        select(TestCase.problem_id, func.count(TestCase.id), hidden)
        .where(TestCase.problem_id.in_(problem_ids))
        .group_by(TestCase.problem_id)
    ).all()
    return {pid: (total, int(hidden_count or 0)) for pid, total, hidden_count in rows}


def _list_item(problem: Problem, counts: tuple[int, int]) -> AdminProblemListItem:
    return AdminProblemListItem.model_validate(problem).model_copy(
        update={
            "test_case_count": counts[0],
            "hidden_test_case_count": counts[1],
            "created_by_name": problem.creator.full_name if problem.creator else None,
        }
    )


def list_problems(
    db: Session,
    *,
    search: str | None = None,
    difficulty: ProblemDifficulty | None = None,
    topic_slug: str | None = None,
    tag_slugs: list[str] | None = None,
    status: ProblemStatus | None = None,
    published: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> Page[AdminProblemListItem]:
    ids = problem_service.apply_filters(
        select(Problem.id),
        search=search,
        difficulty=difficulty,
        topic_slug=topic_slug,
        tag_slugs=tag_slugs,
    )
    if status:
        ids = ids.where(Problem.status == status)
    if published is not None:
        ids = ids.where(
            Problem.status == ProblemStatus.PUBLISHED
            if published
            else Problem.status != ProblemStatus.PUBLISHED
        )
    total = problem_service.count(db, ids)

    problems = db.scalars(
        select(Problem)
        .where(Problem.id.in_(ids))
        .options(selectinload(Problem.topic), selectinload(Problem.tags), selectinload(Problem.creator))
        .order_by(Problem.updated_at.desc(), Problem.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    counts = _test_case_counts(db, [p.id for p in problems])
    return Page[AdminProblemListItem](
        items=[_list_item(p, counts.get(p.id, (0, 0))) for p in problems],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages(total, page_size),
    )


def get_problem_or_404(db: Session, problem_id: int) -> Problem:
    problem = db.get(Problem, problem_id)
    if problem is None:
        raise AppError(404, problem_service.PROBLEM_NOT_FOUND)
    return problem


def to_detail(db: Session, problem: Problem) -> AdminProblemDetail:
    db.refresh(problem)
    test_cases = [TestCaseOut.model_validate(tc) for tc in problem.test_cases]
    item = _list_item(problem, (len(test_cases), sum(tc.is_hidden for tc in test_cases)))
    return AdminProblemDetail(
        **item.model_dump(),
        description=problem.description,
        constraints=problem.constraints,
        input_format=problem.input_format,
        output_format=problem.output_format,
        time_limit_ms=problem.time_limit_ms,
        memory_limit_kb=problem.memory_limit_kb,
        examples=[ProblemExampleOut.model_validate(e) for e in problem.examples],
        starter_codes=[AdminStarterCodeOut.model_validate(s) for s in problem.starter_codes],
        test_cases=test_cases,
    )


# ------------------------------------------------------------------ writes
def _resolve_slug(db: Session, data: ProblemIn, *, current_id: int | None = None) -> str:
    slug = data.slug or slugify(data.title)
    if not slug:
        raise AppError(400, "Could not generate a slug from the title. Please enter a slug.")
    existing = db.scalar(select(Problem.id).where(Problem.slug == slug))
    if existing is not None and existing != current_id:
        raise AppError(409, SLUG_TAKEN)
    return slug


def _apply_content(db: Session, problem: Problem, data: ProblemIn) -> None:
    if topic_service.get_topic(db, data.topic_id) is None:
        raise AppError(400, "Selected topic does not exist.")
    tags = tag_service.get_tags_by_ids(db, data.tag_ids)
    if len(tags) != len(data.tag_ids):
        raise AppError(400, "One or more selected tags do not exist.")

    problem.title = data.title
    problem.description = data.description
    problem.difficulty = data.difficulty
    problem.topic_id = data.topic_id
    problem.constraints = data.constraints
    problem.input_format = data.input_format
    problem.output_format = data.output_format
    problem.time_limit_ms = data.time_limit_ms
    problem.memory_limit_kb = data.memory_limit_kb
    problem.tags = tags
    problem.examples = [
        ProblemExample(input=e.input, output=e.output, explanation=e.explanation, order_index=i)
        for i, e in enumerate(data.examples)
    ]

    # Update starter code in place per language: replacing the rows would
    # briefly violate the (problem_id, language) unique constraint.
    wanted = {item.language: item for item in data.starter_codes}
    for existing in list(problem.starter_codes):
        if existing.language in wanted:
            item = wanted.pop(existing.language)
            existing.starter_code = item.starter_code
            existing.driver_code = item.driver_code
        else:
            problem.starter_codes.remove(existing)
    for language, item in wanted.items():
        problem.starter_codes.append(StarterCode(language=language, starter_code=item.starter_code, driver_code=item.driver_code))


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, SLUG_TAKEN) from None


def create_problem(db: Session, data: ProblemCreate, author: User | None) -> Problem:
    problem = Problem(
        slug=_resolve_slug(db, data),
        created_by=author.id if author else None,
        status=ProblemStatus.PUBLISHED if data.is_published else ProblemStatus.DRAFT,
    )
    _apply_content(db, problem, data)
    problem.test_cases = [_new_test_case(tc, i) for i, tc in enumerate(data.test_cases)]
    db.add(problem)
    _commit(db)
    return problem


def update_problem(db: Session, problem: Problem, data: ProblemUpdate) -> Problem:
    problem.slug = _resolve_slug(db, data, current_id=problem.id)
    _apply_content(db, problem, data)
    if data.is_published is not None:
        problem.status = ProblemStatus.PUBLISHED if data.is_published else ProblemStatus.DRAFT
    _commit(db)
    return problem


def set_published(db: Session, problem: Problem, is_published: bool) -> Problem:
    """Publish, or move back to DRAFT (also restores an archived problem)."""
    problem.status = ProblemStatus.PUBLISHED if is_published else ProblemStatus.DRAFT
    db.commit()
    return problem


def archive_problem(db: Session, problem: Problem) -> Problem:
    """Soft delete: hidden from students, kept for future submission history."""
    problem.status = ProblemStatus.ARCHIVED
    db.commit()
    return problem


# ------------------------------------------------------------------ test cases
def _new_test_case(data: TestCaseIn, default_order: int) -> TestCase:
    return TestCase(
        input_data=data.input_data,
        expected_output=data.expected_output,
        is_hidden=data.is_hidden,
        order_index=data.order_index if data.order_index is not None else default_order,
    )


def list_test_cases(db: Session, problem: Problem) -> list[TestCase]:
    return list(
        db.scalars(
            select(TestCase)
            .where(TestCase.problem_id == problem.id)
            .order_by(TestCase.order_index, TestCase.id)
        ).all()
    )


def add_test_case(db: Session, problem: Problem, data: TestCaseIn) -> TestCase:
    next_order = db.scalar(
        select(func.coalesce(func.max(TestCase.order_index) + 1, 0)).where(TestCase.problem_id == problem.id)
    )
    test_case = _new_test_case(data, next_order or 0)
    test_case.problem_id = problem.id
    db.add(test_case)
    db.commit()
    db.refresh(test_case)
    return test_case


def get_test_case_or_404(db: Session, test_case_id: int) -> TestCase:
    test_case = db.get(TestCase, test_case_id)
    if test_case is None:
        raise AppError(404, TEST_CASE_NOT_FOUND)
    return test_case


def update_test_case(db: Session, test_case: TestCase, data: TestCaseIn) -> TestCase:
    test_case.input_data = data.input_data
    test_case.expected_output = data.expected_output
    test_case.is_hidden = data.is_hidden
    if data.order_index is not None:
        test_case.order_index = data.order_index
    db.commit()
    db.refresh(test_case)
    return test_case


def delete_test_case(db: Session, test_case: TestCase) -> None:
    db.delete(test_case)
    db.commit()
