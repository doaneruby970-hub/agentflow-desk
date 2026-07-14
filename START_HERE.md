# Start Here

AgentFlow Desk is a portfolio/reference backend for AI-assisted support workflow automation.

## What to Look At First

1. [README.md](README.md) - project overview, setup, API surface, and limitations.
2. [UPWORK_APPLICATION_MATERIALS.md](UPWORK_APPLICATION_MATERIALS.md) - proposal wording and interview talking points.
3. [docs/design.md](docs/design.md) - short technical design notes.
4. [app/api/tickets.py](app/api/tickets.py) - ticket API routes.
5. [app/workers/tasks.py](app/workers/tasks.py) - Celery background workflow tasks.
6. [app/services/llm.py](app/services/llm.py) - OpenAI/Anthropic provider abstraction.

## Local Demo Path

```bash
cp .env.example .env
docker-compose up --build
```

Then open:

```text
http://localhost:8000/docs
```

## Positioning for Clients

Use this repository as proof of Python backend structure, LLM integration, workflow automation, queues, database modeling, and documentation. Be clear that it is a reference MVP and that production hardening would include real authentication, authorization, deployment configuration, and stronger vector search.
