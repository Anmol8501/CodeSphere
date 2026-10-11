"""RUN and SUBMIT: the boundary between CodeArena and the Judge0 sandbox.

Student code is NEVER executed by this process. It is assembled with the
problem's hidden driver (if any) and sent to Judge0, which compiles and runs
it in isolation. This module validates requests, applies limits, decides the
verdict from Judge0's raw results and persists submissions.

  RUN    public tests (+ the student's custom cases). Not stored.
  SUBMIT public + hidden tests. Always stored; always resolves to a final
         status (never left PENDING/RUNNING, see expire_stuck_submissions).
"""

import logging
import threading
import time
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.languages import LANGUAGES, parse_language
from app.models.problem import Problem, ProgrammingLanguage, TestCase
from app.models.submission import (
    IN_PROGRESS_STATUSES,
    TEST_STATUS_FOR_VERDICT,
    Submission,
    SubmissionStatus,
    SubmissionTestResult,
)
from app.models.user import User
from app.schemas.workspace import RunRequest, RunResult, SubmitRequest, TestResultOut
from app.services import problem_service, progress_service
from app.services.judging import judge0
from app.services.judging.harness import build_program
from app.services.judging.runner import JudgeCase, RunReport, TestOutcome, limits_for, overall_verdict, run_cases
from app.utils.rate_limiter import run_rate_limiter, submit_rate_limiter

logger = logging.getLogger("codearena.execution")

UNAVAILABLE_MESSAGE = "Code execution service is temporarily unavailable."
TIMEOUT_MESSAGE = "The execution service did not respond in time. Please try again."
HIDDEN_RUNTIME_MESSAGE = "Your program failed on a hidden test case. Hidden test details are not shown."
# Stored per public test in a submission (keeps rows small).
STORED_TEXT_LIMIT = 4_000

_job_slots = threading.BoundedSemaphore(max(1, settings.JUDGE0_MAX_CONCURRENT_JOBS))
_active_lock = threading.Lock()
_active: set[tuple[str, int]] = set()


def get_judge_client() -> judge0.Judge0Client | None:
    """The configured Judge0 client (tests replace this)."""
    return judge0.client_from_settings()


# ------------------------------------------------------------------ guards
@contextmanager
def _one_at_a_time(kind: str, user_id: int, message: str):
    """Reject a second concurrent run/submit from the same student (double clicks)."""
    key = (kind, user_id)
    with _active_lock:
        if key in _active:
            raise AppError(409, message, code=f"{kind.upper()}_IN_PROGRESS")
        _active.add(key)
    try:
        yield
    finally:
        with _active_lock:
            _active.discard(key)


@contextmanager
def _job_slot():
    if not _job_slots.acquire(timeout=10):
        raise judge0.JudgeUnavailable("All execution slots are busy")
    try:
        yield
    finally:
        _job_slots.release()


def _validate(db: Session, problem_id: int, language_value: str | None, source_code: str) -> tuple[Problem, ProgrammingLanguage]:
    language = parse_language(language_value)
    if language is None:
        raise AppError(400, "This language is not supported.", code="INVALID_LANGUAGE")
    problem = problem_service.get_published_by_id(db, problem_id)  # 404 for drafts / archived
    if language not in problem_service.available_languages(problem):
        raise AppError(400, "This language is not available for this problem.", code="LANGUAGE_NOT_AVAILABLE")
    size = len(source_code.encode("utf-8"))
    if size > settings.EXECUTION_MAX_SOURCE_BYTES:
        raise AppError(
            413, f"Source code is too large (limit {settings.EXECUTION_MAX_SOURCE_BYTES // 1000} KB).", code="SOURCE_TOO_LARGE"
        )
    if not source_code.strip():
        raise AppError(400, "Write some code before running it.", code="EMPTY_SOURCE")
    return problem, language


def _program(problem: Problem, language: ProgrammingLanguage, source_code: str) -> str:
    starter = next((s for s in problem.starter_codes if s.language == language), None)
    return build_program(source_code.replace("\r\n", "\n"), starter.driver_code if starter else None)


