# CodeArena Architecture (Phases 1–5)

## Overview

```
┌────────────────────────┐   HTTPS / JSON    ┌─────────────────────────┐   SQL    ┌────────────┐
│  React + Vite (5173)   │ ───────────────▶  │  FastAPI (8000)         │ ───────▶ │ PostgreSQL │
│  AuthContext, Router   │  Bearer <JWT>     │  routes → services → DB │          │  users     │
└────────────────────────┘ ◀───────────────  └─────────────────────────┘          └────────────┘
         { success, message, data }
```

## Backend layers

| Layer | Folder | Responsibility |
|---|---|---|
| Routes | `app/api/routes/` | HTTP only: parse input, call a service, wrap the result with `ok()` |
| Dependencies | `app/api/dependencies.py` | `get_current_user`, `require_student/staff/admin/staff_or_admin` |
| Services | `app/services/` | Business rules (registration, login, last-admin protection) |
| Models | `app/models/` | SQLAlchemy tables |
| Schemas | `app/schemas/` | Pydantic request/response models + validation |
| Core | `app/core/` | Settings, password hashing, JWT, error handlers |
| DB | `app/db/` | Engine, session, declarative base |
| Utils | `app/utils/` | Seed scripts, rate limiter |

Adding a feature in a later phase (for example problems) means adding a model,
a schema file, a service, and a router, then registering the router in
`app/api/router.py`. Authentication does not change.

## Problem database (Phase 3)

```
users ──< submissions >── problems >── topics (self-referencing parent_topic_id for future subtopics)
                            │
                            ├──< problem_tags >── tags
                            ├──< problem_examples      (public worked examples)
                            ├──< starter_codes         (one per language, never executed)
                            └──< test_cases            (is_hidden; admin + future judge only)
```

* **Lifecycle.** `problems.status` is `DRAFT → PUBLISHED → ARCHIVED`; `is_published` is derived. Students see `PUBLISHED` only. Deleting through the API archives (soft delete) because submissions will reference problems.
* **Foreign keys.** Problem children use `ON DELETE CASCADE`. `problems.topic_id` is `RESTRICT` (a topic with problems cannot be deleted). `problems.created_by` is `SET NULL`, so deleting a problem never touches users and deleting a user never deletes problems.
* **Hidden test cases.** The student schemas in `schemas/problem.py` have no field for hidden data, and `problem_service.get_published_detail` selects only `is_hidden = false` cases. Hidden cases are reachable only through `/api/admin/...`.
* **Search and filters** run in SQL (`ILIKE` on title, slug and tag names with escaped wildcards; filters as query parameters; `LIMIT/OFFSET` pagination). Indexes: `problems.slug` (unique), `topic_id`, `difficulty`, `status`; `tags.slug`; `topics.slug`, `order_index`.
* **Progress.** Solved = an `ACCEPTED` submission. The `submissions` table exists so this has one source of truth, but nothing writes to it until the judge phase.
* **Seed.** `python -m app.utils.seed_learning` (data in `app/seed_data/`) is idempotent and runs every problem through the same validation and service as the admin API.

## Coding workspace (Phase 4)

* `/student/problems/:slug/solve` is a full-screen workspace: problem panel, Monaco editor (bundled locally, loaded only on this route), test/result panel and toolbar; resizable split on desktop, stacked on mobile.
* **Drafts** (`code_drafts`, unique per user/problem/language) are autosaved after 1 s of inactivity. Load order: saved draft > unsynced local backup > starter code; autosave starts only after that, so starter code can never overwrite a draft. Every save carries the draft `version`; a stale tab gets 409 and the student chooses which version to keep.
* Local storage only holds a temporary backup of unsaved code (keyed by user), editor preferences and custom test cases. PostgreSQL is the source of truth.

## Code execution (Phase 5)

```
CodingWorkspace ─▶ executionService ─▶ POST /api/executions/run | /api/submissions
                                              │
                    execution_service (validate, rate limit, one job per student)
                                              │  harness.build_program (hidden driver)
                    judging/runner ── judge0 client ──HTTP──▶ Judge0 ──▶ isolate sandbox
                                              │  comparator.outputs_match (server decides)
                    submissions table (results JSON without hidden data)
```

