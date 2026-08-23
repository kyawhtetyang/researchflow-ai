# ResearchFlow AI

Agentic research workflow platform:

```text
Plan -> Search -> Analyze -> Report -> Store
```

ResearchFlow AI is the next step after `RAG Knowledge Assistant`. The earlier RAG project proves retrieval QA. ResearchFlow AI proves multi-step research orchestration with stored jobs, sources, workflow steps, and cited reports.

## Current Release
- Release line: `1.1.0` production-hardening candidate
- Stable predecessor: `1.0.0`
- Stack: FastAPI + PostgreSQL/pgvector + background worker + React/Vite frontend
- LLM path: Gemini with OpenAI-compatible fallback support
- Search path: Tavily web search
- Schema ownership: Alembic migrations

## Architecture

```text
React/Vite
    |
    v
FastAPI API ----> PostgreSQL / pgvector
    |                    ^
    | queue job          |
    v                    |
Background worker -------+
    |
    v
Plan -> Search -> Analyze -> Report
```

New research requests are persisted as queued jobs. The worker claims queued jobs, records workflow steps and sources, and stores the final cited report.

## Setup

```bash
cp .env.example .env
docker compose up -d --build
open http://127.0.0.1:8000/
open http://127.0.0.1:8000/docs
```

Docker Compose applies `alembic upgrade head` before starting the API. The worker starts after the API and database are available.

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

CI also validates Alembic migrations, backend tests, frontend lint/tests/build, and the production Docker image.

## API
- `GET /health`
- `GET /api/capabilities`
- `POST /api/research/`
- `GET /api/research/{job_id}`
- `GET /api/research/{job_id}/chat`
- `GET /api/research/{job_id}/summary`
- `GET /api/jobs/`
- `GET /api/reports/{job_id}`
- `POST /api/eval/run`

## Runtime Notes
- The backend is async-first: new research jobs are created as `queued` and processed by the worker.
- Workers use database row locking with `SKIP LOCKED` so multiple workers do not claim the same queued job.
- The worker handles SIGTERM/SIGINT and stops claiming new work while allowing the active call to return before exit.
- The frontend polls `GET /api/research/{job_id}/chat`.
- Production requires the web and worker services to share the same `DATABASE_URL` and provider credentials.
- Do not use `Base.metadata.create_all()` for production schema changes; add and apply Alembic migrations.

## Release Convention

ResearchFlow AI uses Semantic Versioning:

```text
vMAJOR.MINOR.PATCH
```

A release is complete only after CI, clean-checkout validation, migration validation, and deployment smoke checks pass for the exact commit that receives the Git tag.
