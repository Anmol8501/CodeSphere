"""Runs a program against test cases through the judge and decides verdicts.

The verdict of a run is the verdict of the first test that does not pass
(tests are executed in order). A compile error stops everything, because the
program is the same for every test. Hidden tests are executed like any other
test, but their data and outputs never leave this module in a result that is
returned to students (see `TestOutcome.public_view`).
"""

import time
from dataclasses import dataclass, field

from app.core.languages import LanguageSpec
from app.models.submission import SubmissionStatus
from app.services.judging.comparator import outputs_match
from app.services.judging.judge0 import ExecutionLimits, Judge0Client

ACCEPTED = SubmissionStatus.ACCEPTED
# Custom (student-written) case without an expected output: it ran, nothing to compare.
EXECUTED = "EXECUTED"


@dataclass
class JudgeCase:
    kind: str  # "public" | "hidden" | "custom"
    index: int  # official tests: 1-based position among them; custom cases: 1-based among custom
    stdin: str
    expected_output: str | None  # None = do not compare (custom case without expectation)
    test_case_id: int | None = None  # official tests only


@dataclass
class TestOutcome:
    case: JudgeCase
    verdict: str  # SubmissionStatus value or EXECUTED
    stdout: str = ""
    stderr: str = ""
    compile_output: str = ""
    time_ms: int | None = None
    memory_kb: int | None = None

    @property
    def passed(self) -> bool:
        return self.verdict in (ACCEPTED.value, EXECUTED)


@dataclass
class RunReport:
    outcomes: list[TestOutcome] = field(default_factory=list)
    compile_output: str = ""
    system_error: SubmissionStatus | None = None  # SYSTEM_ERROR / EXECUTION_TIMEOUT
    duration_ms: int = 0

    def official(self) -> list[TestOutcome]:
        return [o for o in self.outcomes if o.case.kind != "custom"]


def limits_for(language: LanguageSpec, time_limit_ms: int, memory_limit_kb: int, max_output_kb: int) -> ExecutionLimits:
    cpu = min(round(time_limit_ms / 1000 * language.time_factor, 2), 15.0)
    return ExecutionLimits(
        cpu_time_s=cpu,
        wall_time_s=min(round(cpu * 2 + 1, 2), 20.0),
        memory_kb=min(memory_limit_kb, 512_000),
        max_output_kb=max_output_kb,
    )


def run_cases(
    client: Judge0Client,
    *,
    program: str,
    language: LanguageSpec,
    cases: list[JudgeCase],
    limits: ExecutionLimits,
    deadline: float,
    stop_on_failure: bool,
    max_output_bytes: int,
) -> RunReport:
    """Execute `cases` in order. Raises JudgeUnavailable / JudgeTimeout to the caller."""
    started = time.monotonic()
    report = RunReport()
    for case in cases:
        result = client.execute(
            source_code=program, language_id=language.judge0_id, stdin=case.stdin, limits=limits, deadline=deadline
        )
        mapped = result.verdict(limits.memory_kb)
        if mapped == SubmissionStatus.SYSTEM_ERROR:
            report.system_error = SubmissionStatus.SYSTEM_ERROR
            break
        if mapped is None:
            if case.expected_output is None:
                verdict = EXECUTED
            else:
                verdict = (ACCEPTED if outputs_match(result.stdout, case.expected_output) else SubmissionStatus.WRONG_ANSWER).value
        else:
            verdict = mapped.value
        outcome = TestOutcome(
            case=case,
            verdict=verdict,
            stdout=result.stdout[:max_output_bytes],
            stderr=result.stderr[:max_output_bytes],
            compile_output=result.compile_output[:max_output_bytes],
            time_ms=result.time_ms,
            memory_kb=result.memory_kb,
        )
        report.outcomes.append(outcome)
        if verdict == SubmissionStatus.COMPILE_ERROR.value:
            report.compile_output = outcome.compile_output or result.message
            break  # same program for every test
        if stop_on_failure and not outcome.passed and case.kind != "custom":
            break
    report.duration_ms = round((time.monotonic() - started) * 1000)
    return report


def overall_verdict(report: RunReport) -> SubmissionStatus:
    """Verdict over the official (public + hidden) tests that were executed."""
    if report.system_error:
        return report.system_error
    for outcome in report.official():
        if outcome.verdict != ACCEPTED.value:
            return SubmissionStatus(outcome.verdict)
    return ACCEPTED
