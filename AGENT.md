# AGENT.md — AI-Assisted Development Log

## 1. Summary

This project was built with Claude Code in two sessions: a planning conversation, where I (the author) set the requirements and made the architectural calls, and an execution session, where Claude Code implemented a detailed written plan phase by phase, committing and pushing after every step. I owned the direction, the key decisions, and everything that needed an account or a dashboard (Neon, Render, Vercel). AI output was never taken on trust: the API was built test-first against real PostgreSQL, a contract test guards the OpenAPI documentation, frontend types are generated rather than written, every step ran lint, type checks and tests before committing, and the finished app was driven in a real browser locally and on the live deployment.

## 2. AI Tools Used

| Tool | Model/Version | Used for |
|---|---|---|
| Claude Code (desktop) | Claude | Planning conversation: repo structure, auth scope, stack and hosting choices; produced the written execution plan the build followed |
| Claude Code (VS Code extension) | Claude Opus 5.5 | Execution session: all implementation, tests, CI, docs, deployment config, debugging the deployment |
| ↳ skill `superpowers:executing-plans` | | Drove the plan step by step with a progress ledger and recorded rulings for every deviation |
| ↳ skill `superpowers:test-driven-development` | | Every backend endpoint: failing test first, watched it fail, then the implementation |
| ↳ skill `design-md` | | Pulled the Linear design system into `frontend/DESIGN.md`, then adapted it for a data tool |
| ↳ skill `minimalist-skill` | | Restraint rules (neutral palette, hairlines, muted status tags); parts were rejected, see §7 |
| ↳ skill `web-design-guidelines` | | Fetched Vercel's current Web Interface Guidelines and audited `frontend/src` |
| ↳ skill `playwright-skill` | | Real-browser runs of every flow at 1280px and 375px, locally and on the live site; screenshots |
| ↳ skill `code-review` | | Correctness review of the whole codebase (8 accepted findings, see §7 for the rejected one) |
| ↳ skill `simplify` | | Four parallel review agents (reuse, simplification, efficiency, altitude) followed by a cleanup pass |

The `security-review` skill was attempted but needs a git diff range that did not exist (everything was already pushed), so its checklist was applied by hand instead (§8).

## 3. Workflow

1. **Planning conversation.** I described the assignment and asked the design questions in §4. The outcome was a long, explicit execution plan: target architecture, every endpoint and schema, the error contract, the exact test cases, the commit sequence, which skills to use where, and guardrails such as "no SQLite in tests", "never `*` in CORS", and "no hand-written API types".
2. **Execution session.** Claude Code followed the plan step by step. Each step was: implement → run checks → append to a running log → commit → push. Where the plan was wrong or a tool had changed since it was written, the deviation was decided, logged with its reason and cost, and carried forward (several are in §7).
3. **Human checkpoints.** Work stopped for me wherever an account or a judgment call was needed: creating the GitHub repository, provisioning Neon, Render and Vercel, fixing the failed first deploy, approving the production seed, and approving a history rewrite.
4. **Guardrails that made AI output checkable:**
   - **TDD for the API:** 59 backend tests against real PostgreSQL, each written to fail first.
   - **An OpenAPI contract test:** fails if any operation, parameter or schema field lacks documentation, if any error response lacks named examples, or if FastAPI's default validation schema reappears next to the custom error envelope.
   - **Generated frontend types:** `openapi.json` → `schema.d.ts`; CI fails if either drifts.
   - **Verification before every commit:** ruff, mypy strict, pytest, and on the frontend typecheck, oxlint, Vitest and a production build.
   - **CI** (GitHub Actions) as the automated gate on every push.
   - **Real-browser checks** with Playwright rather than trusting unit tests alone.

## 4. Key Prompts

**Planning conversation** (verbatim, lightly trimmed):

1. "help me plan this assignment, I want to use FastAPI as the backend, should I have two dedicated repos for the front end and backend for separation of concern and easier deployment?"
   → Discussion of trade-offs; I chose a monorepo (see §6, Q1).
2. "should I also implement a sign up/log in functionality in the system that'll prevent unathenticated users from interacting with the endpoints and the client?"
   → Decided against it for this brief; documented as a trade-off and future improvement (§6, Q2).
3. "I want you to create a execution plan md file which I'll feed into another claude code session in my repo … for the backend I want to have proper type definitions for every request and response schema and all possible errors should also be documented, the swagger and redoc documents should reflect a very carefully written code and API design … instruct to use any necessary skills … it should commit and push step by step … the AGENT.md should be properly documented … for deployment I'll use vercel for frontend and render for backend"
   → The execution plan: typed schemas with examples on every field, a single error envelope, the OpenAPI contract test, the generated-types chain, and the step-by-step commit trail visible in the git history.

