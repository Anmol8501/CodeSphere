"""Recompute student progress from the submissions table, or audit it.

    python -m app.utils.rebuild_progress          # rebuild (idempotent), then audit
    python -m app.utils.rebuild_progress --check  # audit only; exit code 1 on differences

Progress is normally maintained in the same transaction as each verdict; this
is for backfills and consistency checks. It never deletes submissions and
never creates duplicate progress rows.
"""

import sys

from app.db.session import SessionLocal
from app.services import progress_service


def main(argv: list[str]) -> int:
    with SessionLocal() as db:
        if "--check" not in argv:
            written = progress_service.rebuild_progress(db)
            print(f"Rebuilt {written} progress row(s) from judged submissions.")
        problems = progress_service.audit_progress(db)
    if problems:
        print(f"{len(problems)} inconsistency(ies):")
        for line in problems[:50]:
            print(f"  - {line}")
        return 1
    print("Progress is consistent with the submissions table.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
