# ResearchFlow AI

Agentic research workflow platform:

```text
Plan -> Search -> Analyze -> Report -> Store
```

This project is the upgrade path after `RAG Knowledge Assistant`. The RAG project proves retrieval QA. ResearchFlow AI proves multi-step research orchestration with stored jobs, sources, steps, and reports.

## Setup
```bash
cp .env.example .env
docker compose up -d --build
open http://127.0.0.1:8000/
open http://127.0.0.1:8000/docs
```

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
- `GET /api/research/{job_id}/summary`
- `GET /api/jobs/`
- `GET /api/reports/{job_id}`
- `POST /api/eval/run`

## Current Release
- `v2`: full AI research platform with standalone UI, Portfolio Ask integration, RAG contracts, eval/observability contracts, OpenAI Agents SDK blueprint, and LangGraph/LlamaIndex/LangChain adapter contracts.

## Version Roadmap
- `v0`: production backend scaffold.
- `v0.1`: basic custom research workflow.
- `v1`: recruiter-ready standalone release.
- `v2`: final platform release combining agent framework readiness, RAG, evals, observability, and portfolio integration.
