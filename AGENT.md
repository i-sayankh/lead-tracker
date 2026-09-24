# AGENT.md — AI-Assisted Development Log

## 1. Summary

_To be finalized at the end of the project._

## 2. AI Tools Used

| Tool | Model/Version | Used for |
|---|---|---|
| Claude Code (desktop) | Claude | Planning conversation that produced the written execution plan |
| Claude Code (VS Code extension) | Claude Opus 5.5 | Execution session: implementation, tests, docs, following the plan phase by phase |

_Skills invoked are listed as they are used (see running log)._

## 3. Workflow

_To be finalized._

## 4. Key Prompts

1. "help me plan this assignment, I want to use FastAPI as the backend, should I have two dedicated repos for the front end and backend for separation of concern and easier deployment?"
   — Led to the monorepo decision (see §6).
2. "should I also implement a sign up/log in functionality in the system that'll prevent unathenticated users from interacting with the endpoints and the client?"
   — Led to the decision to leave authentication out of scope (see §6).
3. "I want you to create a execution plan md file which I'll feed into another claude code session in my repo … for the backend I want to have proper type definitions for every request and response schema and all possible errors should also be documented, the swagger and redoc documents should reflect a very carefully written code and API design … instruct to use any necessary skills … it should commit and push step by step … the AGENT.md should be properly documented … for deployment I'll use vercel for frontend and render for backend"
   — Produced the detailed execution plan that drove the implementation session.

## 5. AI-Generated vs Manually Written

_To be finalized with the author's input._

## 6. Key Engineering Decisions

### Monorepo instead of two repositories
- **Decision:** one repository with `backend/` and `frontend/` folders.
- **Alternatives considered:** two repositories (the author's initial preference, for separation of concerns and deployment).
- **Why:** the brief asks for one repository; one commit trail tells the story of cross-cutting changes; README and AGENT.md cover the whole system; separation of concerns comes from the folder boundary; Vercel and Render both deploy from a subdirectory.
- **Consequence:** CI runs both jobs on every push; deploy targets are configured with a root directory.

### No authentication
- **Decision:** no sign-up or login.
- **Alternatives considered:** adding sign-up/login to protect the endpoints and the client.
- **Why:** not in the brief, not a grading criterion, roughly a day of work, and the data is demo data.
- **Consequence:** anyone with the URL can read and write leads. Documented as a trade-off and future improvement.

### Deployment targets
- **Decision:** Vercel (frontend), Render (backend), Neon (Postgres).
- **Why:** Vercel and Render were the author's choice; Neon was picked because Render's free Postgres is deleted after 30 days, which could fall inside the review window.

### Frontend types generated from OpenAPI
- **Decision:** `frontend/src/api/schema.d.ts` is generated from `backend/openapi.json` with `openapi-typescript`; no hand-written API types.
- **Why:** follows from the requirement of typed request and response schemas end to end; one source of truth (Pydantic).
- **Consequence:** CI fails if either generated file drifts.

## 7. AI Suggestions Rejected or Overridden

_To be built from the running log._

## 8. Verification of AI Output

_To be finalized._

## 9. Lessons Learned

_To be finalized._

<!-- RUNNING LOG -->
## Running log (removed when finalized)

- **Step 1.1 — repository scaffold.** Instruction: "Execute EXECUTION_PLAN.md". Skills: `superpowers:executing-plans`. Docker daemon was not running; started Docker Desktop. Existing `README.md` was UTF-16 encoded; rewritten as UTF-8. Local Node is 24 (plan asks for 22 LTS); CI pins 22.
- **Step 1.2 — backend scaffold, config and health check.** Skills: `superpowers:test-driven-development` (health test written first; failed on missing `app.main`, then passed). Candidate rejections from own drafts: (a) the first `Settings` draft declared the CORS field as `cors_origins_raw` without an alias, so it would have silently ignored the `CORS_ORIGINS` env var and always used the default; fixed with `validation_alias="CORS_ORIGINS"`. (b) mypy strict flagged an unnecessary `# type: ignore` on `Settings()`; removed. Deviation: the test client dependency is `httpx2` instead of `httpx`, because the installed Starlette emits a deprecation warning for `httpx` with `TestClient`.
- **Step 1.3 — lead model and migration.** Migration written by hand; verified `upgrade head` → `downgrade base` (enum type dropped) → `upgrade head`, and `\d leads` shows the unique constraint and both indexes. `LeadStatus` uses `enum.StrEnum` (Python 3.11+) rather than `class LeadStatus(str, Enum)`, which ruff's `UP` rules flag. The `status` column maps enum *values* (`values_callable`) so the PG enum stores `new`, not `NEW`. Ruff's isort treated `alembic` as first-party because of the local `alembic/` folder; fixed with `known-third-party`.
- **Step 2.1 — schemas and error envelope.** 404/405/503 envelope tests written first and watched fail. Candidate rejections from own drafts: (a) the 500-handler no-leak test was added after the handler existed, so it passed on first run; it is kept as a regression guard, not as TDD evidence. (b) mypy strict rejected the shared `EXAMPLE_LEAD` dict inside `json_schema_extra` until it was typed as pydantic's `JsonDict`. (c) The health check originally let any DB exception bubble up as a 500; it now maps `SQLAlchemyError` to the documented `503 SERVICE_UNAVAILABLE`.
- **Step 2.2 — create lead.** 14 tests written first; all failed with 404 (route missing) before the implementation, then passed. Uniqueness relies on the `uq_leads_email` constraint: insert, catch `IntegrityError`, roll back, raise `LeadEmailConflictError` (no SELECT-before-INSERT). Case-insensitive uniqueness comes from lowercasing in the schema before the insert.
- **Step 2.3 — list and search.** 15 tests written first, all failed before the route existed. User input to `ILIKE` escapes `\`, `%` and `_` with `escape="\\"`; the `100%` / `snake_case` test proves wildcards match literally. Tooling defect caught: patching files with inline Python on Windows wrote cp1252 (breaking the UTF-8 en dash) and mangled `\n` escapes inside the heredoc; fixed and switched to direct file edits.