def _official_cases(db: Session, problem: Problem, *, include_hidden: bool) -> list[JudgeCase]:
    query = select(TestCase).where(TestCase.problem_id == problem.id)
    if not include_hidden:
        query = query.where(TestCase.is_hidden.is_(False))
    return [
        JudgeCase(
            kind="hidden" if tc.is_hidden else "public",
            index=position,
            stdin=tc.input_data,
            expected_output=tc.expected_output,
            test_case_id=tc.id,
        )
        for position, tc in enumerate(db.scalars(query.order_by(TestCase.order_index, TestCase.id)).all(), start=1)
    ]


def _limits(problem: Problem, language: ProgrammingLanguage) -> judge0.ExecutionLimits:
    return limits_for(LANGUAGES[language], problem.time_limit_ms, problem.memory_limit_kb, max_output_kb=1024)


def _execute(problem: Problem, language: ProgrammingLanguage, program: str, cases: list[JudgeCase], *, stop_on_failure: bool) -> RunReport:
    client = get_judge_client()
    if client is None:
        raise judge0.JudgeUnavailable("Judge0 is not configured")
    spec = LANGUAGES[language]
    limits = _limits(problem, language)
    try:
        with _job_slot():
            return run_cases(
                client,
                program=program,
                language=spec,
                cases=cases,
                limits=limits,
                deadline=time.monotonic() + settings.JUDGE0_TIMEOUT,
                stop_on_failure=stop_on_failure,
                max_output_bytes=settings.EXECUTION_MAX_OUTPUT_BYTES,
            )
    finally:
        client.close()


def _result_out(outcome: TestOutcome, *, text_limit: int) -> TestResultOut:
    case = outcome.case
    base = TestResultOut(
        index=case.index,
        kind=case.kind,
        status=TEST_STATUS_FOR_VERDICT[outcome.verdict],
        runtime_ms=outcome.time_ms,
        memory_kb=outcome.memory_kb,
    )
    if case.kind == "hidden":
        return base  # never the hidden input, expected output, or the program's output on it
    return base.model_copy(
        update={
            "input": case.stdin[:text_limit],
            "expected_output": case.expected_output[:text_limit] if case.expected_output is not None else None,
            "actual_output": outcome.stdout[:text_limit],
            "stderr": outcome.stderr[:text_limit] or None,
        }
    )


def _stored_result(outcome: TestOutcome) -> SubmissionTestResult:
    """Row for one executed official test. Hidden tests keep no test data at all."""
    case = outcome.case
    hidden = case.kind == "hidden"
    return SubmissionTestResult(
        test_case_id=case.test_case_id,
        position=case.index,
        is_hidden=hidden,
        status=TEST_STATUS_FOR_VERDICT[outcome.verdict],
        runtime_ms=outcome.time_ms,
        memory_kb=outcome.memory_kb,
        input_data=None if hidden else case.stdin[:STORED_TEXT_LIMIT],
        expected_output=None if hidden or case.expected_output is None else case.expected_output[:STORED_TEXT_LIMIT],
        actual_output=None if hidden else outcome.stdout[:STORED_TEXT_LIMIT],
        error_message=None if hidden else (outcome.stderr[:STORED_TEXT_LIMIT] or None),
    )


def _peak(outcomes: list[TestOutcome]) -> tuple[int | None, int | None]:
    times = [o.time_ms for o in outcomes if o.time_ms is not None]
    memory = [o.memory_kb for o in outcomes if o.memory_kb is not None]
    return (max(times) if times else None, max(memory) if memory else None)


def is_configured() -> bool:
    return bool(settings.JUDGE0_BASE_URL)


