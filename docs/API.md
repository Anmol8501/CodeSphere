# CodeArena API Reference (Phases 1–5)

Base URL: `http://localhost:8000/api`. Interactive docs: <http://localhost:8000/docs>.

All responses use the same envelope:

```json
{ "success": true,  "message": "Login successful", "data": { } }
{ "success": false, "message": "Invalid email or password.",
  "error": { "code": "UNAUTHORIZED", "message": "Invalid email or password." } }
```

`error.code` is a stable machine-readable code (e.g. `NOT_FOUND`, `VALIDATION_ERROR`, `RATE_LIMITED`, `INVALID_LANGUAGE`, `LANGUAGE_NOT_AVAILABLE`, `SOURCE_TOO_LARGE`, `EXECUTION_UNAVAILABLE`, `SUBMISSION_IN_PROGRESS`).

Validation errors (422) also include `errors: [{ "field": "email", "message": "..." }]`.

Authenticated endpoints need the header `Authorization: Bearer <access_token>`.

## Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | Public | Register a **student** (`full_name`, `email`, `password`, `confirm_password`). 201 on success, 409 if the email exists. Any other field, such as `role`, is rejected with a 422. |
| POST | `/auth/login` | Public | `email`, `password`, optional `portal` (`STUDENT`, `STAFF` or `ADMIN`). Returns `access_token`, `token_type`, `expires_in` and `user`. |
| GET | `/auth/me` | Any role | The current user. |
| POST | `/auth/logout` | Any role | Confirms logout. The client discards its token. |

## Dashboards

Statistics are real values. They are zero until the systems that produce them exist (problems, submissions, contests, classrooms).

| Method | Path | Auth | Returns |
|---|---|---|---|
| GET | `/student/dashboard` | STUDENT | `user`, `statistics` (`problems_solved`, `current_streak`, `accuracy`, `contest_rating`), `learning_progress`, `coding_activity` |
| GET | `/staff/dashboard` | STAFF | `user`, `statistics` (`students`, `classrooms`, `assignments`, `contests`) |
| GET | `/admin/dashboard` | ADMIN | User counts calculated from the database, plus `system_status` for the API, database, authentication, judge engine and AI service |

## Admin

| Method | Path | Description |
|---|---|---|
| GET | `/admin/stats` | Student, staff and admin counts, active users, published problems. |
| GET | `/admin/users?role=&is_active=&search=&page=&page_size=` | Paginated user list. `role` filters by role, `is_active` by status. `search` matches name or email. |
| PATCH | `/admin/users/{id}/status` | Body `{ "is_active": false }`. You cannot deactivate yourself or the last active admin (400). |
| POST | `/admin/staff` | Create a staff account (`full_name`, `email`, `password`). |

## Problems, topics and learning path (Phase 3)

Any signed-in, active user (student, staff or admin). These endpoints only ever return **published** problems. An unpublished or archived problem returns the same `404 Problem not found.` as a slug that never existed.

| Method | Path | Description |
|---|---|---|
| GET | `/problems` | Paginated list. Query: `search` (title, slug or tag, case-insensitive), `difficulty` (`EASY`/`MEDIUM`/`HARD`), `topic` (slug), `tags` (comma-separated slugs, all must match), `status` (`solved`/`attempted`/`unsolved`, your own progress), `page`, `page_size` (max 50). Each item has `user_status`. |
| GET | `/problems/{slug}` | Public problem data: description (Markdown-style text), constraints, input/output format, `examples`, `starter_codes`, and `sample_test_cases` (only cases marked visible). Hidden test cases are never selected. |
| GET | `/topics` | Active top-level topics ordered by `order_index`, each with `problem_count` (published). |
| GET | `/topics/{slug}` | Topic with `difficulty_counts`, `solved_count`, `progress`, `status`. 404 `Topic not found.` |
| GET | `/tags` | All tags. |
| GET | `/learning-path` | `{ topics: [...], total_problems, total_solved, progress }`. |

Paginated responses use `{ "items": [], "page": 1, "page_size": 20, "total": 20, "total_pages": 1 }`.

**Solved status.** A problem is `SOLVED` only when the user has an `ACCEPTED` row in `submissions`, `ATTEMPTED` when they have any other submission, otherwise `UNSOLVED`. Opening a problem never changes it. Submissions are created by the judge in a later phase, so every value is honestly 0/UNSOLVED today.

## Admin problem management (Phase 3)

ADMIN only; STAFF and STUDENT get 403.

