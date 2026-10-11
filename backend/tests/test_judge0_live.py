"""Opt-in checks against a REAL Judge0 (compiles and runs code in its sandbox).

Skipped by default. With Judge0 running and JUDGE0_BASE_URL / JUDGE0_API_KEY in
backend/.env:

    JUDGE0_LIVE=1 pytest tests/test_judge0_live.py -v

Covers: every seeded problem's reference solution in C++/Java/Python through
its hidden harness, every verdict type, and sandbox containment (no network,
no backend secrets, no persistence, runaway programs are stopped).
"""

import os
import time

import pytest

from app.core.config import settings
from app.core.languages import LANGUAGES
from app.models.problem import ProgrammingLanguage
from app.models.submission import SubmissionStatus
from app.seed_data.problems import PROBLEMS
from app.services.judging.harness import build_program
from app.services.judging.judge0 import client_from_settings
from app.services.judging.runner import JudgeCase, limits_for, overall_verdict, run_cases
from tests.fixtures.reference_solutions import SOLUTIONS

pytestmark = pytest.mark.skipif(
    os.environ.get("JUDGE0_LIVE") != "1" or not settings.JUDGE0_BASE_URL,
    reason="Set JUDGE0_LIVE=1 and configure JUDGE0_BASE_URL to run against a real Judge0",
)


def _judge(language: ProgrammingLanguage, program: str, cases: list[tuple[str, str | None]], *, time_ms=2000, memory_kb=262144):
    client = client_from_settings()
    spec = LANGUAGES[language]
    report = run_cases(
        client,
        program=program,
        language=spec,
        cases=[JudgeCase("public", i, stdin, expected) for i, (stdin, expected) in enumerate(cases, start=1)],
        limits=limits_for(spec, time_ms, memory_kb, 1024),
        deadline=time.monotonic() + 120,
        stop_on_failure=False,
        max_output_bytes=64_000,
    )
    client.close()
    return report


def test_judge0_reachable():
    client = client_from_settings()
    assert client.is_available()
    client.close()


@pytest.mark.parametrize("language", list(ProgrammingLanguage))
@pytest.mark.parametrize("problem", PROBLEMS, ids=[p["slug"] for p in PROBLEMS])
def test_reference_solution_accepted(problem, language):
    program = build_program(SOLUTIONS[problem["slug"]][language.value], (problem.get("driver") or {}).get(language.value))
    cases = [(c["input_data"], c["expected_output"]) for c in problem["test_cases"]]
    report = _judge(language, program, cases)
    detail = [(o.case.index, o.verdict, o.stdout[:200], o.stderr[:300], o.compile_output[:300]) for o in report.outcomes]
    assert overall_verdict(report) == SubmissionStatus.ACCEPTED, detail


@pytest.mark.parametrize(
    "language, source, verdict",
    [
        (ProgrammingLanguage.PYTHON, "print(10)\n", SubmissionStatus.WRONG_ANSWER),
        (ProgrammingLanguage.CPP, "int main() { return 0 }\n", SubmissionStatus.COMPILE_ERROR),
        (ProgrammingLanguage.JAVA, "public class Main { public static void main(String[] a) { int x = ; } }\n", SubmissionStatus.COMPILE_ERROR),
        (ProgrammingLanguage.PYTHON, "print(1 // 0)\n", SubmissionStatus.RUNTIME_ERROR),
        (ProgrammingLanguage.CPP, "#include <cstdio>\nint main() { int *p = nullptr; *p = 1; return 0; }\n", SubmissionStatus.RUNTIME_ERROR),
        (ProgrammingLanguage.PYTHON, "while True:\n    pass\n", SubmissionStatus.TIME_LIMIT_EXCEEDED),
        (ProgrammingLanguage.CPP, "int main() { volatile long long i = 0; while (true) i++; }\n", SubmissionStatus.TIME_LIMIT_EXCEEDED),
        (ProgrammingLanguage.PYTHON, "x = bytearray(1024 * 1024 * 1024)\nprint(len(x))\n", SubmissionStatus.MEMORY_LIMIT_EXCEEDED),
        (ProgrammingLanguage.PYTHON, "import sys\nwhile True:\n    sys.stdout.write('x' * 65536)\n", SubmissionStatus.OUTPUT_LIMIT_EXCEEDED),
    ],
)
def test_verdicts(language, source, verdict):
    report = _judge(language, source, [("2 3", "5")], time_ms=1000, memory_kb=65536)
    assert overall_verdict(report) == verdict, [(o.verdict, o.stderr[:300], o.compile_output[:300]) for o in report.outcomes]


def test_sandbox_has_no_network():
    source = (
        "import socket\ntry:\n    socket.create_connection(('1.1.1.1', 53), timeout=3)\n    print('NETWORK-OPEN')\n"
        "except Exception as exc:\n    print('blocked', type(exc).__name__)\n"
    )
    report = _judge(ProgrammingLanguage.PYTHON, source, [("", None)])
    assert "NETWORK-OPEN" not in report.outcomes[0].stdout


def test_sandbox_cannot_reach_codearena_services():
    source = (
        "import socket\nfor host, port in [('127.0.0.1', 8000), ('host.docker.internal', 8000), ('172.17.0.1', 5432), ('db', 5432), ('redis', 6379)]:\n"
        "    try:\n        socket.create_connection((host, port), timeout=2)\n        print('REACHED', host, port)\n"
        "    except Exception:\n        pass\nprint('done')\n"
    )
    report = _judge(ProgrammingLanguage.PYTHON, source, [("", None)])
    assert "REACHED" not in report.outcomes[0].stdout


def test_sandbox_has_no_backend_secrets():
    source = "import os\nprint(sorted(os.environ.items()))\n"
    out = _judge(ProgrammingLanguage.PYTHON, source, [("", None)]).outcomes[0].stdout
    for secret in filter(None, [settings.JWT_SECRET, settings.JUDGE0_API_KEY, settings.DATABASE_URL]):
        assert secret not in out
    for name in ("DATABASE_URL", "JWT_SECRET", "JUDGE0_API_KEY", "POSTGRES_PASSWORD", "REDIS_PASSWORD", "AUTHN_TOKEN"):
        assert name not in out


def test_sandbox_does_not_persist_files():
    write = "open('/tmp/codearena_probe.txt', 'w').write('persisted')\nprint('written')\n"
    read = "import os\nprint(os.path.exists('/tmp/codearena_probe.txt'))\n"
    _judge(ProgrammingLanguage.PYTHON, write, [("", None)])
    assert _judge(ProgrammingLanguage.PYTHON, read, [("", None)]).outcomes[0].stdout.strip() == "False"


def test_fork_bomb_is_contained():
    source = "import os\nwhile True:\n    try:\n        os.fork()\n    except OSError:\n        pass\n"
    report = _judge(ProgrammingLanguage.PYTHON, source, [("", None)], time_ms=1000)
    assert overall_verdict(report) in (SubmissionStatus.TIME_LIMIT_EXCEEDED, SubmissionStatus.RUNTIME_ERROR)
