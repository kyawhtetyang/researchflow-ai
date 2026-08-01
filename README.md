# ResearchFlow AI

Agentic research workflow platform:

```text
Plan -> Search -> Analyze -> Report -> Store
```

ResearchFlow AI is the next step after `RAG Knowledge Assistant`. The earlier RAG project proves retrieval QA. ResearchFlow AI proves multi-step research orchestration with stored jobs, sources, workflow steps, and cited reports.

## Current Release
- App/API release: `1.0.0`
- Historical snapshot label: `v3`
- Current stack: FastAPI + PostgreSQL/pgvector + worker + React/Vite frontend
- Live provider path: Gemini with OpenAI-compatible fallback support
- Live search path: Tavily web search

## Setup
```bash
cp .env.example .env
docker compose up -d --build
open http://127.0.0.1:8000/
open http://127.0.0.1:8000/docs
```

## Frontend Development
```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

Notes:
- Vite defaults to port `3001`; if that port is busy it will choose the next available port.
- Local Vite development proxies `/api` to `http://127.0.0.1:8000`.
- FastAPI serves the built Vite app from `frontend/dist/` when that build exists.

## Verify
```bash
docker compose exec -T -e PYTHONPATH=/app api pytest -q
python3 backend/scripts/first_boot_verify.py http://127.0.0.1:8000
```

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
- The frontend polls the chat-shaped endpoint at `GET /api/research/{job_id}/chat`.
- If provider env values change, recreate the API and worker containers so Docker reloads the environment.

## Version Roadmap
- `v0`: production backend scaffold
- `v0.1`: basic custom research workflow
- `v1`: recruiter-ready standalone release
- `v2`: platform-level contracts for evals, adapters, and portfolio integration
- `v3`: implemented research-engine milestone archived as the `1.0.0` historical snapshot label
