# AgentFlow Desk

AgentFlow Desk is a portfolio backend for AI-assisted support workflow automation. It shows how a Python service can receive support tickets, classify them with an LLM, search a knowledge base, generate draft replies, route tickets to teams, and expose operational metrics.

This is a reference project, not a finished SaaS product. It is useful proof for Upwork jobs involving Python backend work, LLM integration, workflow automation, REST APIs, queues, and database-backed systems.

## What It Demonstrates

- FastAPI REST API with typed request and response schemas.
- SQLAlchemy models for tickets, workflow executions, workflow events, knowledge documents, and LLM cost tracking.
- Celery and Redis background tasks for classification, drafting, and routing.
- OpenAI and Anthropic provider abstraction for chat completion.
- Knowledge base indexing and vector-style similarity search.
- PostgreSQL persistence with tenant-aware model structure.
- Docker Compose setup for local API, worker, Redis, and database services.
- Tests for LLM cost estimation and retrieval similarity.

## Core Workflow

```text
Support ticket
    |
    v
FastAPI ticket endpoint
    |
    v
PostgreSQL record + workflow execution
    |
    v
Celery worker
    |
    +--> LLM classification
    +--> Draft reply generation
    +--> Rule-based team routing
    |
    v
Metrics and audit records
```

## API Surface

| Area | Endpoints |
|---|---|
| Tickets | `POST /api/v1/tickets`, `GET /api/v1/tickets`, `GET /api/v1/tickets/{id}` |
| Workflow actions | `POST /api/v1/tickets/{id}/classify`, `POST /api/v1/tickets/{id}/draft-reply`, `POST /api/v1/tickets/{id}/route` |
| Knowledge base | `POST /api/v1/knowledge/index`, `POST /api/v1/knowledge/search`, `GET /api/v1/knowledge/documents` |
| Monitoring | `GET /api/v1/health`, `GET /api/v1/metrics` |

After the app is running, FastAPI docs are available at:

```text
http://localhost:8000/docs
```

## Tech Stack

| Layer | Tools |
|---|---|
| API | Python 3.11, FastAPI, Pydantic |
| Database | PostgreSQL, SQLAlchemy, Alembic |
| Background jobs | Celery, Redis |
| AI integration | OpenAI API, Anthropic API |
| Retrieval | Embeddings plus cosine similarity MVP |
| Delivery | Docker Compose |
| Tests | pytest, pytest-asyncio |

## Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
```

Set one provider key in `.env`:

```bash
OPENAI_API_KEY=your-key
# or
ANTHROPIC_API_KEY=your-key
```

### 2. Run With Docker Compose

```bash
docker-compose up --build
```

### 3. Check the API

```bash
curl http://localhost:8000/api/v1/health
```

### 4. Create a Ticket

```bash
curl -X POST http://localhost:8000/api/v1/tickets \
  -H "Content-Type: application/json" \
  -d "{\"subject\":\"Cannot login\",\"body\":\"Password reset link is not working\",\"source\":\"email\"}"
```

## Project Structure

```text
agentflow-desk/
  app/
    api/          FastAPI routes and schemas
    core/         settings and database setup
    models/       SQLAlchemy tables
    services/     LLM and retrieval services
    workers/      Celery tasks
  alembic/        database migrations
  docs/           design notes
  tests/          focused unit tests
  docker-compose.yml
  pyproject.toml
```

## Current Limitations

- Authentication is represented by a mock tenant ID and is not production-ready.
- The retrieval layer uses Python cosine similarity for the MVP path; a production system should use pgvector queries directly.
- Draft generation currently uses the ticket text directly; full RAG wiring can be expanded.
- The project needs real provider keys and running infrastructure for an end-to-end local demo.

## Why This Matters for Clients

This repository is most relevant for projects that need:

- a Python API around an LLM workflow;
- a background worker pipeline instead of a single blocking script;
- structured database records and operational visibility;
- rule-based routing around AI classification;
- clean handoff documentation for a maintainable MVP.

For proposal-ready wording, see [UPWORK_APPLICATION_MATERIALS.md](UPWORK_APPLICATION_MATERIALS.md).
