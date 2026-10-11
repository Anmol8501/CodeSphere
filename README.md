# CodeArena

**Learn • Code • Compete.** CodeArena is a full-stack coding learning and assessment platform for college students. Students practice problems, follow learning paths and compete in contests. Staff run classrooms and assignments. Admins manage the platform.

> **Current status: Phase 6 (Submissions, Progress & Analytics). Real code execution still needs a running Judge0.**
> Phases 1 to 4 deliver authentication and roles, dashboards, the problem library and DSA learning path, and a Monaco coding workspace with autosaved drafts. Phase 5 adds RUN / SUBMIT judged by a sandboxed Judge0, with hidden tests and verdicts. Phase 6 adds per-test results, submission history and details, solved state and attempts, progress by difficulty and topic, streaks, a heatmap, a leaderboard and staff analytics, all computed from real submissions (definitions: [docs/ANALYTICS.md](docs/ANALYTICS.md)). Execution is tested against a Judge0 test double; real execution needs a running Judge0 (see section 7).

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4, React Router 7, Axios, Lucide icons |
| Theme | Dark terminal palette: background `#050805`, cards `#0B100B`, subtle green borders, primary `#39FF14` (tokens in `frontend/src/index.css`) |
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, PyJWT, bcrypt |
| Database | PostgreSQL (tested with 16–18), using the pure-Python `pg8000` driver |
| Tooling | pytest, oxlint, Git |

## Architecture

```
React (5173)  ──Bearer JWT──▶  FastAPI (8000)  ──SQLAlchemy──▶  PostgreSQL
 AuthContext                    routes → services → models
 ProtectedRoute                 role dependencies (require_admin, ...)
 Monaco editor                       │
                                     └──HTTP (server-side only)──▶  Judge0 (sandboxed code execution)
```

* The **backend is the authority**. Every protected endpoint loads the user from the database and checks their role. Frontend route guards only improve the experience.
* **Public registration always creates a STUDENT.** Staff are created by an admin or by a seed script. Admins are created only by the seed script.
* Admins have a **separate login** at `/admin/login`, which is not linked from public pages.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details and [docs/API.md](docs/API.md) for the API reference.

## Folder structure

```
CodeVita/                     (project root)
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/       auth, admin, admin_problems, problems, learning, student, staff, health
│   │   │   ├── dependencies.py   get_current_user, require_* role guards
│   │   │   └── router.py     mounts everything under /api
│   │   ├── core/             config.py, security.py (bcrypt + JWT), exceptions.py
│   │   ├── db/               base.py, session.py
│   │   ├── models/           user, topic, tag (+ problem_tags), problem (+ examples, starter code, test cases), submission
│   │   ├── schemas/          auth, user, dashboard, common (Page), problem, learning, admin_problem, validators
│   │   ├── services/         auth, user, dashboard, problem, admin_problem, topic, tag, learning, submission
│   │   ├── seed_data/        topics.py, tags.py, problems.py, starter_code.py (curated seed content)
│   │   ├── utils/            seed_admin.py, seed_staff.py, seed_learning.py, seed.py, slug.py, rate_limiter.py
│   │   └── main.py
│   ├── alembic/              migrations: 0001 users, 0002 problem database
│   ├── tests/                pytest suite
│   ├── requirements.txt / requirements-dev.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/       ui/, brand/, auth/, layout/, dashboard/, problems/, admin/ (incl. admin/problems form)
│   │   ├── config/           navigation.ts (sidebar per role), features.ts (coming-soon pages)
│   │   ├── context/          AuthContext.tsx
│   │   ├── hooks/            useAuth, useApiQuery, useDebouncedValue, useFlashMessage
│   │   ├── layouts/          AuthLayout, DashboardLayout
│   │   ├── pages/            auth/, student/, staff/, admin/, shared/, errors/, HomePage
│   │   ├── routes/           AppRoutes, ProtectedRoute, GuestRoute
│   │   ├── services/         api.ts, authService, adminService, dashboardService,
│   │   │                     problemService, topicService, learningService, adminProblemService
│   │   ├── types/  utils/  assets/
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── .env.example
├── docs/                     ARCHITECTURE.md, API.md
├── docker-compose.yml        optional PostgreSQL container
└── README.md
```

## Requirements

