"""Problem queries for signed-in users. Only PUBLISHED problems are visible here.

Search, filters and pagination all run in the database; the client never
receives the full problem list.
"""

from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.orm import Session, contains_eager, selectinload

from app.core.exceptions import AppError
from app.models.problem import Problem, ProblemDifficulty, ProblemStatus, ProgrammingLanguage, TestCase
from app.models.tag import Tag, problem_tags
from app.models.topic import Topic
from app.models.user import User, UserRole
from app.schemas.common import Page, total_pages
from app.schemas.problem import (
    ProblemDetail,
    ProblemExampleOut,
    ProblemListItem,
    ProblemStats,
    ProgressFilter,
    SampleTestCaseOut,
    StarterCodeOut,
)
from app.services import progress_service
from app.utils.slug import escape_like

PROBLEM_NOT_FOUND = "Problem not found."

DIFFICULTY_RANK = case(
    {ProblemDifficulty.EASY: 0, ProblemDifficulty.MEDIUM: 1, ProblemDifficulty.HARD: 2},
    value=Problem.difficulty,
)


def parse_tag_slugs(raw: str | None) -> list[str]:
    """"array, hashmap" -> ["array", "hashmap"] (max 10)."""
    if not raw:
        return []
    return list(dict.fromkeys(part.strip().lower() for part in raw.split(",") if part.strip()))[:10]


def apply_filters(
    query: Select,
    *,
    search: str | None = None,
    difficulty: ProblemDifficulty | None = None,
    topic_slug: str | None = None,
    tag_slugs: list[str] | None = None,
) -> Select:
    if search and search.strip():
        pattern = f"%{escape_like(search.strip())}%"
        tagged = (
            select(problem_tags.c.problem_id)
            .join(Tag, Tag.id == problem_tags.c.tag_id)
            .where(or_(Tag.name.ilike(pattern, escape="\\"), Tag.slug.ilike(pattern, escape="\\")))
        )
        query = query.where(
            or_(
                Problem.title.ilike(pattern, escape="\\"),
                Problem.slug.ilike(pattern, escape="\\"),
                Problem.id.in_(tagged),
            )
        )
    if difficulty:
        query = query.where(Problem.difficulty == difficulty)
    if topic_slug:
        query = query.where(Problem.topic_id.in_(select(Topic.id).where(Topic.slug == topic_slug)))
    for slug in tag_slugs or []:
        # A problem must carry every requested tag.
        query = query.where(
            Problem.id.in_(
                select(problem_tags.c.problem_id)
                .join(Tag, Tag.id == problem_tags.c.tag_id)
                .where(Tag.slug == slug)
            )
        )
    return query


def count(db: Session, query: Select) -> int:
    return db.scalar(select(func.count()).select_from(query.subquery())) or 0


def count_published(db: Session) -> int:
    return db.scalar(select(func.count(Problem.id)).where(Problem.status == ProblemStatus.PUBLISHED)) or 0


def list_published(
    db: Session,
    *,
    user: User,
    search: str | None = None,
    difficulty: ProblemDifficulty | None = None,
    topic_slug: str | None = None,
    tag_slugs: list[str] | None = None,
    progress: ProgressFilter | None = None,
    page: int = 1,
    page_size: int = 20,
) -> Page[ProblemListItem]:
    ids = apply_filters(
        select(Problem.id).where(Problem.status == ProblemStatus.PUBLISHED),
        search=search,
        difficulty=difficulty,
        topic_slug=topic_slug,
        tag_slugs=tag_slugs,
    )
    if progress:
        ids = ids.where(progress_service.progress_filter(user.id, progress))
    total = count(db, ids)

    problems = db.scalars(
        select(Problem)
        .join(Problem.topic)
        .where(Problem.id.in_(ids))
        .options(contains_eager(Problem.topic), selectinload(Problem.tags))
        .order_by(Topic.order_index, DIFFICULTY_RANK, Problem.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    ids_on_page = [p.id for p in problems]
    statuses = progress_service.statuses_for(db, user.id, ids_on_page)
    stats = progress_service.problem_stats(db, ids_on_page)
    items = [
        ProblemListItem.model_validate(p).model_copy(
            update={"user_status": statuses.get(p.id, "UNSOLVED"), "stats": stats.get(p.id, ProblemStats())}
        )
        for p in problems
    ]
    return Page[ProblemListItem](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages(total, page_size),
    )


def get_published_detail(db: Session, *, slug: str, user: User) -> ProblemDetail:
    """Public problem view. Unpublished/archived problems are reported as not found."""
    problem = db.scalar(
        select(Problem)
        .where(Problem.slug == slug, Problem.status == ProblemStatus.PUBLISHED)
        .options(
            selectinload(Problem.topic),
            selectinload(Problem.tags),
            selectinload(Problem.examples),
            selectinload(Problem.starter_codes),
        )
    )
    if problem is None:
        raise AppError(404, PROBLEM_NOT_FOUND)

    # Only visible test cases are ever selected; hidden ones never leave the DB here.
    samples = db.scalars(
        select(TestCase)
        .where(TestCase.problem_id == problem.id, TestCase.is_hidden.is_(False))
        .order_by(TestCase.order_index, TestCase.id)
    ).all()
    # Personal progress only exists for students (staff/admin browse read-only).
    progress = progress_service.problem_progress(db, user.id, problem.id) if user.role == UserRole.STUDENT else None
    stats = progress_service.problem_stats(db, [problem.id]).get(problem.id, ProblemStats())

    base = ProblemListItem.model_validate(problem).model_dump()
    return ProblemDetail(
        **{**base, "user_status": progress.status if progress else "UNSOLVED", "stats": stats},
        description=problem.description,
        constraints=problem.constraints,
        input_format=problem.input_format,
        output_format=problem.output_format,
        examples=[ProblemExampleOut.model_validate(e) for e in problem.examples],
        starter_codes=[StarterCodeOut.model_validate(s) for s in problem.starter_codes],
        sample_test_cases=[SampleTestCaseOut.model_validate(tc) for tc in samples],
        languages=available_languages(problem),
        time_limit_ms=problem.time_limit_ms,
        memory_limit_kb=problem.memory_limit_kb,
        progress=progress,
    )


def get_published_by_id(db: Session, problem_id: int) -> Problem:
    """Published problem by id; drafts/archived look exactly like a missing id."""
    problem = db.scalar(
        select(Problem)
        .where(Problem.id == problem_id, Problem.status == ProblemStatus.PUBLISHED)
        .options(selectinload(Problem.starter_codes))
    )
    if problem is None:
        raise AppError(404, PROBLEM_NOT_FOUND)
    return problem


def available_languages(problem: Problem) -> list[ProgrammingLanguage]:
    """Languages a student may code in for this problem.

    Per-problem control comes from starter code: a language is offered when the
    problem has starter code for it. A problem without any starter code allows
    every supported language.
    """
    configured = {code.language for code in problem.starter_codes}
    return [lang for lang in ProgrammingLanguage if not configured or lang in configured]
