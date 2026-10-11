"""Minimal Judge0 CE client plus the single Judge0 status mapping.

Judge0 only executes code. Expected outputs are never sent to it; CodeArena
compares outputs itself (see comparator.py). All values are base64-encoded so
any input/output (unicode, control characters) survives the round trip.
"""

import base64
import logging
import time
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.models.submission import SubmissionStatus

logger = logging.getLogger("codearena.judge0")

RESULT_FIELDS = "token,status,stdout,stderr,compile_output,message,time,memory,exit_code,exit_signal"

# Judge0 status id -> CodeArena meaning. None = finished normally; CodeArena
# then compares the output. The only place Judge0 status ids appear.
IN_QUEUE, PROCESSING = 1, 2
JUDGE0_STATUS: dict[int, SubmissionStatus | None] = {
    3: None,  # Accepted = ran successfully (no expected output was sent)
    4: None,  # Wrong Answer: only if expected output were sent; compare ourselves
    5: SubmissionStatus.TIME_LIMIT_EXCEEDED,
    6: SubmissionStatus.COMPILE_ERROR,
    7: SubmissionStatus.RUNTIME_ERROR,  # SIGSEGV
    8: SubmissionStatus.OUTPUT_LIMIT_EXCEEDED,  # SIGXFSZ: output file size limit
    9: SubmissionStatus.RUNTIME_ERROR,  # SIGFPE
    10: SubmissionStatus.RUNTIME_ERROR,  # SIGABRT
    11: SubmissionStatus.RUNTIME_ERROR,  # NZEC (non-zero exit code)
    12: SubmissionStatus.RUNTIME_ERROR,  # other runtime error (e.g. killed)
    13: SubmissionStatus.SYSTEM_ERROR,  # Judge0 internal error
    14: SubmissionStatus.SYSTEM_ERROR,  # exec format error
}

_MEMORY_HINTS = ("MemoryError", "OutOfMemoryError", "std::bad_alloc", "Cannot allocate memory", "out of memory")


class JudgeUnavailable(Exception):
    """Judge0 could not be reached, rejected the request or failed internally."""


class JudgeTimeout(Exception):
    """Judge0 did not finish before the configured deadline."""


@dataclass(frozen=True)
class ExecutionLimits:
    cpu_time_s: float
    wall_time_s: float
    memory_kb: int
    max_output_kb: int = 1024


@dataclass
class JudgeResult:
    status_id: int
    stdout: str
    stderr: str
    compile_output: str
    message: str
    time_ms: int | None
    memory_kb: int | None

    def verdict(self, memory_limit_kb: int) -> SubmissionStatus | None:
        """Mapped status; None means "ran fine, compare the output"."""
        if self.status_id not in JUDGE0_STATUS:
            return SubmissionStatus.SYSTEM_ERROR
        verdict = JUDGE0_STATUS[self.status_id]
        if verdict == SubmissionStatus.RUNTIME_ERROR and self._looks_like_memory_limit(memory_limit_kb):
            return SubmissionStatus.MEMORY_LIMIT_EXCEEDED
        return verdict

    def _looks_like_memory_limit(self, memory_limit_kb: int) -> bool:
        # Judge0 has no dedicated memory-limit status: a program over the limit
        # is killed or fails to allocate. Use the reported peak and error text.
        near_limit = self.memory_kb is not None and self.memory_kb >= memory_limit_kb * 0.95
        return near_limit or any(hint in self.stderr for hint in _MEMORY_HINTS)


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _unb64(value: str | None, limit: int) -> str:
    if not value:
        return ""
    raw = base64.b64decode(value)[:limit]
    return raw.decode("utf-8", errors="replace")


