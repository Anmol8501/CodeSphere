"""Student progress: solved state, attempts, statistics, streaks and activity.

Definitions (see docs/ANALYTICS.md):

  judged submission  an official SUBMIT whose final status is a verdict on the
                     code: ACCEPTED, WRONG_ANSWER, COMPILE_ERROR, RUNTIME_ERROR,
                     TIME/MEMORY/OUTPUT_LIMIT_EXCEEDED. RUN is never stored.
                     SYSTEM_ERROR / EXECUTION_TIMEOUT (judge failures) and
                     PENDING / RUNNING count for nothing.
  attempt            one judged submission.
  SOLVED             the student has >= 1 ACCEPTED submission on the problem;
                     ATTEMPTED: judged submissions but none accepted.
  acceptance rate    accepted / judged submissions * 100 (submission-based).
  coding day         a calendar day (APP_TIMEZONE) with >= 1 judged submission.
  current streak     consecutive coding days ending today, or ending yesterday
                     while today has no submission yet; otherwise 0.
  longest streak     the longest run of consecutive coding days ever.

Solved / total counts (overall, by difficulty, by topic) use PUBLISHED
problems, so "x / y" can never exceed 100%.

Per-problem progress lives in `user_problem_progress` and is updated in the
SAME transaction that stores a submission's final verdict
(record_judged_submission). `rebuild_progress` recomputes it from the
submissions table at any time and `audit_progress` reports any difference.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import ColumnElement, and_, case, exists, func, select, update
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import Session

from app.core.clock import as_date, local_date_expr, local_today, start_of_day_utc, to_utc
from app.core.config import settings
from app.models.problem import Problem, ProblemDifficulty, ProblemStatus, ProgrammingLanguage
from app.models.progress import UserProblemProgress
from app.models.submission import JUDGED_STATUSES, Submission, SubmissionStatus
from app.models.topic import Topic
from app.schemas.problem import ProblemStats, ProgressFilter, TopicRef, UserProblemProgressOut, UserProblemStatus
from app.schemas.progress import (
    ActivityItem,
    DifficultyCount,
    DifficultyProgress,
    Heatmap,
    HeatmapDay,
    LanguageStat,
    ProblemRef,
    ProgressOverview,
    Recommendation,
    RecommendedProblem,
    StreakInfo,
    TopicProgressItem,
)
from app.services import topic_service

ACCEPTED = SubmissionStatus.ACCEPTED
STREAK_LOOKBACK_DAYS = 365
DIFFICULTY_ORDER = {ProblemDifficulty.EASY: 0, ProblemDifficulty.MEDIUM: 1, ProblemDifficulty.HARD: 2}


def judged() -> ColumnElement[bool]:
    return Submission.status.in_(JUDGED_STATUSES)


def rate(part: int, whole: int) -> float:
    """part / whole as a percentage with one decimal (0 when whole is 0)."""
    return round(part * 100 / whole, 1) if whole else 0.0


def _valid_metric(value: int | None) -> bool:
    return value is not None and value >= 0


def _min(current: int | None, candidate: int | None) -> int | None:
    if candidate is None or candidate < 0:
        return current
    return candidate if current is None else min(current, candidate)


# ================================================================== write path
def _locked_progress_row(db: Session, user_id: int, problem_id: int) -> UserProblemProgress:
    """The (user, problem) progress row, created if missing and locked FOR UPDATE.

    INSERT ... ON CONFLICT DO NOTHING makes concurrent first submissions safe:
    exactly one row exists, and the row lock serialises the counter updates.
    """
    dialect = db.get_bind().dialect.name
    insert = postgresql.insert if dialect == "postgresql" else sqlite.insert
    db.execute(
        insert(UserProblemProgress)
        .values(user_id=user_id, problem_id=problem_id, attempt_count=0, accepted_count=0)
        .on_conflict_do_nothing(index_elements=["user_id", "problem_id"])
    )
    return db.scalars(
        select(UserProblemProgress)
        .where(UserProblemProgress.user_id == user_id, UserProblemProgress.problem_id == problem_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).one()


def record_judged_submission(db: Session, submission: Submission) -> UserProblemProgress | None:
    """Fold a submission's final verdict into the student's progress.

    Call after setting the final status, inside the same transaction; the
    caller commits. Infrastructure failures and unfinished submissions change
    nothing. Marks the submission as first accepted when it solves the problem.
    """
    if submission.status not in JUDGED_STATUSES:
        return None
    progress = _locked_progress_row(db, submission.user_id, submission.problem_id)
    at = to_utc(submission.submitted_at)
    progress.attempt_count += 1
    first, last = progress.first_attempt_at, progress.last_attempt_at
    progress.first_attempt_at = at if first is None else min(to_utc(first), at)
    progress.last_attempt_at = at if last is None else max(to_utc(last), at)
    if submission.status == ACCEPTED:
        progress.accepted_count += 1
        # "First accepted" means earliest submitted (ties: lowest id), even if an
        # earlier submission happens to finish judging after a later one.
        current = db.execute(
            select(Submission.id, Submission.submitted_at).where(
                Submission.user_id == submission.user_id,
                Submission.problem_id == submission.problem_id,
                Submission.is_first_accepted.is_(True),
                Submission.id != submission.id,
            )
        ).first()
        if current is None or (at, submission.id) < (to_utc(current.submitted_at), current.id):
            if current is not None:
                db.execute(update(Submission).where(Submission.id == current.id).values(is_first_accepted=False))
            submission.is_first_accepted = True
        progress.solved_at = at if progress.solved_at is None else min(to_utc(progress.solved_at), at)
        progress.best_runtime_ms = _min(progress.best_runtime_ms, submission.runtime_ms)
        progress.best_memory_kb = _min(progress.best_memory_kb, submission.memory_kb)
    return progress


# ================================================================== rebuild / audit
def _expected_progress(db: Session, user_ids: list[int] | None) -> dict[tuple[int, int], dict]:
    accepted = Submission.status == ACCEPTED
    query = (
        select(
            Submission.user_id,
            Submission.problem_id,
            func.count(),
            func.sum(case((accepted, 1), else_=0)),
            func.min(Submission.submitted_at),
            func.max(Submission.submitted_at),
            func.min(case((accepted, Submission.submitted_at))),
            func.min(case((and_(accepted, Submission.runtime_ms >= 0), Submission.runtime_ms))),
            func.min(case((and_(accepted, Submission.memory_kb >= 0), Submission.memory_kb))),
        )
        .where(judged())
        .group_by(Submission.user_id, Submission.problem_id)
    )
    if user_ids is not None:
        query = query.where(Submission.user_id.in_(user_ids))
    expected: dict[tuple[int, int], dict[str, Any]] = {}
    rows: Any = db.execute(query).all()
    for user_id, problem_id, attempts, accepted_count, first, last, solved, runtime, memory in rows:
        expected[(user_id, problem_id)] = {
            "attempt_count": attempts,
            "accepted_count": int(accepted_count or 0),
            "first_attempt_at": to_utc(first),
            "last_attempt_at": to_utc(last),
            "solved_at": to_utc(solved) if solved is not None else None,
            "best_runtime_ms": runtime,
            "best_memory_kb": memory,
        }
    return expected


def _expected_first_accepted(db: Session, user_ids: list[int] | None) -> set[int]:
    query = (
        select(Submission.id, Submission.user_id, Submission.problem_id)
        .where(Submission.status == ACCEPTED)
        .order_by(Submission.user_id, Submission.problem_id, Submission.submitted_at, Submission.id)
    )
    if user_ids is not None:
        query = query.where(Submission.user_id.in_(user_ids))
    seen: set[tuple[int, int]] = set()
    first: set[int] = set()
    for submission_id, user_id, problem_id in db.execute(query).all():
        if (user_id, problem_id) not in seen:
            seen.add((user_id, problem_id))
            first.add(submission_id)
    return first


def rebuild_progress(db: Session, user_ids: list[int] | None = None) -> int:
    """Recompute progress rows and first-accepted flags from submissions. Idempotent.

    Existing rows are updated in place (never duplicated). Commits.
    Returns the number of progress rows written.
    """
    expected = _expected_progress(db, user_ids)
    stored_query = select(UserProblemProgress)
    if user_ids is not None:
        stored_query = stored_query.where(UserProblemProgress.user_id.in_(user_ids))
    stored = {(p.user_id, p.problem_id): p for p in db.scalars(stored_query).all()}
    empty = dict.fromkeys(
        ("first_attempt_at", "last_attempt_at", "solved_at", "best_runtime_ms", "best_memory_kb"), None
    ) | {"attempt_count": 0, "accepted_count": 0}
    written = 0
    for key in expected.keys() | stored.keys():
        values = expected.get(key, empty)
        row = stored.get(key)
        if row is None:
            db.add(UserProblemProgress(user_id=key[0], problem_id=key[1], **values))
        else:
            for field, value in values.items():
                setattr(row, field, value)
        written += 1

    first = _expected_first_accepted(db, user_ids)
    clear = update(Submission).where(Submission.is_first_accepted.is_(True))
    if user_ids is not None:
        clear = clear.where(Submission.user_id.in_(user_ids))
    db.execute(clear.values(is_first_accepted=False))
    if first:
        db.execute(update(Submission).where(Submission.id.in_(first)).values(is_first_accepted=True))
    db.commit()
    return written


def audit_progress(db: Session) -> list[str]:
    """Differences between stored progress and the submissions table (empty = consistent)."""
    problems: list[str] = []
    expected = _expected_progress(db, None)
    stored = {(p.user_id, p.problem_id): p for p in db.scalars(select(UserProblemProgress)).all()}
    for key in expected.keys() | stored.keys():
        want = expected.get(key)
        row = stored.get(key)
        if want is None:
            if row is not None and row.attempt_count:
                problems.append(f"user {key[0]} problem {key[1]}: progress row has attempts but no judged submissions")
            continue
        if row is None:
            problems.append(f"user {key[0]} problem {key[1]}: progress row missing")
            continue
        for field, value in want.items():
            have = getattr(row, field)
            if isinstance(have, datetime):
                have = to_utc(have)
            if have != value:
                problems.append(f"user {key[0]} problem {key[1]}: {field} is {have!r}, expected {value!r}")
    first = _expected_first_accepted(db, None)
    flagged = set(db.scalars(select(Submission.id).where(Submission.is_first_accepted.is_(True))).all())
    for submission_id in sorted(first - flagged):
        problems.append(f"submission {submission_id}: should be the first accepted")
    for submission_id in sorted(flagged - first):
        problems.append(f"submission {submission_id}: wrongly marked first accepted")
    return problems


# ================================================================== per-problem status
def _status(progress: UserProblemProgress | None) -> UserProblemStatus:
    if progress is None or not progress.attempt_count:
        return "UNSOLVED"
    return "SOLVED" if progress.solved_at is not None else "ATTEMPTED"


def statuses_for(db: Session, user_id: int, problem_ids: list[int]) -> dict[int, UserProblemStatus]:
    if not problem_ids:
        return {}
    rows = db.scalars(
        select(UserProblemProgress).where(
            UserProblemProgress.user_id == user_id, UserProblemProgress.problem_id.in_(problem_ids)
        )
    ).all()
    return {row.problem_id: _status(row) for row in rows}


def problem_progress(db: Session, user_id: int, problem_id: int) -> UserProblemProgressOut:
    row = db.scalar(
        select(UserProblemProgress).where(
            UserProblemProgress.user_id == user_id, UserProblemProgress.problem_id == problem_id
        )
    )
    if row is None:
        return UserProblemProgressOut()
    return UserProblemProgressOut(
        status=_status(row),
        attempts=row.attempt_count,
        accepted_submissions=row.accepted_count,
        first_attempt_at=row.first_attempt_at,
        last_attempt_at=row.last_attempt_at,
        solved_at=row.solved_at,
        best_runtime_ms=row.best_runtime_ms,
        best_memory_kb=row.best_memory_kb,
    )


def progress_filter(user_id: int, progress: ProgressFilter) -> ColumnElement[bool]:
    """WHERE clause on Problem for the problem-list Status filter (server-side)."""
    mine = and_(UserProblemProgress.user_id == user_id, UserProblemProgress.problem_id == Problem.id)
    solved = exists().where(mine, UserProblemProgress.solved_at.is_not(None))
    if progress == "solved":
        return solved
    if progress == "attempted":
        return exists().where(mine, UserProblemProgress.attempt_count > 0, UserProblemProgress.solved_at.is_(None))
    return ~solved  # "unsolved": everything not solved yet (attempted or not)


def problem_stats(db: Session, problem_ids: list[int]) -> dict[int, ProblemStats]:
    if not problem_ids:
        return {}
    rows: Any = db.execute(
        select(
            UserProblemProgress.problem_id,
            func.sum(case((UserProblemProgress.solved_at.is_not(None), 1), else_=0)),
            func.sum(UserProblemProgress.attempt_count),
            func.sum(UserProblemProgress.accepted_count),
        )
        .where(UserProblemProgress.problem_id.in_(problem_ids))
        .group_by(UserProblemProgress.problem_id)
    ).all()
    stats = {}
    for problem_id, solved_by, attempts, accepted in rows:
        attempts, accepted = int(attempts or 0), int(accepted or 0)
        stats[problem_id] = ProblemStats(
            solved_by=int(solved_by or 0),
            attempts=attempts,
            accepted=accepted,
            acceptance_rate=rate(accepted, attempts) if attempts else None,
        )
    return stats


def solved_counts_by_topic(db: Session, user_id: int) -> dict[int, int]:
    """{topic_id: published problems the student has solved}."""
    rows = db.execute(
        select(Problem.topic_id, func.count())
        .join(UserProblemProgress, UserProblemProgress.problem_id == Problem.id)
        .where(
            UserProblemProgress.user_id == user_id,
            UserProblemProgress.solved_at.is_not(None),
            Problem.status == ProblemStatus.PUBLISHED,
        )
        .group_by(Problem.topic_id)
    ).all()
    return dict(rows)


# ================================================================== statistics
def _published_progress(db: Session, user_id: int):
    """(problem_id, difficulty, topic_id, attempted?, solved?) for published problems the student touched."""
    return db.execute(
        select(
            Problem.id,
            Problem.difficulty,
            Problem.topic_id,
            UserProblemProgress.attempt_count,
            UserProblemProgress.solved_at,
        )
        .join(UserProblemProgress, UserProblemProgress.problem_id == Problem.id)
        .where(UserProblemProgress.user_id == user_id, Problem.status == ProblemStatus.PUBLISHED)
    ).all()


def submission_totals(db: Session, user_id: int) -> tuple[int, int]:
    """(judged submissions, accepted submissions) across every problem."""
    total, accepted = db.execute(
        select(
            func.coalesce(func.sum(UserProblemProgress.attempt_count), 0),
            func.coalesce(func.sum(UserProblemProgress.accepted_count), 0),
        ).where(UserProblemProgress.user_id == user_id)
    ).one()
    return int(total), int(accepted)


def overview(db: Session, user_id: int) -> ProgressOverview:
    total_problems = db.scalar(select(func.count(Problem.id)).where(Problem.status == ProblemStatus.PUBLISHED)) or 0
    rows = _published_progress(db, user_id)
    solved = sum(1 for r in rows if r.solved_at is not None)
    attempted = sum(1 for r in rows if r.solved_at is None and r.attempt_count > 0)
    total, accepted = submission_totals(db, user_id)
    return ProgressOverview(
        total_problems=total_problems,
        solved_problems=solved,
        attempted_problems=attempted,
        total_submissions=total,
        accepted_submissions=accepted,
        acceptance_rate=rate(accepted, total),
    )


def difficulty_progress(db: Session, user_id: int) -> DifficultyProgress:
    totals = dict(
        db.execute(
            select(Problem.difficulty, func.count())
            .where(Problem.status == ProblemStatus.PUBLISHED)
            .group_by(Problem.difficulty)
        ).all()
    )
    solved: dict[ProblemDifficulty, int] = defaultdict(int)
    for row in _published_progress(db, user_id):
        if row.solved_at is not None:
            solved[row.difficulty] += 1

    def count(level: ProblemDifficulty) -> DifficultyCount:
        total = totals.get(level, 0)
        return DifficultyCount(total=total, solved=solved[level], percentage=rate(solved[level], total))

    return DifficultyProgress(
        easy=count(ProblemDifficulty.EASY),
        medium=count(ProblemDifficulty.MEDIUM),
        hard=count(ProblemDifficulty.HARD),
    )


def topic_progress(db: Session, user_id: int) -> list[TopicProgressItem]:
    topics = topic_service.list_topics(db)  # same topics as the learning path
    totals = dict(
        db.execute(
            select(Problem.topic_id, func.count())
            .where(Problem.status == ProblemStatus.PUBLISHED)
            .group_by(Problem.topic_id)
        ).all()
    )
    solved: dict[int, int] = defaultdict(int)
    attempted: dict[int, int] = defaultdict(int)
    for row in _published_progress(db, user_id):
        if row.solved_at is not None:
            solved[row.topic_id] += 1
        elif row.attempt_count > 0:
            attempted[row.topic_id] += 1
    return [
        TopicProgressItem(
            topic=TopicRef(id=t.id, name=t.name, slug=t.slug),
            total_problems=totals.get(t.id, 0),
            solved_problems=solved[t.id],
            attempted_problems=attempted[t.id],
            percentage=rate(solved[t.id], totals.get(t.id, 0)),
        )
        for t in topics
    ]


def language_stats(db: Session, user_id: int) -> list[LanguageStat]:
    accepted = Submission.status == ACCEPTED
    grouped: Any = db.execute(
        select(
            Submission.language,
            func.count(),
            func.sum(case((accepted, 1), else_=0)),
            func.count(func.distinct(case((accepted, Submission.problem_id)))),
        )
        .where(Submission.user_id == user_id, judged())
        .group_by(Submission.language)
    ).all()
    rows = {language: (int(total), int(acc or 0), int(solved or 0)) for language, total, acc, solved in grouped}
    stats = []
    for language in ProgrammingLanguage:
        total, acc, solved = rows.get(language, (0, 0, 0))
        stats.append(
            LanguageStat(
                language=language,
                submissions=total,
                accepted=acc,
                acceptance_rate=rate(acc, total) if total else None,
                solved_problems=solved,
            )
        )
    return stats


# ================================================================== days, streaks, heatmap
def coding_days(db: Session, user_ids: list[int], since: date | None = None) -> dict[int, dict[date, int]]:
    """{user_id: {local date: judged submissions}} using one GROUP BY query."""
    if not user_ids:
        return {}
    day = local_date_expr(db, Submission.submitted_at)
    query = (
        select(Submission.user_id, day, func.count())
        .where(Submission.user_id.in_(user_ids), judged())
        .group_by(Submission.user_id, day)
    )
    if since is not None:
        query = query.where(Submission.submitted_at >= start_of_day_utc(since))
    result: dict[int, dict[date, int]] = {uid: {} for uid in user_ids}
    rows: Any = db.execute(query).all()
    for user_id, value, count in rows:
        result[user_id][as_date(value)] = count
    return result


def compute_streaks(days: set[date], today: date) -> tuple[int, int, bool]:
    """(current streak, longest streak, active today) from a set of coding days."""
    active_today = today in days
    current = 0
    cursor = today if active_today else today - timedelta(days=1)
    while cursor in days:
        current += 1
        cursor -= timedelta(days=1)
    longest = run = 0
    previous: date | None = None
    for day in sorted(days):
        run = run + 1 if previous is not None and day - previous == timedelta(days=1) else 1
        longest = max(longest, run)
        previous = day
    return current, longest, active_today


def streak(db: Session, user_id: int, today: date | None = None) -> StreakInfo:
    today = today or local_today()
    days = coding_days(db, [user_id])[user_id]  # all time, for the longest streak
    current, longest, active_today = compute_streaks(set(days), today)
    window_start = today - timedelta(days=STREAK_LOOKBACK_DAYS - 1)
    return StreakInfo(
        current_streak=current,
        longest_streak=longest,
        active_today=active_today,
        last_active_date=max((d for d in days if d <= today), default=None),
        activity_dates=sorted(d for d in days if window_start <= d <= today),
        timezone=settings.APP_TIMEZONE,
    )


def current_streaks(db: Session, user_ids: list[int], today: date | None = None) -> dict[int, int]:
    """Current streak for many students at once (one grouped query)."""
    today = today or local_today()
    # A current streak can only be as long as the lookback window.
    per_user = coding_days(db, user_ids, since=today - timedelta(days=STREAK_LOOKBACK_DAYS))
    return {uid: compute_streaks(set(days), today)[0] for uid, days in per_user.items()}


def heatmap(db: Session, user_id: int, days: int = 365, today: date | None = None) -> Heatmap:
    today = today or local_today()
    start = today - timedelta(days=days - 1)
    counts = coding_days(db, [user_id], since=start)[user_id]
    series = [
        HeatmapDay(date=start + timedelta(days=i), submission_count=counts.get(start + timedelta(days=i), 0))
        for i in range(days)
    ]
    return Heatmap(
        start_date=start,
        end_date=today,
        timezone=settings.APP_TIMEZONE,
        total_submissions=sum(d.submission_count for d in series),
        active_days=sum(1 for d in series if d.submission_count),
        days=series,
    )


# ================================================================== activity
def activity(db: Session, user_id: int, limit: int = 20) -> list[ActivityItem]:
    rows = db.execute(
        select(
            Submission.id,
            Submission.status,
            Submission.language,
            Submission.submitted_at,
            Submission.is_first_accepted,
            Problem.id,
            Problem.slug,
            Problem.title,
            Problem.difficulty,
        )
        .join(Problem, Problem.id == Submission.problem_id)
        .where(Submission.user_id == user_id, judged())
        .order_by(Submission.submitted_at.desc(), Submission.id.desc())
        .limit(limit)
    ).all()
    items = []
    for sid, status, language, submitted_at, first, pid, slug, title, difficulty in rows:
        kind = "SOLVED" if first else "ACCEPTED" if status == ACCEPTED else "ATTEMPTED"
        items.append(
            ActivityItem(
                submission_id=sid,
                type=kind,
                verdict=status,
                language=language,
                problem=ProblemRef(id=pid, slug=slug, title=title, difficulty=difficulty),
                occurred_at=to_utc(submitted_at),
            )
        )
    return items


# ================================================================== recommendations
def recommendations(db: Session, user_id: int, limit: int = 3) -> list[Recommendation]:
    """Rule-based "continue solving" suggestions from the student's real progress.

    1. RESUME          the most recently attempted problem that is still unsolved.
    2. CONTINUE_TOPIC  for each topic in progress (some but not all problems
                       solved), in learning-path order: its easiest unsolved problem.
    3. START_TOPIC     the next topics not started yet, in learning-path order:
                       their easiest problem.
    Easiest = EASY before MEDIUM before HARD, then the oldest problem.
    """
    problems = db.execute(
        select(Problem.id, Problem.slug, Problem.title, Problem.difficulty, Topic.id, Topic.name, Topic.slug)
        .join(Topic, Topic.id == Problem.topic_id)
        .where(Problem.status == ProblemStatus.PUBLISHED, Topic.is_active.is_(True))
        .order_by(Topic.order_index, Topic.id)
    ).all()
    if not problems:
        return []
    mine = {
        row.problem_id: row
        for row in db.scalars(select(UserProblemProgress).where(UserProblemProgress.user_id == user_id)).all()
    }

    def solved(pid: int) -> bool:
        return pid in mine and mine[pid].solved_at is not None

    by_topic: dict[int, list] = defaultdict(list)
    topic_order: list[int] = []
    for row in problems:
        if row[4] not in by_topic:
            topic_order.append(row[4])
        by_topic[row[4]].append(row)
    for rows in by_topic.values():
        rows.sort(key=lambda r: (DIFFICULTY_ORDER[r[3]], r[0]))

    def to_problem(row) -> RecommendedProblem:
        return RecommendedProblem(
            id=row[0], slug=row[1], title=row[2], difficulty=row[3], topic=TopicRef(id=row[4], name=row[5], slug=row[6])
        )

    chosen: list[Recommendation] = []
    used: set[int] = set()

    def add(row, reason, message) -> None:
        if len(chosen) < limit and row[0] not in used:
            used.add(row[0])
            chosen.append(Recommendation(problem=to_problem(row), reason=reason, message=message))

    attempted = [
        (mine[r[0]].last_attempt_at, r) for r in problems if r[0] in mine and mine[r[0]].attempt_count and not solved(r[0])
    ]
    if attempted:
        _, row = max(attempted, key=lambda item: (to_utc(item[0]) if item[0] else datetime.min, item[1][0]))
        attempts = mine[row[0]].attempt_count
        add(row, "RESUME", f"You have tried this {attempts} time{'s' if attempts != 1 else ''}. Pick it back up.")

    for topic_id in topic_order:
        rows = by_topic[topic_id]
        done = sum(1 for r in rows if solved(r[0]))
        if 0 < done < len(rows):
            pick = next((r for r in rows if not solved(r[0]) and r[0] not in used), None)
            if pick is not None:
                add(pick, "CONTINUE_TOPIC", f"Next in {pick[5]}: {done} of {len(rows)} solved.")
    for topic_id in topic_order:
        rows = by_topic[topic_id]
        if not any(solved(r[0]) for r in rows):
            pick = next((r for r in rows if r[0] not in used), None)
            if pick is not None:
                add(pick, "START_TOPIC", f"Start {pick[5]} with its easiest problem.")
    return chosen