* **Python** 3.12 or newer (developed on 3.13)
* **Node.js** 20.19+ or 22.12+ (developed on 22.18) with npm
* **PostgreSQL** 14+ installed locally, **or** Docker for `docker-compose.yml`

---

## 1. PostgreSQL setup

### Option A: local PostgreSQL (Windows installer, Homebrew, apt and so on)

Open `psql` (on Windows: *SQL Shell (psql)* from the Start menu) as the `postgres` superuser and run:

```sql
CREATE USER codearena WITH PASSWORD 'choose-a-strong-password';
CREATE DATABASE codearena OWNER codearena;
```

Your connection URL is then:

```
postgresql+pg8000://codearena:choose-a-strong-password@localhost:5432/codearena
```

> If your password contains special characters such as `@ : / % #`, URL-encode them, for example `@` becomes `%40`.

### Option B: Docker

```bash
cp .env.example .env              # set POSTGRES_PASSWORD
docker compose up -d
```

Use `postgresql+pg8000://codearena:<POSTGRES_PASSWORD>@localhost:5432/codearena`.

## 2. Backend setup

```bash
cd backend
python -m venv .venv

# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Windows (Git Bash):    source .venv/Scripts/activate
# macOS / Linux:         source .venv/bin/activate

pip install -r requirements-dev.txt
cp .env.example .env              # then edit .env (see below)
```