class Judge0Client:
    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        api_key_header: str = "X-Auth-Token",
        rapidapi_host: str | None = None,
        request_timeout: float = 10.0,
        poll_interval: float = 0.75,
        max_output_bytes: int = 1_100_000,
        transport: httpx.BaseTransport | None = None,
    ):
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers[api_key_header] = api_key
        if rapidapi_host:
            headers["X-RapidAPI-Host"] = rapidapi_host
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"), headers=headers, timeout=request_timeout, transport=transport
        )
        self._poll_interval = poll_interval
        self._max_output_bytes = max_output_bytes

    def close(self) -> None:
        self._http.close()

    # ------------------------------------------------------------------ http
    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        try:
            response = self._http.request(method, url, **kwargs)
        except httpx.HTTPError as exc:
            logger.warning("judge0_unreachable method=%s path=%s error=%s", method, url.split("?")[0], type(exc).__name__)
            raise JudgeUnavailable("Judge0 is unreachable") from exc
        if response.status_code >= 400:
            # 401/403: bad token, 422: rejected limits, 503: queue full, 5xx: down.
            logger.warning("judge0_error method=%s path=%s status=%s", method, url.split("?")[0], response.status_code)
            raise JudgeUnavailable(f"Judge0 returned HTTP {response.status_code}")
        return response

    def is_available(self) -> bool:
        try:
            self._request("GET", "/about")
            return True
        except JudgeUnavailable:
            return False

    def create(self, *, source_code: str, language_id: int, stdin: str, limits: ExecutionLimits) -> str:
        body = {
            "source_code": _b64(source_code),
            "language_id": language_id,
            "stdin": _b64(stdin),
            "cpu_time_limit": limits.cpu_time_s,
            "wall_time_limit": limits.wall_time_s,
            "memory_limit": limits.memory_kb,
            "max_file_size": limits.max_output_kb,
            "number_of_runs": 1,
            "enable_network": False,
        }
        response = self._request("POST", "/submissions?base64_encoded=true&wait=false", json=body)
        token = response.json().get("token")
        if not token:
            raise JudgeUnavailable("Judge0 did not return a token")
        return token

    def fetch(self, token: str) -> JudgeResult | None:
        """The finished result, or None while queued / processing."""
        response = self._request("GET", f"/submissions/{token}?base64_encoded=true&fields={RESULT_FIELDS}")
        data = response.json()
        status_id = int((data.get("status") or {}).get("id", 0))
        if status_id in (IN_QUEUE, PROCESSING):
            return None
        time_s = data.get("time")
        return JudgeResult(
            status_id=status_id,
            stdout=_unb64(data.get("stdout"), self._max_output_bytes),
            stderr=_unb64(data.get("stderr"), self._max_output_bytes),
            compile_output=_unb64(data.get("compile_output"), self._max_output_bytes),
            message=_unb64(data.get("message"), 2000),
            time_ms=round(float(time_s) * 1000) if time_s not in (None, "") else None,
            memory_kb=int(data["memory"]) if data.get("memory") is not None else None,
        )

    def execute(
        self, *, source_code: str, language_id: int, stdin: str, limits: ExecutionLimits, deadline: float
    ) -> JudgeResult:
        """Submit one program run and poll until it finishes or `deadline` passes."""
        token = self.create(source_code=source_code, language_id=language_id, stdin=stdin, limits=limits)
        while True:
            time.sleep(self._poll_interval)
            result = self.fetch(token)
            if result is not None:
                return result
            if time.monotonic() >= deadline:
                raise JudgeTimeout(f"Judge0 did not finish token={token[:8]}")


def client_from_settings() -> Judge0Client | None:
    """The configured client, or None when code execution is not set up."""
    if not settings.JUDGE0_BASE_URL:
        return None
    return Judge0Client(
        settings.JUDGE0_BASE_URL,
        api_key=settings.JUDGE0_API_KEY,
        api_key_header=settings.JUDGE0_API_KEY_HEADER,
        rapidapi_host=settings.JUDGE0_RAPIDAPI_HOST,
        request_timeout=settings.JUDGE0_REQUEST_TIMEOUT,
        poll_interval=settings.JUDGE0_POLL_INTERVAL,
    )
