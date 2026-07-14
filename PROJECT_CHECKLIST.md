# Project Checklist

## Implemented

- [x] FastAPI application entry point.
- [x] Ticket create, list, detail, classify, draft reply, and route endpoints.
- [x] Knowledge document indexing and search endpoints.
- [x] Metrics and health endpoints.
- [x] SQLAlchemy models for tickets, workflows, events, knowledge documents, and LLM requests.
- [x] OpenAI and Anthropic provider classes.
- [x] Celery worker tasks for classification, draft generation, and routing.
- [x] Docker Compose configuration.
- [x] Alembic scaffolding.
- [x] Focused tests for LLM cost estimation and retrieval similarity.
- [x] Upwork-oriented application notes.

## Known Gaps

- [ ] Replace mock tenant ID with real authentication and tenant extraction.
- [ ] Add authorization and rate limiting.
- [ ] Use pgvector database operators for production retrieval.
- [ ] Wire retrieved knowledge into draft generation.
- [ ] Add end-to-end API tests with a test database.
- [ ] Add CI status badge after confirming workflow runs.
- [ ] Add deployment-specific configuration for a chosen hosting target.

## Client Handoff Notes

This project is best described as a working reference MVP. For client work, the first milestone should define the exact workflow states, input sources, integrations, data retention needs, and acceptance tests before expanding the feature set.
