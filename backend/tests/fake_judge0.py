"""A Judge0 *test double* for the backend test suite.

It speaks Judge0's HTTP API shape (tokens, base64 fields, queue -> processing
-> finished) but NEVER executes code: every result comes from a `behaviour`
function supplied by the test, which decides the canned outcome for a given
(program, stdin, language_id). Real compilation/execution is verified
separately against a real Judge0 (see README "Code execution").
"""

import base64
import itertools
import json
from collections.abc import Callable
from dataclasses import dataclass, field

import httpx


@dataclass
class Outcome:
    status_id: int = 3  # 3 = ran fine (CodeArena compares output itself)
    stdout: str = ""
    stderr: str = ""
    compile_output: str = ""
    time: float | None = 0.01
    memory: int | None = 3000


def b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def unb64(text: str | None) -> str:
    return base64.b64decode(text).decode() if text else ""


@dataclass
class FakeJudge0:
    behaviour: Callable[[str, str, int], Outcome]
    # Polls answered with "Processing" before the result is returned.
    polls_before_done: int = 1
    down: bool = False  # connection refused
    http_status: int | None = None  # e.g. 401 / 503 for every request
    never_finishes: bool = False
    submissions: list[dict] = field(default_factory=list)
    _results: dict[str, tuple[Outcome, int]] = field(default_factory=dict)
    _tokens: itertools.count = field(default_factory=lambda: itertools.count(1))

    def handler(self, request: httpx.Request) -> httpx.Response:
        if self.down:
            raise httpx.ConnectError("connection refused", request=request)
        if self.http_status:
            return httpx.Response(self.http_status, json={"error": "nope"})
        path = request.url.path
        if request.method == "GET" and path == "/about":
            return httpx.Response(200, json={"version": "fake"})
        if request.method == "POST" and path == "/submissions":
            body = json.loads(request.content)
            source, stdin = unb64(body["source_code"]), unb64(body["stdin"])
            self.submissions.append({**body, "source_code": source, "stdin": stdin, "headers": dict(request.headers)})
            token = f"tok-{next(self._tokens)}"
            self._results[token] = (self.behaviour(source, stdin, body["language_id"]), 0)
            return httpx.Response(201, json={"token": token})
        if request.method == "GET" and path.startswith("/submissions/"):
            token = path.rsplit("/", 1)[1]
            outcome, polls = self._results[token]
            self._results[token] = (outcome, polls + 1)
            if self.never_finishes or polls < self.polls_before_done:
                return httpx.Response(200, json={"token": token, "status": {"id": 2, "description": "Processing"}})
            return httpx.Response(
                200,
                json={
                    "token": token,
                    "status": {"id": outcome.status_id, "description": "done"},
                    "stdout": b64(outcome.stdout) if outcome.stdout else None,
                    "stderr": b64(outcome.stderr) if outcome.stderr else None,
                    "compile_output": b64(outcome.compile_output) if outcome.compile_output else None,
                    "message": None,
                    "time": None if outcome.time is None else str(outcome.time),
                    "memory": outcome.memory,
                },
            )
        return httpx.Response(404, json={"error": "not found"})

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handler)