| Method | Path | Description |
|---|---|---|
| GET | `/admin/problems` | All problems in every state. Same filters as `/problems` plus `status` (`DRAFT`/`PUBLISHED`/`ARCHIVED`) and `published` (true/false). |
| GET | `/admin/problems/{id}` | Full problem including all test cases. |
| POST | `/admin/problems` | Create. Body: `title`, optional `slug` (generated from the title), `description`, `difficulty`, `topic_id`, `tag_ids`, `constraints`, `input_format`, `output_format`, `examples[]`, `starter_codes[]` (`CPP`/`JAVA`/`PYTHON`, one each), `test_cases[]`, `is_published`. Unknown fields (e.g. `status`, `created_by`) → 422. Duplicate slug → 409. |
| PUT | `/admin/problems/{id}` | Replace content (same body without `test_cases`; optional `is_published`). |
| PATCH | `/admin/problems/{id}/publish` | `{ "is_published": true }` publishes; `false` moves it to DRAFT (also restores an archived problem). |
| DELETE | `/admin/problems/{id}` | Archive (soft delete). Hidden from students, kept for submission history. |
| GET / POST | `/admin/problems/{id}/test-cases` | List / add (`input_data`, `expected_output`, `is_hidden` default true, optional `order_index`). |
| PUT / DELETE | `/admin/test-cases/{id}` | Update / delete a test case. |
| POST | `/admin/tags` | Create a tag (`name`); 409 if it exists. |

Test cases are stored for the judge (Phase 5). Nothing is executed in Phase 3.

## Coding workspace and judging (Phases 4–5)

STUDENT only (staff/admin get 403). The user always comes from the JWT; any `user_id`-style field is rejected (422), and so are client-sent verdict fields (`status`, `passed`, `score`, `runtime_ms`, `time_limit_ms`, ...).

| Method | Path | Description |
|---|---|---|
| GET | `/problems/{id}/draft?language=CPP` | Your draft for that problem/language, or `data: null`. |
| PUT | `/problems/{id}/draft` | `{language, source_code, base_version, force?}`. Upsert; 409 if another tab saved a newer version. Max 200,000 characters. |
| POST | `/executions/run` | `{problem_id, language, source_code, custom_cases?: [{input, expected_output?}]}` (max 5 custom). Runs the public tests + custom cases through Judge0. Returns `{verdict, passed_tests, total_tests, runtime_ms, memory_kb, compile_output, message, results[]}`. Not stored. |
| POST | `/submissions` | `{problem_id, language, source_code}`. Judges public + hidden tests (stops at the first failure) and stores the submission. Returns the submission detail. |
| GET | `/submissions?problem=&language=&status=&page=&page_size=` | Your submissions, newest first. |
| GET | `/submissions/{id}` | One of your submissions (someone else's id returns 404). Includes your source code and per-test results. |
| GET | `/health/execution` | `{"available": bool}` (public, no infrastructure details). |

`language` accepts `CPP`, `JAVA`, `PYTHON` (case-insensitive); anything else is `400 INVALID_LANGUAGE`, a language the problem does not offer is `400 LANGUAGE_NOT_AVAILABLE`, source over `EXECUTION_MAX_SOURCE_BYTES` is `413 SOURCE_TOO_LARGE`. Runs are limited to 10 and submissions to 5 per minute per student (`429`). A second submission while one is being judged returns `409 SUBMISSION_IN_PROGRESS`. With no Judge0 configured both return `503 EXECUTION_UNAVAILABLE` and nothing is stored.

**Verdicts:** `ACCEPTED`, `WRONG_ANSWER`, `COMPILE_ERROR`, `RUNTIME_ERROR`, `TIME_LIMIT_EXCEEDED`, `MEMORY_LIMIT_EXCEEDED`, `OUTPUT_LIMIT_EXCEEDED`, and the infrastructure statuses `SYSTEM_ERROR` (judge unavailable) and `EXECUTION_TIMEOUT` (judge too slow), which never count as attempts. Each result entry has `kind` (`public` / `hidden` / `custom`); for hidden tests `input`, `expected_output`, `actual_output` and `stderr` are always `null`.

## Status codes

| Code | Meaning |
|---|---|
| 200 / 201 | Success |
| 400 | Business rule violated (e.g. last admin, unknown topic/tag) |
| 401 | Missing, invalid or expired token, or wrong credentials |
| 403 | Authenticated but wrong role, account deactivated, or portal mismatch |
| 404 | Resource not found |
| 409 | Email already registered, duplicate problem slug or tag, stale draft, submission in progress |
| 413 | Source code too large |
| 422 | Validation error (including invalid filters such as `difficulty=X`) |
| 429 | Too many login/register attempts, runs or submissions |
| 503 | Code execution not configured |
| 500 | Unexpected server error (generic message only) |

## Example (curl)

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Asha Kumar","email":"asha@college.edu","password":"Password123","confirm_password":"Password123"}'

TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"asha@college.edu","password":"Password123","portal":"STUDENT"}' | python -c "import sys,json;print(json.load(sys.stdin)['data']['access_token'])")

curl http://localhost:8000/api/auth/me -H "Authorization: Bearer $TOKEN"
```
