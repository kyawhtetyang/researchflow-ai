# Changelog

All notable changes to ResearchFlow AI are recorded here. Releases follow Semantic Versioning.

## [Unreleased]

### Changed
- Centralized application version metadata for the `1.1.0` hardening line.
- Made Alembic migrations authoritative for schema creation and evolution.
- Added database row locking when workers claim queued jobs.
- Added graceful worker shutdown handling.
- Added CI for migrations, backend tests, frontend checks, and Docker builds.
- Expanded Render Blueprint to include the background worker.
- Removed the historical `v3` snapshot label from runtime release metadata.

### Production hardening still required
- Add API authentication/authorization before exposing private research data to untrusted users.
- Add rate limits and abuse controls for provider-backed endpoints.
- Add structured logs, metrics, traces, and alerting.
- Add stale-job recovery/retry policy and job-attempt metadata.
- Add production backup/restore and disaster-recovery procedures.
- Pin and routinely audit runtime dependencies.
- Complete clean-checkout, deployment, and rollback validation before tagging `v1.1.0`.

## [1.0.0]
- Initial standalone ResearchFlow AI release with persisted research jobs, sources, workflow steps, cited reports, async worker processing, and React/Vite UI.