**Execution session:**

4. "Execute EXECUTION_PLAN.md"
   → Phases 1–6.1 end to end: 18 commits, CI green, then a stop at the deployment checkpoint with exact dashboard instructions.
5. "backend deployment issue" (with Render's build log: `No matching distribution found for pywin32==311`)
   → Root cause found in the repo, not the app: a `requirements.txt` from a global `pip freeze` had been committed, and the Render service had been created without the Blueprint, so Render ignored the `uv` build. Explained, with the correct service settings.
6. "remove that file and the commit as well"
   → The commit was dropped and `main` was force-pushed with a lease (refuses if the remote moved). The redeploy succeeded.
7. "yeah seed the production DB and let's come to the AGENT.md after everything is done"
   → Production seeded with 25 demo leads; full browser run on the live site; README; clean-clone verification of the README's setup steps.

## 5. AI-Generated vs Manually Written

| Area / file | Origin | Notes |
|---|---|---|
| Requirements, architectural decisions (§6 Q1–Q3), hosting choice | Human | Decided by me in the planning conversation |
| Planning prompts and execution-session direction | Human | The prompts in §4 |
| Execution plan (kept local, not in the repo) | AI-generated from my prompt | Its guardrails shaped everything below |
| `backend/` (app, migration, tests, seed script) | AI-generated | Verified by 59 tests against PostgreSQL, ruff, mypy strict, and CI |
| `frontend/` (components, hooks, API client, tests) | AI-generated | Verified by 20 tests, typecheck, lint, build, and Playwright runs |
| `backend/openapi.json`, `frontend/src/api/schema.d.ts` | Tool-generated | Produced by FastAPI and openapi-typescript; CI rejects hand edits |
| `frontend/DESIGN.md` | AI-adapted from the Linear design system | Adaptation section added for a light/dark data tool; contrast pairs measured |
| CI, `docker-compose.yml`, `render.yaml` | AI-generated | CI green on every push; `render.yaml` build/start commands dry-run locally |
| README.md, AGENT.md | AI-written from the project log | Checked against the code (counts, versions, commands) |
| Neon, Render and Vercel setup | Human | Accounts, services, environment variables, domains, and the fix after the failed first deploy |

## 6. Key Engineering Decisions

Framed as the questions a reviewer is likely to ask.

**Q1. Why one repository instead of separate frontend and backend repos?**
- **Decision:** a monorepo with `backend/` and `frontend/`.
- **Alternatives:** two repositories. This was my initial preference, for separation of concerns and independent deployment.
- **Why:** the brief asks for one repository, and one commit trail tells the story of changes that cross the API boundary (a schema change and the matching frontend change land together). Separation of concerns comes from the folder boundary, and Vercel and Render both deploy from a subdirectory. Crucially, CI can check that the frontend's generated types match the backend's spec in the same commit, which two repos cannot do without extra machinery.
- **Trade-off:** both CI jobs run on every push, even when only one side changed.

**Q2. Why no authentication?**
- **Decision:** leave sign-up/login out.
- **Alternatives:** adding sign-up/login to protect the endpoints and the client, which I considered.
- **Why:** it isn't in the brief, it doesn't count toward any grading criterion, it would cost about a day, and the data is demo data. The time went into validation, error handling, tests and documentation instead.
- **Trade-off:** anyone with the URL can read and add leads. Listed first under Future Improvements, with role-based access.

**Q3. How do the frontend and backend stay in agreement about the API?**
- **Decision:** Pydantic schemas are the single source of truth. FastAPI generates `openapi.json`, `openapi-typescript` generates `schema.d.ts`, and the client imports its types from it.
- **Alternatives:** hand-written TypeScript interfaces mirroring the backend.
- **Why:** hand-written types drift silently. With generation, a renamed field becomes a TypeScript compile error. `ErrorCode` arrives as a string union, so the UI can switch on error codes safely.
- **Trade-off:** two generated files are committed, and CI must regenerate and diff them (it does).

**Q4. How is email uniqueness guaranteed under concurrent requests?**
- **Decision:** a `UNIQUE` constraint on `email`. Emails are lowercased before insert; the insert is attempted, and `IntegrityError` on `uq_leads_email` is caught and mapped to `409 LEAD_EMAIL_CONFLICT`.
- **Alternatives:** check with a `SELECT` first, then insert.
- **Why:** two simultaneous requests would both pass a `SELECT` check. Only the database constraint is race-safe. Lowercasing in the schema makes `Jane@Acme.com` and `jane@acme.com` the same lead.
- **Trade-off:** conflict detection relies on the constraint's name, now defined once in the model and shared.

**Q5. What does an error look like, and why one shape for all of them?**
- **Decision:** every non-2xx response is `{"error": {"code", "message", "details"}}`, with a fixed `ErrorCode` enum. `details` lists each invalid field (`body.email`, `query.limit`) for 422 and 409 responses.
- **Alternatives:** FastAPI's default `{"detail": ...}`, which has a different shape for validation errors than for everything else.
- **Why:** one parser on the client, and inline field errors come straight from `details[].field`. Every error is documented with named examples in Swagger and ReDoc, and a contract test keeps it that way.
- **Consequence:** unexpected errors go through an ASGI middleware placed *inside* CORS rather than an exception handler, so even a 500 reaches the browser readable (see §7.1).

**Q6. Why test against PostgreSQL instead of SQLite?**
- **Decision:** pytest runs against a real Postgres 16 (Docker locally, a service container in CI). Migrations are applied once and the table is truncated after each test.
- **Why:** the app depends on `ILIKE`, a native enum type, `gen_random_uuid()` and `TIMESTAMPTZ`, which SQLite lacks or treats differently. Tests on SQLite would pass on code that fails in production.
- **Trade-off:** running the tests needs Docker.

**Q7. Why synchronous SQLAlchemy, offset pagination and `ILIKE` search?**
- **Decision:** the simplest correct option in each case.
  - Sync sessions: FastAPI runs them in a thread pool.
  - `limit`/`offset` with a `total` count.
  - `ILIKE '%term%'` with `%`, `_` and `\` escaped so user input matches literally.
- **Why:** they are correct and easy to test at this scale. Each has a known scaling ceiling, written down in the README trade-offs with its upgrade path: async only if I/O-bound concurrency demands it, keyset pagination, a `pg_trgm` GIN index.
- **Guardrail:** `offset` is capped at 1,000,000, because an unbounded value overflowed Postgres' bigint and produced a 500 instead of a 422 (found in review).

**Q8. How does search stay correct when the user types fast or the network is slow?**
- **Decision:** a 300 ms debounce on the search term, plus an `AbortController` that cancels the previous request whenever the query changes. Search, filter and page live in the URL.
- **Alternatives:** debounce alone, or a data-fetching library such as TanStack Query.
- **Why:** a debounce alone still lets a slow early response overwrite a newer one. Cancelling makes out-of-order results impossible. URL state makes every view shareable and refresh-proof without a router or a state library.
- **Trade-off:** a hand-written hook (`useLeads`) instead of a library. That's fine for one list screen, and it is covered by tests including a fake-timer debounce test.

**Q9. Why Neon for Postgres when the API runs on Render?**
- **Decision:** API on Render, database on Neon.
- **Why:** Render's free Postgres is deleted after 30 days, which could fall inside the review window. Neon's free tier doesn't expire.
- **Trade-off:** one more dashboard, and a cross-provider network hop between the API and the database.

**Q10. Why no UI kit, state library or date library?**
- **Decision:**
  - native `<dialog>` (focus trap and Esc for free) and native `<select>` styled as status pills;
  - `Intl.RelativeTimeFormat` for dates;
  - a small custom toast component;
  - Tailwind with design tokens from `DESIGN.md`.
- **Why:** it's a single screen. Every dependency is weight and upgrade work, and native elements bring accessibility for free.
- **Result:** after an audit against Vercel's Web Interface Guidelines, all controls are at least 40px tall, text contrast is at least 4.5:1, status colors always carry a text label, and there's a skip link, reduced-motion support and light and dark themes.

## 7. AI Suggestions Rejected or Overridden

### 1. An error handler that made server errors look like network failures
- **Context:** the error envelope and the 500 handler (Step 2.1), revisited in the code-review pass (Step 5.1).
- **AI suggested:** a catch-all handler registered with `app.add_exception_handler(Exception, handler)`. It returned the right JSON, and a test confirmed that no exception text leaked.
- **Why it was wrong:** Starlette runs `Exception` handlers in `ServerErrorMiddleware`, *outside* every user middleware, including CORS. Every 500 therefore reached the browser without `Access-Control-Allow-Origin`, the browser hid the body, and the client reported "Could not reach the server. Check your connection." A real server bug would have been shown to users as their own network problem.
- **What was done instead:** a small pure ASGI middleware, registered in `create_app` directly inside `CORSMiddleware`, converts unhandled exceptions into the envelope. It re-raises if the response has already started.
- **Guarded by:** `test_unhandled_error_response_still_carries_cors_headers`. It was written first and failed first.
- **Source:** code review pass (Step 5.1). The first replacement used `BaseHTTPMiddleware`; the simplify review rejected that too (per-request task overhead), leading to the pure ASGI version.

### 2. Operation IDs that silently came out empty
- **Context:** stable, readable `operationId`s for the OpenAPI spec (Step 2.5).
- **AI suggested:** `generate_unique_id_function=lambda route: route.name if isinstance(route, APIRoute) else ""`, a "defensive" type guard.
- **Why it was wrong:** the installed FastAPI version passes a different route object to that hook, so the guard returned `""` for every route. That produced duplicate empty operation IDs, and the generated TypeScript would have had unusable operation names. Nothing crashed; only a warning appeared.
- **What was done instead:** the plain `lambda route: route.name`.
- **Guarded by:** the OpenAPI contract test asserts every operation's ID. That test caught the bug on its first run.
- **Source:** execution Step 2.5.

### 3. A setting that would have silently ignored its environment variable
- **Context:** configuration with pydantic-settings (Step 1.2).
- **AI suggested:** a field named `cors_origins_raw` holding the comma-separated origins, parsed by a `cors_origins` property.
- **Why it was wrong:** pydantic-settings maps a field to an env var of the same name, so this read `CORS_ORIGINS_RAW`. In production, setting `CORS_ORIGINS` on Render would have done nothing, and the API would have kept allowing only `localhost:5173`: a deploy-time CORS failure with no error message.
- **What was done instead:** `validation_alias="CORS_ORIGINS"`. Later hardening rejects `*` in the list at startup.
- **Guarded by:** `tests/test_config.py` (parsing, and the wildcard rejection).
- **Source:** execution Step 1.2 (caught while reviewing the draft before committing); hardening from the security checklist (Step 5.1).

### 4. Design-skill advice that didn't fit a data tool
- **Context:** the frontend design system (Step 4.1).
- **AI suggested:**
  - The Linear DESIGN.md is dark-only and explicitly says "Don't ship a light-mode page".
  - `minimalist-skill` asked for scroll-entry animations on every block, ambient gradient backgrounds, editorial serif headings and background imagery.
- **Why it was not a fit:** both describe *marketing pages*. A CRM table used all day needs a light theme, and animation on table rows is noise. The Linear file also had no error color or status colors.
- **What was done instead:**
  - Kept Linear's tokens, type scale, radius and restraint.
  - Added a light default, with the Linear dark palette under `prefers-color-scheme: dark`.
  - Took only the muted status-tag palette and the no-heavy-shadow rules from the minimalist skill.
  - Motion is limited to 150 ms hover transitions, disabled under reduced motion.
- **Guarded by:** a contrast script over every status pair. It measured every pair at 4.5:1 or better, and caught the draft's claim of "4.6:1" for white on lavender, which is actually 4.7:1.
- **Source:** execution Step 4.1, via the `design-md` and `minimalist-skill` skills.

### 5. Plan and review suggestions that were wrong for the tools as they exist today
- **Context:** CI and deployment config (Steps 3.1 and 6.1).
- **AI suggested:**
  - The plan's CI guard `if: hashFiles('frontend/package.json') != ''` on the frontend job.
  - The plan's Render start command `uv run alembic upgrade head && uv run uvicorn …`.
- **Why they were wrong:**
  - `hashFiles()` is not available in job-level `if` expressions in GitHub Actions.
  - `uv run` syncs the default dependency groups, so after a `--no-dev` build it would reinstall pytest, mypy and ruff on every boot of the production server.
- **What was done instead:**
  - A detection step that sets an environment flag, which guards each frontend step.
  - `uv run --no-dev …` in the start command.
- **Guarded by:** CI green in both states (before and after the frontend existed), and a local dry run of the Render build and start commands confirming pytest is absent at runtime.
- **Source:** execution Steps 3.1 and 6.1 (defects in the AI-written plan).

### 6. Review findings that were deliberately not adopted
- **Context:** the automated code-review and simplify passes (Step 5.1) and the UI guidelines audit (Step 4.6).
- **AI suggested:**
  - (a) When a lead's status changes while a status filter is active, remove it from the list immediately.
  - (b) Expose a `stale` flag from the `useLeads` hook so every consumer can tell whether the data is current.
  - (c) Skip the `COUNT(*)` query on short first pages, and use `UPDATE … RETURNING` for status changes.
  - (d) Title Case on all buttons, a `…` suffix on every placeholder, and an unsaved-changes warning on the dialog.
- **Why each was not adopted:**
  - (a) A row vanishing from under the cursor mid-edit is worse UX than a briefly stale count, and the next fetch corrects it.
  - (b) There is one consumer, and it already has two explicit guards with tests.
  - (c) Micro-optimizations with no measurable benefit at this scale.
  - (d) The design system uses sentence case; the placeholders show a format, not an in-progress state; and a four-field form doesn't need a navigation guard.
- **What was done instead:** 8 other review findings were accepted and each was fixed test-first: stale rows under a failed filter, a new lead hidden by active filters, late responses leaking into a reopened form, phone search not matching `98200 11223`, and more. The rejections and their reasons are in the README trade-offs.
- **Source:** code review pass (Step 5.1) and UI audit (Step 4.6).

## 8. Verification of AI Output

- **Backend:** 59 pytest tests against PostgreSQL 16. Every endpoint and error case from the plan is covered, plus the review regressions, settings, seed idempotency and the OpenAPI contract. ruff (lint + format) and mypy `--strict` are clean.
- **Frontend:** 20 Vitest + Testing Library tests. Because the plan placed these after the components, each key behavior was checked with a deliberate mutation: removing the debounce, removing the rollback and disabling error parsing each made the relevant tests fail, and restoring the code made them pass. TypeScript strict with `noUncheckedIndexedAccess`, oxlint with warnings as errors, and a production build are all clean.
- **CI:** GitHub Actions runs all of the above on every push, plus migrations against a Postgres service container and drift checks on both generated files.
- **API docs:** Swagger UI and ReDoc were reviewed by eye and by script. All four operations have summaries, descriptions, bounded parameters with examples, and named examples for every error status. The contract test enforces this permanently.
- **Browser:** Playwright drove the full flow at 1280px and 375px (create, duplicate email, search, filter, paginate, status change surviving a reload), measured that no control is under 40px, checked for horizontal overflow, and watched the console. This ran locally, again after the review fixes, and on the live deployment with no CORS or console errors.
- **Security checklist** (applied by hand):
  - Only `.env.example` files are tracked.
  - No SQL is built from input (SQLAlchemy parameters; `ILIKE` input escaped).
  - No raw HTML rendering.
  - 500 responses never include exception text.
  - CORS is an explicit allowlist with credentials disabled, and `*` is rejected at startup.
- **Clean clone:** `main` was cloned into an empty directory and the README's setup steps were followed literally with a fresh database. Migrations, seed, both test suites, lint, type checks and build all passed; regenerating the API spec and types produced no diff; and the app from the clone passed the browser flow.
- **Environment drift:** one check caught the local virtualenv running Python 3.14 while CI and Render use 3.12. It was pinned back and everything was re-run on 3.12.

## 9. Lessons Learned

- **The written plan did the heavy lifting.** Spending the planning session on a precise plan (exact endpoints, error codes, test cases, commit sequence and guardrails) meant the execution session rarely had to guess. Where it did deviate, the plan's explicit rules made the deviation visible and easy to judge.
- **AI's most dangerous mistakes are the quiet ones.** None of the defects in §7.1–7.3 crashed anything: a 500 that looked like a network error, empty operation IDs, an env var silently ignored. Each was caught only because a specific test, contract check or review pass was looking for it. I'd now insist on contract tests and a separate review pass from the start of any AI-assisted project, not the end.
- **Tests written after the code need proof they can fail.** The frontend tests were written after the components, so passing proved little on its own. Deliberately breaking the code and watching the tests fail was a cheap way to earn back that confidence.
- **Deployment is where local assumptions break.** The first deploy failed because of a `requirements.txt` I had generated with `pip freeze` from my global Windows Python, and because I created the Render service by hand instead of from the Blueprint, so Render ignored the lock file. Separately, the first Vercel link I shared sat behind Vercel's login. Next time I'd deploy from the Blueprint and open the public URL in a private window before sharing it.
- **Generic design advice needs judgment.** The design skills were written for marketing sites. Taking their restraint while rejecting their motion and dark-only rules gave a better tool than following either one completely.
