# Upwork Application Materials

Project: AgentFlow Desk  
GitHub: https://github.com/doaneruby970-hub/agentflow-desk

## Best Use

Use this project when applying for jobs involving:

- Python backend APIs;
- LLM integration;
- workflow automation;
- support ticket automation;
- Celery, Redis, PostgreSQL, or Docker;
- AI-assisted classification, routing, or draft generation.

Do not present it as a completed commercial SaaS product. Present it as a reference backend/MVP that proves you can structure the same kind of system for a client.

## Short Proposal Paragraph

I have a related public project called AgentFlow Desk:
https://github.com/doaneruby970-hub/agentflow-desk

It is a Python FastAPI backend for AI-assisted support workflow automation. It includes ticket intake, LLM-based classification, draft reply generation, rule-based routing, PostgreSQL models, Celery/Redis background tasks, Docker Compose setup, and focused tests. The business case may differ from your project, but the engineering pattern is relevant: reliable API endpoints, background processing, structured records, LLM integration, and clear handoff documentation.

## Longer Proposal Template

Hello,

I can help build this as a focused Python backend/workflow automation project rather than an overcomplicated AI platform.

A relevant public project is AgentFlow Desk:
https://github.com/doaneruby970-hub/agentflow-desk

It demonstrates a FastAPI backend with LLM integration, Celery/Redis background jobs, PostgreSQL models, ticket classification, draft generation, rule-based routing, metrics endpoints, Docker Compose setup, and tests. I would use the same practical structure for your project: clear inputs, predictable processing steps, structured outputs, retries/error visibility where needed, and documentation that makes the system easy to hand off.

For your project I would start with a small working MVP first, then expand after you approve the behavior and output format.

Best,  
Yingqiang

## Interview Talking Points

- "I used a deterministic workflow instead of a free-form agent because business automation needs predictable states and easier debugging."
- "The API returns quickly while Celery handles heavier LLM work in the background."
- "The LLM provider layer keeps OpenAI and Anthropic integration separate from business logic."
- "The database tracks tickets, workflow state, events, knowledge documents, and LLM request cost fields."
- "This is an MVP/reference backend, so I would still add production authentication, stronger pgvector queries, and deployment hardening for a client system."

## Resume Project Entry

AgentFlow Desk - AI-assisted support workflow backend  
Built a Python FastAPI reference backend for support ticket automation with LLM-based classification, draft reply generation, rule-based routing, PostgreSQL models, Celery/Redis background tasks, Docker Compose setup, and focused pytest coverage. Designed the workflow around auditable states and structured records instead of free-form agent execution.

Tech: Python, FastAPI, PostgreSQL, SQLAlchemy, Celery, Redis, OpenAI API, Anthropic API, Docker, pytest.

## Claims to Avoid

- Do not say it is running in production unless it really is.
- Do not say it has complete authentication; it uses a mock tenant ID.
- Do not say retrieval is full production pgvector; the MVP path computes similarity in Python.
- Do not say it proves direct experience with a client's exact CRM, helpdesk, or automation tool unless that tool is actually integrated.