### Backend environment variables (`backend/.env`)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL URL (see above) |
| `JWT_SECRET` | 32+ character random string. Generate it with `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `JWT_ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime, default `60` |
| `CORS_ORIGINS` | Comma-separated frontend origins, default `http://localhost:5173,http://127.0.0.1:5173` |
| `RATE_LIMIT_ENABLED`, `LOGIN_RATE_LIMIT_PER_MINUTE`, `REGISTER_RATE_LIMIT_PER_MINUTE` | Basic per-IP rate limiting |
| `ADMIN_NAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Development admin created by the seed script |
| `STAFF_NAME`, `STAFF_EMAIL`, `STAFF_PASSWORD` | Development staff account created by the seed script |
| `JUDGE0_BASE_URL`, `JUDGE0_API_KEY` | Judge0 URL and its `AUTHN_TOKEN` (empty = code execution unavailable). Server-side only |
| `JUDGE0_API_KEY_HEADER`, `JUDGE0_RAPIDAPI_HOST` | Only for the hosted RapidAPI Judge0 (`X-RapidAPI-Key`) |
| `JUDGE0_TIMEOUT`, `JUDGE0_POLL_INTERVAL`, `JUDGE0_REQUEST_TIMEOUT`, `JUDGE0_MAX_CONCURRENT_JOBS` | Polling and concurrency (defaults 30 s, 0.75 s, 10 s, 4) |
| `EXECUTION_MAX_SOURCE_BYTES`, `EXECUTION_MAX_OUTPUT_BYTES`, `EXECUTION_STOP_ON_FIRST_FAILURE` | Source size limit (200 KB), output kept per test, early stop on submit |
| `RUN_RATE_LIMIT_PER_MINUTE`, `SUBMIT_RATE_LIMIT_PER_MINUTE` | Per-student limits (10 runs, 5 submissions per minute) |
| `APP_TIMEZONE` | IANA timezone for calendar days: streaks, the heatmap, "today" (default `Asia/Kolkata`). Never the browser's or server's own zone |
| `BCRYPT_ROUNDS` | bcrypt work factor for new password hashes (default 12; the test suite uses 4) |

Seed passwords must be at least 8 characters and contain a letter and a number. Seed emails must use a normal domain, because reserved domains such as `.local` and `.test` are rejected.

## 3. Database migrations (Alembic)

Run these from `backend/` with the virtualenv active.

```bash
alembic upgrade head                          # create/update tables
alembic current                               # show the current revision
alembic revision --autogenerate -m "add xyz"  # create a migration after changing models
alembic downgrade -1                          # undo the last migration
```

When you add a new model in a later phase, import it in `app/models/__init__.py` so autogenerate can see it.

Phase 6 migrations: `0005` adds per-test results, per-problem progress and the first-accepted flag, and **backfills them from existing submissions** (no submission is removed; downgrade restores the old per-test JSON). `0006` adds server-side logout (revoked token ids). To recompute or audit progress at any time:

```bash
python -m app.utils.rebuild_progress           # rebuild from submissions (idempotent), then audit
python -m app.utils.rebuild_progress --check   # audit only; exit code 1 on differences
```

**Reset the development database.** This deletes all data.

```bash
alembic downgrade base && alembic upgrade head
# or drop and recreate in psql:
#   DROP DATABASE codearena; CREATE DATABASE codearena OWNER codearena;
```

## 4. Seed the development accounts

```bash
python -m app.utils.seed_admin    # creates ADMIN from ADMIN_EMAIL / ADMIN_PASSWORD
python -m app.utils.seed_staff    # creates STAFF from STAFF_EMAIL / STAFF_PASSWORD
```

The scripts are safe to run repeatedly. They skip accounts that already exist, refuse to change an existing user's role, hash passwords, and never print them.

**Changed a password in `.env`?** Re-running the seed does not touch an existing account. Sync it with:

```bash
python -m app.utils.seed_admin --reset-password
python -m app.utils.seed_staff --reset-password
```

This re-hashes the password from `.env` and re-activates the account. If a seeded login fails with "Invalid email or password.", this is almost always the fix.

### Seed the learning path (topics, tags, starter problems)

```bash
python -m app.utils.seed_learning
```

Creates the 17 ordered DSA topics, 21 tags and 21 original starter problems (each with examples, C++/Java/Python starter code and hidden execution harnesses, one visible sample test case and hidden test cases), all published. It is idempotent: every row is looked up by slug first, so running it again creates nothing and never overwrites problems an admin has edited.

Databases seeded before Phase 5 get the harnesses with `python -m app.utils.seed_execution` (only where the starter code is unchanged).

## 5. Run the backend

```bash
uvicorn app.main:app --reload --port 8000
```

If auto-reload stops picking up changes on Windows, run without `--reload` and restart manually.

* API: <http://localhost:8000/api>
* Swagger UI: <http://localhost:8000/docs>. Click **Authorize** and paste an `access_token` from `/api/auth/login`.
* Health check: <http://localhost:8000/api/health>

> **Run one backend process.** Rate limits (login, register, run, submit), the duplicate RUN/SUBMIT guard,
> the Judge0 concurrency limit and the execution health cache are kept in memory per process. Do not start
> uvicorn with `--workers N` or several instances behind a load balancer: each process would keep its own
> counters, multiplying the limits. Scaling out means moving that state to a shared store such as Redis first.

## 6. Frontend setup and run

```bash
cd frontend
npm install
cp .env.example .env      # VITE_API_BASE_URL=http://localhost:8000/api
npm run dev               # http://localhost:5173
```

Other scripts include `npm run build` for type-checking and a production build, `npm run lint` for oxlint, and `npm run preview`.

---

## 7. Code execution (Judge0)

Students' code is **never executed by the CodeArena backend**. RUN and SUBMIT
send it to a self-hosted [Judge0 CE](https://github.com/judge0/judge0) 1.13.1,
which compiles and runs it inside its `isolate` sandbox (no network, CPU time,
memory, process and output limits). CodeArena only compares outputs and
decides verdicts.

```
Browser ──▶ CodeArena API ──▶ Judge0 (127.0.0.1:2358) ──▶ isolate sandbox
              │  validates user/problem/language/size, rate limits
              │  adds the problem's hidden harness, sends limits
              └─ compares outputs, decides the verdict, stores the submission
