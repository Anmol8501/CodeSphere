"""Code drafts. Every query is scoped to the authenticated user's id.

There is no way to pass another user's id: routes take the user from the JWT
and every lookup filters on it, so one student can never read or write
another student's code.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.draft import CodeDraft
from app.models.problem import Problem, ProgrammingLanguage
from app.models.user import User
from app.schemas.workspace import DraftSave
from app.services import problem_service

DRAFT_CONFLICT = "This draft was changed in another tab or window."


def _own_draft(db: Session, user: User, problem_id: int, language: ProgrammingLanguage, *, lock=False) -> CodeDraft | None:
    query = select(CodeDraft).where(
        CodeDraft.user_id == user.id,
        CodeDraft.problem_id == problem_id,
        CodeDraft.language == language,
    )
    if lock:
        query = query.with_for_update()
    return db.scalar(query)


def _check_language(problem: Problem, language: ProgrammingLanguage) -> None:
    if language not in problem_service.available_languages(problem):
        raise AppError(400, "This language is not available for this problem.")


def get_draft(db: Session, user: User, problem_id: int, language: ProgrammingLanguage) -> CodeDraft | None:
    problem = problem_service.get_published_by_id(db, problem_id)
    _check_language(problem, language)
    return _own_draft(db, user, problem.id, language)


def save_draft(db: Session, user: User, problem_id: int, data: DraftSave) -> CodeDraft:
    """Upsert the user's draft. One row per (user, problem, language), never duplicates."""
    problem = problem_service.get_published_by_id(db, problem_id)
    _check_language(problem, data.language)
    source = data.source_code.replace("\r\n", "\n")

    draft = _own_draft(db, user, problem.id, data.language, lock=True)
    current_version = draft.version if draft else 0
    if not data.force and data.base_version != current_version:
        db.rollback()
        raise AppError(409, DRAFT_CONFLICT)

    if draft is None:
        draft = CodeDraft(user_id=user.id, problem_id=problem.id, language=data.language, source_code=source, version=1)
        db.add(draft)
    else:
        draft.source_code = source
        draft.version = current_version + 1
    try:
        db.commit()
    except IntegrityError:
        # Two first saves raced; the unique constraint kept a single row.
        db.rollback()
        raise AppError(409, DRAFT_CONFLICT) from None
    db.refresh(draft)
    return draft
