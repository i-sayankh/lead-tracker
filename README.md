# Lead Tracker

[![CI](https://github.com/i-sayankh/lead-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/i-sayankh/lead-tracker/actions/workflows/ci.yml)

A small CRM-style lead tracker: create leads, list them newest first, search by name, email or phone, filter by status, and move a lead through the pipeline with an inline status change. React + TypeScript on the front, FastAPI + PostgreSQL on the back, with request and response types generated end to end from one source.

**Live links**

| | URL |
|---|---|
| App | https://lead-tracker-mauve.vercel.app |
| API docs (Swagger UI) | https://lead-tracker-orv1.onrender.com/docs |
| API docs (ReDoc) | https://lead-tracker-orv1.onrender.com/redoc |
| Health check | https://lead-tracker-orv1.onrender.com/api/v1/health |

> The API runs on Render's free tier, which sleeps when idle. The first request after a quiet period can take up to about 50 seconds; the app shows a "waking up the server" notice while it waits.

## Screenshots

| Desktop | Mobile (375px) |
|---|---|
| ![Lead list on desktop](docs/screenshots/app-desktop.png) | ![Lead list on mobile](docs/screenshots/app-mobile.png) |

| Swagger UI | ReDoc |
|---|---|
| ![Swagger UI for POST /api/v1/leads](docs/screenshots/swagger.png) | ![ReDoc for POST /api/v1/leads](docs/screenshots/redoc.png) |

## Features

- **Create lead** in a dialog with Name, Email, Phone and Status. Validation runs in the browser (on blur and on submit) and again on the server; server errors are shown under the matching field, and a duplicate email (compared case-insensitively) shows "A lead with this email already exists".
- **List leads** newest first, 20 per page, with "Showing 21–40 of 57" pagination.
- **Search** by any part of a name, email or phone number. Case-insensitive, debounced (300 ms), and previous requests are cancelled so results never arrive out of order. Phone search ignores spaces, dashes, dots and parentheses, so `98200 11223` finds `+919820011223`. Press `/` to jump to the search box.
- **Filter by status** (All, New, Contacted, Qualified, Lost), combinable with search.
- **Update status inline** from a status pill in each row. The change shows immediately, the row's control is disabled while saving, and it rolls back with an error toast if the server rejects it.
- **Shareable views**: search, filter and page live in the URL (`?q=acme&status=qualified&page=2`) and survive a refresh.
- **Clear states** for loading (skeleton rows), an empty database, no search results, errors (with Retry), and a free-tier cold start.
- **Accessible and responsive**: labelled controls, visible focus rings, text labels on every status color, contrast ≥ 4.5:1, all controls at least 40px tall, a skip link, `prefers-reduced-motion`, light and dark themes following the OS, and a stacked card layout below 640px.

## Architecture

```mermaid
flowchart LR
    B[Browser] -->|HTTPS| V["Vercel<br/>React SPA (static)"]
    B -->|"fetch /api/v1/... (CORS)"| R["Render<br/>FastAPI + Uvicorn"]
    R -->|"SQLAlchemy 2.0<br/>psycopg 3, TLS"| N[("Neon<br/>PostgreSQL")]
```

The browser loads the static single-page app from Vercel and calls the API on Render directly. CORS on the API allows only the listed front-end origins. The API talks to Postgres on Neon, and Alembic migrations run on every deploy before the server starts.

### Repository layout

```
lead-tracker/
├── backend/                  FastAPI service (deployed to Render)
│   ├── app/
│   │   ├── main.py           app factory: metadata, CORS, middleware, routers
│   │   ├── config.py         settings from environment (pydantic-settings)
│   │   ├── db.py             engine, session, get_db dependency
│   │   ├── models.py         SQLAlchemy model: Lead
│   │   ├── schemas.py        every Pydantic request/response model
│   │   ├── errors.py         error codes, error envelope, handlers, OpenAPI error docs
│   │   ├── services.py       create, list/search, update status
│   │   ├── routers/          leads.py, health.py
│   │   └── export_openapi.py writes backend/openapi.json
│   ├── alembic/              hand-written migration
│   ├── scripts/seed.py       idempotent demo data
│   ├── tests/                pytest against real Postgres
│   └── openapi.json          generated; CI fails if it is stale
├── frontend/                 React + Vite + TypeScript (deployed to Vercel)
│   ├── DESIGN.md             design system (Linear, adapted for this app)
│   └── src/
│       ├── api/schema.d.ts   generated from backend/openapi.json
│       ├── api/client.ts     typed fetch wrapper + ApiError
│       ├── hooks/            useLeads, useUrlState, useDebouncedValue, useToasts
│       ├── components/       LeadForm, LeadTable, StatusSelect, Toolbar, Pagination, Toasts, EmptyState
│       └── __tests__/        Vitest + Testing Library
├── .github/workflows/ci.yml
├── docker-compose.yml        local Postgres only
└── render.yaml               Render Blueprint
```

### Type-safety chain

The backend's Pydantic schemas are the single source of truth for every request and response:

1. `backend/app/schemas.py` and `errors.py` define the models, with descriptions and examples on every field.
2. FastAPI turns them into an OpenAPI 3.1 spec, exported to `backend/openapi.json`.
3. `openapi-typescript` generates `frontend/src/api/schema.d.ts` from that file.
4. `frontend/src/api/client.ts` takes its types (`Lead`, `LeadCreate`, `LeadStatus`, `ErrorCode`, …) from the generated file. No API types are written by hand.

CI regenerates both files and fails if either differs from what is committed, so a backend change that affects the API cannot land without the frontend types being updated.

### Error envelope

Every non-2xx response has the same shape, and clients branch on `error.code`:

```json
{
  "error": {
    "code": "LEAD_EMAIL_CONFLICT",
    "message": "A lead with email 'jane@acme.com' already exists.",
    "details": [{ "field": "body.email", "message": "Email already exists", "type": "conflict" }]
  }
}
```

`details` lists each invalid field for validation (422) and conflict (409) errors and is `null` otherwise. Unexpected errors return `500 INTERNAL_ERROR` without exception text (the traceback is logged server-side) and still carry CORS headers, so the browser can read them.

| Status | `code` |
|---|---|
| 404 | `LEAD_NOT_FOUND`, `ROUTE_NOT_FOUND` |
| 405 | `METHOD_NOT_ALLOWED` |
| 409 | `LEAD_EMAIL_CONFLICT` |
| 422 | `VALIDATION_ERROR` |
| 500 | `INTERNAL_ERROR` |
| 503 | `SERVICE_UNAVAILABLE` |

### API summary

All routes are under `/api/v1`. Full schemas, parameter bounds and named examples for every error are in [Swagger UI](https://lead-tracker-orv1.onrender.com/docs) and [ReDoc](https://lead-tracker-orv1.onrender.com/redoc).

| Method | Path | Success | Errors |
|---|---|---|---|
| `POST` | `/leads` | `201` Lead | `409` duplicate email, `422` invalid body, `500` |
| `GET` | `/leads?q=&status=&limit=&offset=` | `200` page of leads + `total` | `422` invalid query, `500` |
| `PATCH` | `/leads/{lead_id}/status` | `200` updated Lead | `404` unknown lead, `422` invalid id or body, `500` |
| `GET` | `/health` | `200` `{"status":"ok","database":"ok"}` | `503` database unreachable |

Lead fields: `id` (UUID), `name` (1–100 chars), `email` (unique, stored lowercase), `phone` (stored normalized: optional `+` and 7–15 digits), `status` (`new` \| `contacted` \| `qualified` \| `lost`, default `new`), `created_at` (ISO 8601 with offset). `limit` is 1–100 (default 20) and `offset` is 0–1,000,000.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| API | FastAPI 0.141 | Typed request/response models, generated OpenAPI, dependency injection for the DB session |
| Validation | Pydantic 2 + `email-validator` | One set of models validates input, serializes output and documents the API |
| ORM / migrations | SQLAlchemy 2.0 (sync) + Alembic | Typed `Mapped[...]` models; migrations written by hand for the native enum |
| Database | PostgreSQL 16 (Neon in production) | Native enum, `gen_random_uuid()`, `TIMESTAMPTZ`, `ILIKE`; Neon's free tier doesn't expire |
| Driver | psycopg 3 | Current Postgres driver for SQLAlchemy 2 |
| Backend tooling | uv, ruff, mypy (strict), pytest | Locked, reproducible installs; lint, format and type checks in CI |
| Frontend | React 19 + TypeScript (strict, `noUncheckedIndexedAccess`) + Vite 8 | Fast builds; strict types catch missing-data cases |
| Styling | Tailwind CSS v4 with design tokens as CSS variables | Tokens from `frontend/DESIGN.md`; light and dark themes from one set of variables |
| API types | openapi-typescript | Frontend types generated from the backend spec |
| Frontend tests | Vitest + Testing Library + jsdom | Tests run against rendered components with `fetch` mocked |
| Frontend lint | oxlint | Default linter of the current Vite template; includes React hooks rules |
| Hosting | Vercel (frontend), Render (API), Neon (DB) | Free tiers that deploy from a subdirectory of one repository |

No router, state-management, UI-kit, date or toast library: the app is a single screen, dates use `Intl`, and toasts are a small component plus a hook (about 85 lines).

## Setup instructions (local)

**Prerequisites:** Git, Docker (for the local database), Python 3.12, [uv](https://docs.astral.sh/uv/) (`pip install uv`), Node.js 22 or newer.

```bash
git clone https://github.com/i-sayankh/lead-tracker.git
cd lead-tracker

# 1. Database: Postgres 16 on localhost:5432 with databases "leads" and "leads_test"
docker compose up -d db
```

**Backend** (in a first terminal):

```bash
cd backend
uv sync                              # creates .venv with runtime + dev dependencies
cp .env.example .env                 # points at the local "leads" database
uv run alembic upgrade head          # creates the leads table
uv run python -m scripts.seed        # optional: 25 demo leads
uv run uvicorn app.main:app --reload # http://localhost:8000/docs
```

**Frontend** (in a second terminal):

```bash
cd frontend
npm ci
cp .env.example .env                 # VITE_API_BASE_URL=http://localhost:8000
npm run dev                          # http://localhost:5173
```

**Running the tests and checks**

```bash
# backend (needs the docker database; uses the separate leads_test database)
cd backend
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run mypy app scripts

# frontend
cd frontend
npm test -- --run
npm run typecheck
npm run lint
npm run build
```

**Regenerating the API types** after changing a backend schema or route:

```bash
cd backend && uv run python -m app.export_openapi   # writes backend/openapi.json
cd ../frontend && npm run gen:api                   # writes src/api/schema.d.ts
```

Commit both files; CI fails if they are out of date.

## Environment variables

**Backend** (`backend/.env`, or the Render dashboard)

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | yes | | Postgres connection string. `postgres://` and `postgresql://` are rewritten to `postgresql+psycopg://`, so Neon and Render strings can be pasted as-is. |
| `CORS_ORIGINS` | no | `http://localhost:5173` | Comma-separated browser origins allowed to call the API. `*` is rejected at startup. |
| `ENVIRONMENT` | no | `development` | `development`, `test` or `production`. |
| `TEST_DATABASE_URL` | no | `postgresql+psycopg://postgres:postgres@localhost:5432/leads_test` | Database used by `pytest`. The suite migrates it and empties the `leads` table after each test, so never point it at real data. |

**Frontend** (`frontend/.env`, or the Vercel dashboard)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_BASE_URL` | yes | Base URL of the API, without a trailing slash, e.g. `https://lead-tracker-orv1.onrender.com`. The app refuses to start without it. Read at build time, so redeploy after changing it. |

## Deployment steps

The app runs on three free services: Neon (database), Render (API) and Vercel (frontend).

1. **Neon (Postgres).** Create a project and copy the **pooled** connection string, keeping `?sslmode=require`. Neon's free tier doesn't expire; Render's free Postgres is deleted after 30 days, which is why it isn't used.
2. **Render (API).** Either use **New → Blueprint** and select this repository (it reads `render.yaml`), or create a **Web Service** from the repository with these settings:

   | Setting | Value |
   |---|---|
   | Root Directory | `backend` |
   | Runtime | Python |
   | Build Command | `pip install uv && uv sync --frozen --no-dev` |
   | Start Command | `uv run --no-dev alembic upgrade head && uv run --no-dev uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | Health Check Path | `/api/v1/health` |

   Environment: `PYTHON_VERSION=3.12.13`, `ENVIRONMENT=production`, `DATABASE_URL=<Neon string>`, `CORS_ORIGINS=http://localhost:5173` for now. Deploy, then check `https://<service>.onrender.com/api/v1/health` returns `{"status":"ok","database":"ok"}`.

   Don't add a `requirements.txt`: Render would install from it instead of from `uv.lock`.
3. **Vercel (frontend).** Add a new project from the repository with Root Directory `frontend` and framework preset Vite, and set `VITE_API_BASE_URL=https://<service>.onrender.com`. After deploying, use the project's **production domain** (Settings → Domains). The per-deployment URLs are behind Vercel Authentication by default and show visitors a login page.
4. **Connect them.** On Render, set `CORS_ORIGINS` to the Vercel production URL (add `,http://localhost:5173` if you want to run the frontend locally against production). Saving triggers a redeploy.
5. **Demo data (optional).** Run `uv run python -m scripts.seed` locally with `DATABASE_URL` set to the Neon string. Re-running it skips leads that already exist.

Both services redeploy automatically when `main` changes.

## Testing

| Suite | Count | What it covers |
|---|---|---|
| Backend, pytest against real PostgreSQL | 59 tests | Create (all fields, lowercasing and phone normalization, case-insensitive duplicate 409, every 422 case including malformed JSON and unknown fields); list (empty, order, pagination and `total`, search by name/email/phone, phone typed with separators, `%` and `_` matched literally, status filter, filter + search, every out-of-range parameter); status update (persistence, idempotency, 404, every 422 case); health (200, 503, 500 without leaking exception text, CORS headers on 500); settings (URL normalization, CORS parsing, `*` rejected); seed idempotency; and an **OpenAPI contract test** that fails if any operation lacks a summary, description or named error examples, if any schema field lacks a description, or if FastAPI's default `HTTPValidationError` reappears. |
| Frontend, Vitest + Testing Library | 20 tests | API client (error envelope → `ApiError`, network failure, non-JSON responses, aborts); create form (client validation, 409 under Email, server detail mapping, trimmed payload, closes on success); status select (optimistic change, rollback + error toast); app (empty state, no-results + Clear filters, debounced search with fake timers, error state replacing stale rows, no empty-state flash while loading, filters cleared after create, late responses from a closed form ignored). |
| CI (GitHub Actions) | every push | Backend: ruff, ruff format, mypy strict, migrations, pytest against a Postgres 16 service, OpenAPI drift check. Frontend: generated-types drift check, typecheck, lint, tests, production build. |
| Browser (Playwright, run manually) | desktop 1280px + mobile 375px | The full flow on the live deployment: create, duplicate email, search, filter, paginate, status change surviving a reload, no control under 40px, no horizontal overflow, no console or CORS errors. |

Why not SQLite for tests: `ILIKE`, native enums, `gen_random_uuid()` and `TIMESTAMPTZ` behave differently or don't exist there, so the tests run against the same database engine as production.

## Trade-offs

- **No authentication.** The brief doesn't ask for it, and the app assumes a single trusted operator working with demo data. Anyone with the URL can read and add leads.
- **Synchronous SQLAlchemy.** FastAPI runs sync endpoints in a thread pool, which is plenty at this scale and simpler to write and test than the async stack.
- **Offset pagination.** Simple, and gives "page N of M", but deep pages get slower because Postgres still walks the skipped rows. `offset` is capped at 1,000,000.
- **`ILIKE` substring search.** A `%term%` pattern can't use a normal B-tree index, so every search scans the table. Fine for thousands of rows, not millions.
- **Any status can move to any other status.** There is no enforced pipeline order (e.g. `lost` can go back to `new`), and setting the same status again is an idempotent success.
- **Free-tier hosting.** Render sleeps after inactivity, so the first request can take up to ~50 s; the UI says so instead of looking broken.
- **No delete, edit or detail page.** Kept to the four features in the brief.
- **A status change under an active filter keeps the row in place** until the next refresh, so rows don't vanish while you're working on them. The count can be briefly stale.

## Future improvements

- Authentication and role-based access (e.g. admins vs. sales reps).
- A status transition state machine, with an activity/audit history per lead (who changed what, when).
- A `pg_trgm` GIN index for fast substring search at scale.
- Keyset (cursor) pagination for large tables.
- Lead detail and edit pages, and delete with undo.
- Request IDs and structured JSON logging.
- Rate limiting on the public API.
- End-to-end browser tests (Playwright) in CI against a preview deployment.
- CSV import and export.