```

* **RUN** executes the public tests plus the student's own custom cases. Not stored.
* **SUBMIT** executes public + hidden tests (stops at the first failure) and is stored.
* Hidden test inputs, expected outputs and the program's output on them are never sent to the browser.
* If Judge0 is down or slow the result is `SYSTEM_ERROR` / `EXECUTION_TIMEOUT`, never a wrong answer.

### Start Judge0 locally (Windows + WSL2 Ubuntu)

Judge0 1.13.1 needs Docker and **cgroup v1** (its `isolate` sandbox enforces time and memory limits through cgroup v1).
WSL2 mounts cgroup v2 before anything in the distribution runs, and a `kernelCommandLine` setting in `.wslconfig`
does not change that, so CodeArena ships a small WSL init wrapper that re-mounts the cgroup v1 layout and then starts
systemd normally. Use Docker Engine inside Ubuntu (Docker Desktop's own VM uses cgroup v2).

1. **Switch the Ubuntu distribution to cgroup v1 (one time).** In PowerShell:
   ```powershell
   wsl -u root -e sh /mnt/d/Projects/CodeVita/infra/judge0/wsl/install-cgroup-v1.sh
   wsl --shutdown
   ```
   The script installs `infra/judge0/wsl/codearena-init` as `/usr/local/sbin/codearena-init` and sets
   `initPath` in `/etc/wsl.conf` (systemd stays enabled; the original file is kept as `/etc/wsl.conf.bak-codearena`).
   If re-mounting ever fails, the wrapper restores cgroup v2 and boots normally. **Undo:** restore
   `/etc/wsl.conf.bak-codearena` to `/etc/wsl.conf`, then `wsl --shutdown`.
2. **Install Docker Engine and start Judge0.** In the Ubuntu terminal:
   ```bash
   stat -fc %T /sys/fs/cgroup        # must print "tmpfs" (cgroup v1), not "cgroup2fs"
   curl -fsSL https://get.docker.com | sudo sh
   sudo usermod -aG docker $USER     # then reopen the terminal
   cd /mnt/d/Projects/CodeVita/infra/judge0
   cp judge0.conf.example judge0.conf
   for k in AUTHN_TOKEN AUTHZ_TOKEN REDIS_PASSWORD POSTGRES_PASSWORD; do
     sed -i "s/^$k=CHANGE_ME$/$k=$(openssl rand -hex 32)/" judge0.conf
   done
   docker compose up -d              # first pull is several GB
   curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:2358/about   # 401: running, token required
   ```
3. **Keep the distribution running.** WSL stops an idle distribution (no open WSL terminal or `wsl.exe` process)
   even while Docker is running, and Judge0 stops with it. Keep an Ubuntu terminal open, or run
   `wsl -e sleep infinity` in a minimized PowerShell window. The containers start again automatically with the
   distribution. Windows reaches Judge0 at `127.0.0.1:2358` through WSL's localhost forwarding.
4. In `backend/.env` set `JUDGE0_BASE_URL=http://127.0.0.1:2358` and `JUDGE0_API_KEY=<AUTHN_TOKEN from judge0.conf>`,
   then restart the backend.

The compose file binds Judge0 to `127.0.0.1` only and `judge0.conf` disables network access, callbacks, `wait=true`,
compiler options, command-line arguments and additional files, and per-process limits (so cgroups always apply).
`judge0.conf` is git-ignored; its tokens never reach the frontend.

### Verify

```bash
curl http://localhost:8000/api/health/execution         # {"available": true}
python -m app.utils.seed_execution                       # adds hidden harnesses to seeded problems (idempotent)
JUDGE0_LIVE=1 pytest tests/test_judge0_live.py -v        # every seeded problem x C++/Java/Python + verdict + sandbox checks
```

### Languages

| Language | Judge0 id | Runtime | Notes |
|---|---|---|---|
| C++ | 54 | GCC 9.2.0 | default `gnu++14` (no C++17 features) |
| Java | 62 | OpenJDK 13.0.1 | entry class must be `Main` for full programs; `Solution` must not be `public` |
| Python | 71 | Python 3.8.1 | use `typing.List`, not `list[int]` annotations |

The mapping lives only in `backend/app/core/languages.py`. Per problem, the time limit is scaled by language (C++ ×1, Java ×2, Python ×3).

### Problem harnesses

"Implement this function" problems store a hidden **harness** per language (`starter_codes.driver_code`): a full program containing `{{USER_CODE}}`, where the student's code is inserted. It reads stdin, calls the student's method and prints the result. Admins edit it under *Starter Code → Hidden execution harness*. Problems without a harness run the student's code as a complete program.

## Frontend routes

| Route | Access |
|---|---|
| `/` | Public landing page |
| `/login` | Student/Staff login. `?role=staff` opens the Staff tab |
| `/register` | Student registration |
| `/admin/login` | Admin portal login (separate, not linked publicly) |
| `/student/problems/:slug/solve` (full-screen coding workspace), `/student/submissions`, `/student/submissions/:id` | STUDENT |
| `/student/dashboard`, `/student/problems`, `/student/problems/:slug`, `/student/learning`, `/student/learning/:slug`, `/student/leaderboard`, `/student/profile`, `/student/contests`, `/student/assignments`, `/student/ai-tutor` | STUDENT |
| `/staff/dashboard`, `/staff/students`, `/staff/students/:id`, `/staff/analytics`, `/staff/problems` (read-only library), `/staff/problems/:slug`, `/staff/classrooms`, `/staff/assignments`, `/staff/contests`, `/staff/profile` | STAFF |
| `/admin/dashboard`, `/admin/users`, `/admin/students`, `/admin/staff`, `/admin/problems`, `/admin/problems/new`, `/admin/problems/:id/edit`, `/admin/problems/:id/test-cases`, `/admin/analytics`, `/admin/analytics/students`, `/admin/analytics/students/:id`, `/admin/system`, `/admin/profile` | ADMIN |
| `/settings` | Any signed-in role |

