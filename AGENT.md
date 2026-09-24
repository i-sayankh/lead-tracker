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
- **Step 2.4 — update status.** 7 tests written first (all failed), then implemented. `LeadStatusUpdate.status` is required (not Optional); malformed UUIDs, missing body/status and extra fields all get the 422 envelope. The OpenAPI example for a malformed UUID was first written from memory with a longer message; replaced with the exact message pydantic produces after checking it.
- **Step 2.5 — OpenAPI polish and contract tests.** Skills: `playwright-skill` (Swagger and ReDoc screenshots, checked by eye and by script: 4 operations, POST documents 201/409/422/500, no undescribed `string` parameters). Contract tests written first; they caught two real defects in my own drafts: (a) `generate_unique_id_function` guarded with `isinstance(route, APIRoute)` produced an empty `operationId` for every route, because this FastAPI version passes a different route object; replaced with the plain `route.name`. (b) Query/path parameters used `examples=[...]`, which only lands inside the JSON Schema and is not shown as a parameter example; switched to named `openapi_examples`. `export_openapi.py` forces LF line endings so the generated file is identical on Windows and in CI.
- **Step 3.1 — GitHub Actions.** Plan suggested `if: hashFiles('frontend/package.json') != ''` on the frontend job, but `hashFiles` is not available in job-level expressions; used a detection step that sets `HAS_FRONTEND` and guards each later step.
- **Step 4.1 — frontend scaffold and typed API client.** Skills: `design-md` (Linear DESIGN.md copied to `frontend/DESIGN.md`, plus an adaptation section), `minimalist-skill`. Decisions and deviations: (a) Linear's DESIGN.md is dark-only and forbids a light theme for its *marketing* page; the app adds a light default with the Linear dark palette under `prefers-color-scheme: dark`, because the plan asks for both and a CRM tool is used all day. (b) Status pill colors and a danger color are not in the Linear file; added muted pairs (from `minimalist-skill`'s pastel tags) and verified every pair ≥ 4.5:1 with a contrast script. My first draft claimed 4.6:1 for white on lavender; the script measured 4.7:1, so the doc was corrected. (c) Rejected parts of `minimalist-skill`: scroll-entry animations, ambient gradient backgrounds, editorial serif headings and background imagery; they suit marketing pages, not a data table. Kept: neutral palette, 1px hairlines, no heavy shadows, muted pastel tags, `<kbd>` shortcut hints, system fonts (no Inter). (d) `openapi-typescript@7` declares a TypeScript 5 peer dependency; the Vite template now ships TypeScript 6. Pinned TypeScript `~5.9` instead of forcing `--legacy-peer-deps` everywhere. (e) openapi-typescript v7 marks every field with a default as required, which made `LeadCreate.status` mandatory in TypeScript although the API treats it as optional; fixed with `--default-non-nullable false`. (f) The Vite template now uses `oxlint`; kept as the `lint` script with `--deny-warnings`. (g) `@testing-library/dom` added as the required peer of `@testing-library/react`.
- **Step 4.2 — list, search, filter, pagination.** Checked in a real browser with `playwright-skill` (light, dark, 375px; `/` shortcut, debounced search updating `?q=`, status filter, no-results state, Clear filters). Candidate rejections from own drafts: (a) the first `useLeads` set `loading`/`error` state synchronously at the top of the effect; oxlint's `react(set-state-in-effect)` flagged it. Rewritten so `loading` and `slow` are derived from which query the last settled response belongs to; the request is still cancelled with `AbortController` on every query change. (b) The no-results message ignored the status filter when a search term was also set ("No leads match 'north'" while filtering by Qualified); now "No qualified leads match 'north'". (c) The table becomes stacked cards below 640px with CSS only (one DOM, `data-label` per cell) instead of rendering a second mobile list.
- **Step 4.3 — create lead dialog.** Native `<dialog>` with `showModal()` (focus trap and Esc for free); client validation mirrors the server rules; server `details[].field` is mapped onto inline field errors and a 409 shows under Email. Verified in the browser: empty submit shows three inline errors and focuses Name; duplicate email with different casing gets the 409 under Email with `aria-invalid`; success closes the dialog, shows "Lead created", and the new lead is the first row; Esc resets the form. The toast component was pulled forward from Step 4.4 because this step needs the success toast. Own-draft fixes: the first draft re-threw non-API errors from the async submit handler (an unhandled promise rejection), now shown as a form error; the Name placeholder was a realistic name that looked like pre-filled data, replaced with "Full name"; per-toast `role` attributes inside the `aria-live` region were removed to avoid double announcements.
- **Step 4.4 — inline status update.** `StatusSelect` keeps only an optimistic override (`shown = optimistic ?? lead.status`), so rollback is clearing the override and no effect is needed to sync props into state. Verified in the browser in light and dark themes: the select changes immediately and is disabled while the PATCH is pending, the change survives a reload, and a forced 500 (Playwright route interception) rolls back and shows an error toast. Own-draft fix: the chevron icon combined the pill's background class with `bg-transparent` (conflicting utilities); the pill colors moved to the wrapper and the select/chevron inherit them.