# ------------------------------------------------------------------ RUN
def run(db: Session, user: User, data: RunRequest) -> RunResult:
    problem, language = _validate(db, data.problem_id, data.language, data.source_code)
    run_rate_limiter.check(f"user:{user.id}", "Too many runs. Please wait a minute and try again.")
    if not is_configured():
        raise AppError(503, UNAVAILABLE_MESSAGE, code="EXECUTION_UNAVAILABLE")

    public = _official_cases(db, problem, include_hidden=False)
    custom = [
        JudgeCase(kind="custom", index=i, stdin=c.input, expected_output=c.expected_output)
        for i, c in enumerate(data.custom_cases, start=1)
    ]
    if not public and not custom:
        raise AppError(400, "This problem has no public test cases. Add a custom test case to run your code.", code="NO_TEST_CASES")

    with _one_at_a_time("run", user.id, "Your previous run is still in progress."):
        started = time.monotonic()
        message = None
        try:
            report = _execute(problem, language, _program(problem, language, data.source_code), public + custom, stop_on_failure=False)
        except judge0.JudgeUnavailable:
            report, message = RunReport(system_error=SubmissionStatus.SYSTEM_ERROR), UNAVAILABLE_MESSAGE
        except judge0.JudgeTimeout:
            report, message = RunReport(system_error=SubmissionStatus.EXECUTION_TIMEOUT), TIMEOUT_MESSAGE

    if report.compile_output or any(o.verdict == SubmissionStatus.COMPILE_ERROR.value for o in report.outcomes):
        verdict = SubmissionStatus.COMPILE_ERROR
    else:
        verdict = overall_verdict(report)
    if verdict == SubmissionStatus.SYSTEM_ERROR and message is None:
        message = UNAVAILABLE_MESSAGE
    public_outcomes = [o for o in report.outcomes if o.case.kind == "public"]
    runtime, memory = _peak(report.outcomes)
    limits = _limits(problem, language)
    logger.info(
        "run_finished user=%s problem=%s language=%s verdict=%s passed=%s/%s custom=%s duration_ms=%s",
        user.id, problem.id, language.value, verdict.value, sum(o.passed for o in public_outcomes), len(public),
        len(custom), round((time.monotonic() - started) * 1000),
    )
    return RunResult(
        verdict=verdict,
        passed_tests=sum(o.passed for o in public_outcomes),
        total_tests=len(public),
        runtime_ms=runtime,
        memory_kb=memory,
        compile_output=report.compile_output or None,
        message=message,
        time_limit_ms=round(limits.cpu_time_s * 1000),
        memory_limit_kb=limits.memory_kb,
        results=[_result_out(o, text_limit=settings.EXECUTION_MAX_OUTPUT_BYTES) for o in report.outcomes],
    )


# ------------------------------------------------------------------ SUBMIT
def expire_stuck_submissions(db: Session) -> int:
    """Resolve submissions left PENDING/RUNNING (e.g. the server restarted mid-judging)."""
    cutoff = datetime.now(UTC) - timedelta(seconds=settings.JUDGE0_TIMEOUT + 60)
    expired = 0
    for submission in db.scalars(select(Submission).where(Submission.status.in_(IN_PROGRESS_STATUSES))).all():
        submitted = submission.submitted_at
        if submitted.tzinfo is None:  # SQLite returns naive UTC timestamps
            submitted = submitted.replace(tzinfo=UTC)
        if submitted < cutoff:
            submission.status = SubmissionStatus.EXECUTION_TIMEOUT
            submission.error_message = TIMEOUT_MESSAGE
            submission.finished_at = datetime.now(UTC)
            expired += 1
    if expired:
        db.commit()
        logger.warning("expired_stuck_submissions count=%s", expired)
    return expired


