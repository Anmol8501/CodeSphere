"""Add the hidden execution harnesses to seeded problems in an existing database.

Usage (from backend/, after `alembic upgrade head`):
    python -m app.utils.seed_execution

Databases seeded before Phase 5 have starter code but no harness, so their
function-style problems could not be judged. This fills `driver_code` for the
seeded problems, idempotently and conservatively: a harness is only added
where none exists yet AND the starter code is still exactly the seeded one (if
an admin changed the starter code, the harness might no longer match it).
"""

import sys

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.problem import Problem, StarterCode
from app.seed_data.problems import PROBLEMS


def _normalized(code: str) -> str:
    return code.replace("\r\n", "\n").rstrip() + "\n"


def backfill(db) -> dict[str, int]:
    added = skipped_existing = skipped_edited = 0
    for data in PROBLEMS:
        drivers = data.get("driver") or {}
        if not drivers:
            continue  # full-program problems need no harness
        problem_id = db.scalar(select(Problem.id).where(Problem.slug == data["slug"]))
        if problem_id is None:
            continue
        for language, driver in drivers.items():
            row = db.scalar(select(StarterCode).where(StarterCode.problem_id == problem_id, StarterCode.language == language))
            if row is None:
                continue
            if row.driver_code:
                skipped_existing += 1
            elif _normalized(row.starter_code) != _normalized(data["starter"][language]):
                skipped_edited += 1
            else:
                row.driver_code = driver
                added += 1
    db.commit()
    return {"added": added, "already_set": skipped_existing, "skipped_edited": skipped_edited}


def main() -> int:
    with SessionLocal() as db:
        result = backfill(db)
    print(
        f"[seed] Execution harnesses: {result['added']} added, {result['already_set']} already set, "
        f"{result['skipped_edited']} skipped (starter code was edited)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
