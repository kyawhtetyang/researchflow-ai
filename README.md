# ResearchFlow AI

Agentic research workflow platform:

```text
Plan -> Research -> Analyze -> Report -> Store
```

ResearchFlow AI executes asynchronous, multi-step research jobs with persisted workflow steps, web sources, analysis, and cited reports.

## Current Release
- Release line: `1.2.0`
- Stable predecessor: `1.1.0`
- Stack: FastAPI + PostgreSQL/pgvector + background worker + React/Vite frontend
- LLM path: Gemini with OpenAI-compatible fallback support
- Search path: Tavily web search
- Schema ownership: Alembic migrations

## Architecture

```text
React/Vite
    |
    v
FastAPI API
    |
    | create queued job
    v
PostgreSQL / pgvector
    |
    | atomic claim with SKIP LOCKED
    v
Background worker
    |
    v
Workflow
    |- Plan
    |- Research
    |- Analyze
    `- Report
    |
    +--> LLM service
    `--> Search service
    |
    v
Persist steps + sources + report + terminal job state
```

The API owns HTTP concerns and persists new jobs as `queued`. The worker is the sole workflow executor. It atomically claims queued jobs, commits the claim before provider calls, runs the application workflow, and persists either a completed result or a safe failed state.

The active workflow application core lives in `backend/app/workflow/`. Framework adapters and RAG integrations are intentionally kept outside the active runtime and documented under `docs/future/`.

## Job Lifecycle

```text
queued -> in_progress -> completed
                     `-> failed
```

Only queued jobs are claimable. PostgreSQL row locking with `FOR UPDATE SKIP LOCKED` prevents concurrent workers from claiming the same job.

## Setup

```bash
cp .env.example .env
docker compose up -d --build
open http://127.0.0.1:8000/
open http://127.0.0.1:8000/docs
```

Docker Compose waits for PostgreSQL health, runs `alembic upgrade head` in a one-shot migration service, and starts both the API and worker only after migrations succeed.

Gemini defaults to `gemini-3.6-flash`. Provider credentials remain environment configuration and must not be committed.

## Frontend Development

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Local Vite development proxies `/api` to `http://127.0.0.1:8000`. FastAPI serves the built Vite app from `frontend/dist/` when that build exists.

## Verify

```bash
docker compose exec -T -e PYTHONPATH=/app api pytest -q
cd frontend && npm run check
python3 backend/scripts/first_boot_verify.py http://127.0.0.1:8000
```

The first-boot verification requires configured LLM and search provider credentials because it submits a real asynchronous research job and waits for the worker to complete it.

CI validates Alembic migrations, backend tests, frontend lint/tests/build, the production Docker image, Compose service builds, and the Compose migration container.

## API
- `GET /health`
- `GET /api/capabilities`
- `POST /api/research/`
- `GET /api/research/{job_id}`
- `GET /api/research/{job_id}/chat`
- `GET /api/research/{job_id}/summary`
- `GET /api/jobs/`
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/{job_id}/steps`
- `GET /api/reports/{job_id}`
- `GET /api/reports/{job_id}/sources`
- `POST /api/eval/run`

## Runtime Notes
- The backend is asynchronous: research jobs are created as `queued` and processed only by the worker.
- Workers use database row locking with `SKIP LOCKED` so multiple workers do not claim the same queued job.
- Worker and workflow lifecycle events are logged for operational visibility.
- The worker handles SIGTERM/SIGINT and stops claiming new work while allowing the active call to return before exit.
- The frontend polls `GET /api/research/{job_id}/chat` and understands both current `researcher`/`analyst` labels and legacy workflow labels.
- Production requires the web and worker services to share the same `DATABASE_URL` and provider credentials.
- Do not use `Base.metadata.create_all()` for production schema changes; add and apply Alembic migrations.

## v1.2.0 Scope

v1.2.0 is an architecture and runtime-correctness release rather than a feature-expansion release. It separates the HTTP boundary from workflow execution, makes the worker the sole executor, establishes canonical job states, strengthens PostgreSQL concurrency behavior, expands backend/frontend tests, adds operational logging, refreshes provider defaults, and removes inactive experimental runtime packages.

RAG, LangGraph, LangChain, LlamaIndex, OpenAI Agents SDK orchestration, Redis, Celery, Kubernetes, authentication, and distributed tracing are not part of the v1.2.0 active runtime.

## Release Convention

ResearchFlow AI uses Semantic Versioning:

```text
vMAJOR.MINOR.PATCH
```

A release is complete only after CI, clean-checkout validation, migration validation, and deployment smoke checks pass for the exact commit that receives the Git tag.