* Student code is only ever executed by Judge0. The backend never runs it.
* `app/core/languages.py` is the single CodeArena→Judge0 language mapping; `app/services/judging/judge0.py` holds the single Judge0 status mapping.
* Polling is bounded by `JUDGE0_TIMEOUT`; concurrency by `JUDGE0_MAX_CONCURRENT_JOBS`. Submissions are written before judging and always resolve: unreachable Judge0 → `SYSTEM_ERROR`, too slow → `EXECUTION_TIMEOUT`, and rows left `RUNNING` by a restart are expired at startup and on the next request.
* Hidden tests: inputs are sent to Judge0 (necessary), expected outputs never are. Responses for hidden tests carry only verdict/time/memory; stderr from hidden tests is replaced by a generic message.
* Statistics: problems solved, accuracy, streak and the activity heatmap come from judged submissions; infrastructure failures are excluded.

## Authentication flow

1. **Register** (`POST /api/auth/register`). The body has no role field, and the server always creates a `STUDENT`. The password is hashed with bcrypt.
2. **Login** (`POST /api/auth/login`) takes `email`, `password` and an optional `portal`.
   * The credentials are checked. Unknown emails still run a bcrypt check, so response timing does not reveal which emails exist.
   * Inactive accounts are refused with a 403.
   * If `portal` is given, it must match the role stored in the database. A student cannot use the Staff tab or the admin portal.
   * The server returns a signed HS256 JWT with `sub` set to the user id and a configurable expiry.
3. The **frontend** stores the token in `localStorage` and sends `Authorization: Bearer <token>`.
4. **Every protected request** decodes the token and then loads the user from the database. Role and active status always come from that record, never from the token or the request. A deactivated user is locked out immediately.
5. **Role guards** return 403 for the wrong role. Each router declares its guard once, for example `dependencies=[Depends(require_admin)]`.
6. **Logout** (`POST /api/auth/logout`). Tokens are stateless, so the client discards its token. A token blocklist or refresh tokens can be added later without changing routes.

## Frontend structure

| Folder | Contents |
|---|---|
| `context/` | `AuthProvider`: restores the session on refresh, logs out on expiry, syncs tabs |
| `routes/` | `ProtectedRoute` (role check, shows a 403 page), `GuestRoute` (redirects logged-in users), `AppRoutes` |
| `services/` | Axios instance with token and 401 interceptors, plus one service file per API area |
| `layouts/` | `AuthLayout` (login/register), `DashboardLayout` (sidebar, mobile drawer, user menu) |
| `pages/` | One folder per role, plus `auth/`, `shared/` and `errors/` |
| `components/ui/` | Reusable building blocks such as Button, TextField, Alert, Card, StatCard, Modal |
| `config/navigation.ts` | Sidebar items per role. Future features are listed with a "soon" badge |

### Session handling

* **Page refresh.** `AuthProvider` calls `/auth/me` with the stored token before any protected page renders. The user sees "Loading dashboard..." meanwhile.
* **Expired or invalid token.** The Axios interceptor catches a 401 on an authenticated call, clears the token and fires an event. `AuthProvider` stores a flash message and clears the user. `ProtectedRoute` then redirects to the login page, which shows "Your session has expired. Please login again."
* **Proactive expiry.** A timer logs the user out at the JWT's `exp` time, even if they make no API call.

## Security checklist (Phase 1)

* Passwords are hashed with bcrypt and never returned by the API.
* There is no public route that creates STAFF or ADMIN accounts. Staff are created by an admin through `POST /api/admin/staff` or by the seed script.
* The role is always read from the database, never from the frontend or the token.
* Admins cannot deactivate themselves or the last active admin.
* All secrets come from `.env` files, which are git-ignored.
* Errors use the generic envelope. Stack traces are logged server-side only.
* An in-memory rate limiter protects login and registration. Swap in Redis to run multiple workers.
* CORS origins are configured through `CORS_ORIGINS`.
