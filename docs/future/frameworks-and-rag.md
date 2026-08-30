# Future Framework and RAG Roadmap

ResearchFlow v1.2 keeps the runtime source tree limited to capabilities that actually execute in production.

The following ideas are intentionally not runtime features in v1.2:

- OpenAI Agents SDK orchestration
- LangGraph workflow adapters
- LangChain workflow adapters
- LlamaIndex adapters
- embedding pipelines
- document indexing
- vector retrieval / RAG
- distributed tracing integrations

These may be added in a future release only when they have a real execution path, configuration, tests, and documented operational behavior.

## Admission rule

A future capability should move into `backend/app/` only when all of the following are true:

1. It is called by the running application.
2. It has a clear configuration contract.
3. It has unit or integration coverage.
4. The `/api/capabilities` endpoint can truthfully describe it as active.
5. Its failure behavior is defined.

Until then, roadmap concepts belong in documentation rather than production source packages.
