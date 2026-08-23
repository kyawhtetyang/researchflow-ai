# Changelog

All notable changes to ResearchFlow AI are recorded here. Releases follow Semantic Versioning.

## [Unreleased]

### Changed
- Centralized application version metadata for the `1.1.0` hardening line.
- Made Alembic migrations authoritative for schema creation and evolution.
- Added migration-gated Docker Compose startup for the API and worker.
- Added database row locking when workers claim queued jobs.
- Added graceful worker shutdown handling.
- Added CI for migrations, backend tests, frontend checks, production Docker builds, Compose builds, and Compose migration execution.
- Expanded Render Blueprint to include a dedicated background worker.
- Updated first-boot verification to exercise the asynchronous worker path.
- Removed the historical `v3` snapshot label from runtime release metadata.

### Validation status
- GitHub CI passed on the pre-final hardening commit.
- Clean-checkout Docker validation passed locally on Apple Silicon.
- PostgreSQL health, Alembic migration, API startup, worker startup, and `/health` version `1.1.0` were validated locally.
- Async job submission, queue persistence, worker claim, execution attempt, and failed-state persistence were validated without provider credentials.
- Provider-backed completed research flow remains unverified because no local provider credentials were available.
- Production deployment and rollback validation remain required before tagging `v1.1.0`.

### Production hardening still required
- Add API authentication/authorization before exposing private research data to untrusted users.
- Add rate limits and abuse controls for provider-backed endpoints.
- Add structured logs, metrics, traces, and alerting.
- Add stale-job recovery/retry policy and job-attempt metadata.
- Add production backup/restore and disaster-recovery procedures.
- Pin and routinely audit runtime dependencies.

## [1.0.0]
- Initial standalone ResearchFlow AI release with persisted research jobs, sources, workflow steps, cited reports, async worker processing, and React/Vite UI.
