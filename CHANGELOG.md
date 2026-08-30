# Changelog

All notable changes to ResearchFlow AI are recorded here. Releases follow Semantic Versioning.

## [Unreleased]

No unreleased changes recorded.

## [1.2.0] - 2026-08-30

### Architecture
- Moved the active application workflow into `backend/app/workflow/` with explicit planner, researcher, analyst, reporter, and orchestrator modules.
- Removed inactive agent adapters, experimental framework runner code, RAG runtime stubs, and empty service modules from the active application tree.
- Kept future framework and RAG concepts documented under `docs/future/` instead of advertising them as runtime capabilities.
- Made the background worker the sole executor of research workflows; the API now persists queued jobs and returns without executing the workflow directly.

### Runtime correctness
- Standardized the research job lifecycle as `queued -> in_progress -> completed|failed`.
- Added the canonical job-state Alembic migration without rewriting the released initial migration.
- Added atomic PostgreSQL worker claims using `FOR UPDATE SKIP LOCKED` and committed claims before slow provider calls.
- Added consistent 404 behavior for missing jobs and parent resources while preserving empty collections for existing jobs without steps or sources.
- Centralized readiness scoring across research and evaluation endpoints.
- Added worker startup, shutdown, claim, execution, completion, and failure logging.
- Added workflow-stage logging for planning, research, analysis, reporting, and terminal outcomes.
- Removed Uvicorn `--reload` from the Compose API runtime.

### Providers and configuration
- Updated the default Gemini model to `gemini-3.6-flash` after the previous model became unavailable to new users.
- Retained the OpenAI-compatible provider path as the configured LLM fallback mechanism.
- Refreshed Compose and example environment defaults for the v1.2.0 runtime.

### Verification and quality
- Added isolated backend runtime, worker, workflow, API-contract, and genuine PostgreSQL concurrency tests.
- Verified the backend suite with 21 passing tests.
- Added frontend tests for initial rendering, local casual replies, and asynchronous research completion; verified 3 passing tests plus lint and production build.
- Verified Docker build, PostgreSQL health, Alembic migrations, API startup, and worker startup locally.
- Verified the failure path from API submission through worker claim and safe failed-state persistence when no usable LLM provider was configured.
- Verified a successful provider-backed end-to-end research job using Gemini and Tavily, including planner, researcher, analyst, reporter, persisted sources, persisted report, and completed terminal state.
- Verified DeepSeek/OpenAI-compatible fallback configuration is visible inside the worker; deliberate runtime failover was not forced because the primary provider was healthy.
- Updated vulnerable transitive frontend dependencies (`js-yaml` and `nanoid`); `npm audit` reports zero known vulnerabilities after the update.

### Release boundary
- v1.2.0 is an architecture and runtime-correctness release, not a feature-expansion release.
- RAG, LangGraph, LangChain, LlamaIndex, OpenAI Agents SDK orchestration, Redis, Celery, Kubernetes, authentication, and distributed tracing remain outside the active v1.2.0 runtime.
- Final release/tag remains gated on verification and CI for the exact release-candidate commit.

### Production hardening still required
- Add API authentication/authorization before exposing private research data to untrusted users.
- Add rate limits and abuse controls for provider-backed endpoints.
- Add metrics, distributed traces, alerting, and broader production observability.
- Add stale-job recovery/retry policy and job-attempt metadata.
- Add production backup/restore and disaster-recovery procedures.

## [1.1.0]
- Production-hardening checkpoint that established Alembic-owned schema evolution, migration-gated Compose startup, asynchronous worker validation, CI coverage, and the release discipline used as the base for v1.2.0.

## [1.0.0]
- Initial standalone ResearchFlow AI release with persisted research jobs, sources, workflow steps, cited reports, async worker processing, and React/Vite UI.
