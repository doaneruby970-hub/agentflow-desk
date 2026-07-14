# AgentFlow Desk Design Notes

## Goal

AgentFlow Desk demonstrates a maintainable backend pattern for AI-assisted support workflow automation. The goal is to show how to combine a conventional API, a database, background workers, and LLM calls without turning the whole system into an unpredictable free-form agent.

## Core Components

| Component | Responsibility |
|---|---|
| FastAPI app | Receives HTTP requests, validates input, exposes ticket, knowledge, and metrics routes |
| PostgreSQL | Stores tickets, workflow executions, workflow events, knowledge documents, and LLM request metadata |
| Celery worker | Runs slower classification, draft generation, and routing tasks outside the request path |
| Redis | Broker for Celery background jobs |
| LLM service | Keeps provider-specific OpenAI/Anthropic code away from workflow logic |
| Retrieval service | Indexes documents and ranks relevant knowledge for a query |

## Workflow

```text
Ticket created
    |
    v
Workflow execution created
    |
    v
Classification task queued
    |
    v
LLM classifies category, priority, sentiment, urgency
    |
    v
Draft reply and routing tasks can run
    |
    v
Workflow event records preserve state transitions
```

## Design Choices

### Deterministic Workflow

The system uses explicit states and tasks instead of letting an autonomous agent decide every next step. This keeps behavior easier to debug, test, and explain to a client.

### Background Processing

LLM calls can be slow or fail. Celery moves those calls outside the request path, so the API can accept work quickly and workers can retry failed tasks.

### Provider Abstraction

OpenAI and Anthropic calls are wrapped behind a shared interface. Business logic should not need to know which provider is configured.

### Tenant-Aware Data Model

Core tables include `tenant_id` fields. The current project uses a mock tenant ID for the MVP, but the model shape leaves room for real authentication and tenant extraction.

## Production Hardening Needed

- Real authentication and authorization.
- Rate limiting and tenant extraction.
- Secrets management outside `.env` files.
- Direct pgvector queries for retrieval.
- Stronger end-to-end tests with database and Redis fixtures.
- Deployment-specific configuration, logging, and monitoring.

## Client Project Adaptation

For a real client, start by defining:

- the exact input source, such as form, email, CRM, or helpdesk;
- the workflow states and allowed transitions;
- which actions must be automatic and which need human review;
- the destination systems and data formats;
- failure handling and retry expectations;
- acceptance tests for the first MVP milestone.