def submit(db: Session, user: User, data: SubmitRequest) -> Submission:
    problem, language = _validate(db, data.problem_id, data.language, data.source_code)
    submit_rate_limiter.check(f"user:{user.id}", "Too many submissions. Please wait a minute and try again.")
    if not is_configured():
        raise AppError(503, UNAVAILABLE_MESSAGE, code="EXECUTION_UNAVAILABLE")
    cases = _official_cases(db, problem, include_hidden=True)
    if not cases:
        raise AppError(400, "This problem has no test cases yet, so it cannot be judged.", code="NO_TEST_CASES")

    with _one_at_a_time("submission", user.id, "Your previous submission is still being judged."):
        expire_stuck_submissions(db)
        in_progress = db.scalar(
            select(Submission.id).where(Submission.user_id == user.id, Submission.status.in_(IN_PROGRESS_STATUSES))
        )
        if in_progress is not None:
            raise AppError(409, "Your previous submission is still being judged.", code="SUBMISSION_IN_PROGRESS")

        limits = _limits(problem, language)
        submission = Submission(
            user_id=user.id,
            problem_id=problem.id,
            language=language,
            source_code=data.source_code.replace("\r\n", "\n"),
            status=SubmissionStatus.RUNNING,
            total_tests=len(cases),
            # Effective limits for this language, kept for the result page.
            time_limit_ms=round(limits.cpu_time_s * 1000),
            memory_limit_kb=limits.memory_kb,
            submitted_at=datetime.now(UTC),
        )
        db.add(submission)
        db.commit()  # recorded before judging, so it can never silently disappear
        started = time.monotonic()
        error_message = None
        try:
            report = _execute(problem, language, _program(problem, language, data.source_code), cases,
                              stop_on_failure=settings.EXECUTION_STOP_ON_FIRST_FAILURE)
        except judge0.JudgeUnavailable:
            report, error_message = RunReport(system_error=SubmissionStatus.SYSTEM_ERROR), UNAVAILABLE_MESSAGE
        except judge0.JudgeTimeout:
            report, error_message = RunReport(system_error=SubmissionStatus.EXECUTION_TIMEOUT), TIMEOUT_MESSAGE
        except Exception:  # never leave the row RUNNING
            logger.exception("submission_crashed id=%s", submission.id)
            report, error_message = RunReport(system_error=SubmissionStatus.SYSTEM_ERROR), UNAVAILABLE_MESSAGE

        verdict = overall_verdict(report)
        failing = next((o for o in report.official() if o.verdict != SubmissionStatus.ACCEPTED.value), None)
        if verdict == SubmissionStatus.SYSTEM_ERROR and error_message is None:
            error_message = UNAVAILABLE_MESSAGE
        elif verdict == SubmissionStatus.COMPILE_ERROR:
            error_message = report.compile_output[:settings.EXECUTION_MAX_OUTPUT_BYTES] or "Compilation failed."
        elif failing is not None and failing.case.kind == "public" and failing.stderr:
            error_message = failing.stderr[:STORED_TEXT_LIMIT]
        elif failing is not None and failing.case.kind == "hidden" and verdict != SubmissionStatus.WRONG_ANSWER:
            error_message = HIDDEN_RUNTIME_MESSAGE if verdict == SubmissionStatus.RUNTIME_ERROR else None

        runtime, memory = _peak(report.official())
        try:
            # ONE transaction: final verdict + per-test rows + the student's progress,
            # so a stored verdict can never exist without its progress update.
            submission.status = verdict
            submission.passed_tests = sum(o.passed for o in report.official())
            submission.runtime_ms = runtime
            submission.memory_kb = memory
            submission.error_message = error_message
            submission.test_results = [
                _stored_result(o)
                for o in report.official()
                # A compile error executed nothing; the compiler output is the result.
                if o.verdict != SubmissionStatus.COMPILE_ERROR.value
            ]
            submission.finished_at = datetime.now(UTC)
            progress_service.record_judged_submission(db, submission)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            logger.exception("submission_finalize_failed id=%s", submission.id)
            _mark_failed(db, submission.id)
        db.refresh(submission)

    logger.info(
        "submission_finished id=%s user=%s problem=%s language=%s status=%s passed=%s/%s duration_ms=%s",
        submission.id, user.id, problem.id, language.value, verdict.value, submission.passed_tests,
        submission.total_tests, round((time.monotonic() - started) * 1000),
    )
    return submission


def _mark_failed(db: Session, submission_id: int) -> None:
    """Best effort after a failed finalize: never leave the row RUNNING."""
    try:
        row = db.get(Submission, submission_id)
        if row is not None and row.status in IN_PROGRESS_STATUSES:
            row.status = SubmissionStatus.SYSTEM_ERROR
            row.error_message = UNAVAILABLE_MESSAGE
            row.finished_at = datetime.now(UTC)
            db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("submission_mark_failed_failed id=%s", submission_id)


# ------------------------------------------------------------------ health
_health_cache: dict[str, float | bool] = {"checked_at": 0.0, "available": False}
_HEALTH_TTL_SECONDS = 15


def check_available() -> bool:
    """Whether Judge0 answers right now (cached briefly; no details exposed)."""
    if not is_configured():
        return False
    now = time.monotonic()
    if now - float(_health_cache["checked_at"]) < _HEALTH_TTL_SECONDS:
        return bool(_health_cache["available"])
    client = get_judge_client()
    available = bool(client and client.is_available())
    if client:
        client.close()
    _health_cache.update(checked_at=now, available=available)
    return available
