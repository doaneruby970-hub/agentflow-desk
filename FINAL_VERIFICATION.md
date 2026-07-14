# Verification Notes

Date: 2026-07-14

## Scope Reviewed

- Public documentation was cleaned up to remove broken encoding and reduce overclaiming.
- The README now positions AgentFlow Desk as a reference MVP instead of a finished production SaaS.
- Upwork proposal wording now uses claims that are easier to defend in client conversations.

## Evidence in the Repository

- `app/api/tickets.py` exposes ticket creation, listing, detail, classification, draft reply, and routing endpoints.
- `app/api/knowledge.py` exposes document indexing and search endpoints.
- `app/api/metrics.py` exposes basic operational metrics.
- `app/services/llm.py` defines OpenAI and Anthropic provider classes behind a common interface.
- `app/services/retrieval.py` implements MVP cosine-similarity retrieval.
- `app/workers/tasks.py` defines Celery tasks for classification, drafting, and routing.
- `tests/` includes focused tests for LLM cost estimation and retrieval similarity.

## Important Limitations

- This is not verified as a live production deployment.
- Authentication is not production-ready; the current MVP uses a mock tenant ID.
- Retrieval should be upgraded to direct pgvector queries for production use.
- End-to-end testing requires local dependencies, database, Redis, and provider keys.