Pages for features that are not built yet show an honest "Coming soon" empty state. They never show sample data.

* Opening another role's page shows a **403 "You are not authorized to access this page."** screen.
* Opening a protected page while logged out redirects to the login page. After login, you return to the page you asked for if it belongs to your role.

## API endpoints

| Method | Path | Access |
|---|---|---|
| POST | `/api/auth/register` | Public (always creates a STUDENT) |
| POST | `/api/auth/login` | Public |
| GET | `/api/auth/me` | Authenticated |
| POST | `/api/auth/logout` | Authenticated. Revokes the presented token on the server (401 on reuse); other sessions stay signed in |
| GET | `/api/student/dashboard` | STUDENT |
| GET | `/api/staff/dashboard` | STAFF |
| GET | `/api/admin/stats` | ADMIN |
| GET | `/api/admin/users` | ADMIN (filters: `role`, `is_active`, `search`, `page`, `page_size`) |
| PATCH | `/api/admin/users/{id}/status` | ADMIN |
| POST | `/api/admin/staff` | ADMIN |
| GET | `/api/problems` | Any signed-in role. Published only. `search`, `difficulty`, `topic`, `tags`, `status`, `page`, `page_size` |
| GET | `/api/problems/{slug}` | Any signed-in role. Published only, never hidden test cases |
| GET | `/api/topics`, `/api/topics/{slug}` | Any signed-in role |
| GET | `/api/tags` | Any signed-in role |
| GET | `/api/learning-path` | Any signed-in role (progress is per user) |
| GET / POST | `/api/admin/problems` | ADMIN (list all statuses / create) |
| GET / PUT / DELETE | `/api/admin/problems/{id}` | ADMIN (DELETE archives: soft delete) |
| PATCH | `/api/admin/problems/{id}/publish` | ADMIN |
| GET / POST | `/api/admin/problems/{id}/test-cases` | ADMIN |
| PUT / DELETE | `/api/admin/test-cases/{id}` | ADMIN |
| POST | `/api/admin/tags` | ADMIN |
| GET / PUT | `/api/problems/{id}/draft` | STUDENT (own draft only; `?language=`, versioned upsert, 409 on stale tab) |
| POST | `/api/executions/run` | STUDENT. Public tests + custom cases through Judge0. Not stored |
| POST | `/api/submissions` | STUDENT. Public + hidden tests; verdict decided by the server; stored |
| GET | `/api/submissions` | STUDENT, own only. `page`, `limit` (max 100), `status`, `language`, `problem_id` / `problem` (slug), `search`, `period` (`today`, `7d`, `30d`, `all`) |
| GET | `/api/submissions/{id}` | STUDENT, own only (someone else's id is 404). Per-test results, limits, percentiles when enough data |
| GET | `/api/progress/overview`, `/topics`, `/difficulty`, `/languages`, `/activity`, `/streak`, `/heatmap` | STUDENT, own progress only (read-only: no write endpoint exists) |
| GET | `/api/leaderboard` | Any signed-in role. Rank, name, solved, acceptance only |
| GET | `/api/analytics/overview`, `/api/analytics/students`, `/api/analytics/students/{id}` | STAFF, ADMIN (aggregates; never source code) |
| GET | `/api/health` | Public |
| GET | `/api/health/execution` | Public. `{"available": true/false}` only |

## Test accounts

There are **no hard-coded credentials** anywhere in the code.

* **Admin.** The email and password come from `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `backend/.env`, after you run `python -m app.utils.seed_admin`. Log in at `/admin/login`.
* **Staff.** The email and password come from `STAFF_EMAIL` and `STAFF_PASSWORD` in `backend/.env`, after you run `python -m app.utils.seed_staff`. Log in at `/login` using the **Staff** tab. Admins can create more staff from **Admin, then Users, then Add Staff**.
* **Student.** Register at `/register`.

If a seeded login fails, check the exact password in `backend/.env` and run the seed with `--reset-password` (see section 4).

Never use the development values in production.

## Running tests

```bash
cd backend
pytest
```

Lint and type check: `ruff check .` and `mypy app` (dev tools in `requirements-dev.txt`).

The suite uses an isolated in-memory SQLite database and never touches your PostgreSQL data. It covers registration, duplicate emails, validation, login, wrong passwords, portal mismatches, role access for every dashboard, logout, invalid, expired and forged tokens, deactivation, last-admin protection, staff creation, and user filtering and search. Phase 3 adds topics, tags, problem CRUD, publish/unpublish/archive, search, filters, pagination, test cases, hidden-test-case and role security, solved status from submissions, the learning path, and seed idempotency. Phase 4 adds drafts (isolation, upsert, conflicts, limits). Phase 5 adds the judging pipeline against a Judge0 **test double** (`tests/fake_judge0.py`, which never executes code): every verdict, hidden-test protection, Judge0 outages and timeouts, rate limits, duplicate submissions, history and isolation. Phase 6 adds solved state, attempts, first accepted, best runtime/memory, progress by difficulty and topic, streak rules (month and year boundaries, timezone), the heatmap, activity, recommendations, the leaderboard (including ties), staff analytics, history filters and pagination limits, and the incremental-vs-rebuild consistency check. `tests/test_audit.py` checks the complete role matrix over every API endpoint, server-side logout, forged tokens, mass assignment, injection-shaped input, hidden test data across every student endpoint, and that list endpoints run a constant number of queries (no N+1). Foreign keys are enforced in the test database just like PostgreSQL.

Against a real Judge0 (opt-in): `JUDGE0_LIVE=1 pytest tests/test_judge0_live.py -v`.

## Troubleshooting

* **"An Application Control policy has blocked this file"** (Windows Smart App Control). Windows may block some compiled Python extensions. This project uses the pure-Python `pg8000` driver for that reason. If SQLAlchemy's compiled extension is blocked, reinstall it as pure Python:

  ```powershell
  $env:DISABLE_SQLALCHEMY_CEXT = "1"
  pip install --force-reinstall --no-deps --no-binary sqlalchemy SQLAlchemy==2.1.1
  ```
* **`Too many attempts` (429)**. The login rate limit is 10 per minute per IP by default. Wait a minute, or raise `LOGIN_RATE_LIMIT_PER_MINUTE` in development.
* **"Unable to connect to the server."** in the UI. Check that the backend runs on port 8000 and that `VITE_API_BASE_URL` matches.
* **CORS errors**. Add your frontend origin to `CORS_ORIGINS`.
* **Run/Submit say "Code execution service is temporarily unavailable."** `JUDGE0_BASE_URL` is empty or Judge0 is not reachable. Check `curl http://localhost:8000/api/health/execution` and `curl -H "X-Auth-Token: <token>" http://127.0.0.1:2358/about`, and restart the backend after editing `backend/.env`.
* **Every result is `SYSTEM_ERROR` and Judge0 reports "Internal Error" (status 13).** Judge0 1.13 needs cgroup v1. `stat -fc %T /sys/fs/cgroup` must print `tmpfs`; see section 7, step 1.
* **Compile errors for code that works on your machine.** Judge0 runs GCC 9.2 (C++14 by default), OpenJDK 13 and Python 3.8, so newer language features (C++17 structured bindings, Java `switch` arrows, `list[int]` annotations) are not available.

## Roadmap

* **Phase 1 (done):** authentication, roles, dashboards, user management
* **Phase 2 (done):** application shell, role-aware navigation, real dashboard APIs, problems and learning foundations, profile and settings
* **Phase 3 (done):** problem database, topics, tags, examples, starter code, hidden test cases (stored, not executed), admin problem management, search/filter/pagination, DSA learning path
* **Phase 4 (done):** Monaco coding workspace, autosaved per-language drafts, settings, fullscreen, responsive layout
* **Phase 5 (built, real-Judge0 verification pending):** RUN / SUBMIT through Judge0, hidden tests, verdicts, submission storage
* **Phase 6 (built; depends on Phase 5 for real verdicts):** per-test results, submission history and details, solved state and attempts, progress, streaks, heatmap, leaderboard, staff analytics
* **Later:** classrooms, contests, assignments and the AI tutor
