# AgentFlow Desk — Technical Design Specification

**Version:** 1.0  
**Date:** 2026-07-08  
**Status:** Draft for Phase 1 (MVP)

---

## 1. Project Overview

### 1.1 Purpose

AgentFlow Desk is a production-grade Python backend for automating support workflows using Large Language Models (LLMs). It provides intelligent ticket classification, knowledge retrieval, response drafting, and routing through deterministic, auditable state machines rather than free-form agent execution.

### 1.2 Target Use Case

Enterprise support teams handling high volumes of customer inquiries via email, web forms, or chat. The system:
- Classifies incoming tickets by category, priority, sentiment, and urgency
- Retrieves relevant knowledge from FAQ, SOP, and historical solutions
- Drafts response suggestions or automated replies
- Routes tickets to appropriate teams
- Maintains full audit trail for compliance and debugging

### 1.3 Design Goals

1. **Deterministic execution** — State machines over emergent agent behavior
2. **Provider independence** — Swap OpenAI/Claude/local models without business logic changes
3. **Production-ready patterns** — Multi-tenancy, observability, error handling, cost tracking
4. **Horizontal scalability** — Stateless API + background workers
5. **Developer experience** — Clear abstractions, comprehensive tests, documented APIs

---

## 2. System Architecture

### 2.1 High-Level Components

```
┌──────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  (Web App, Mobile App, Third-party Integrations, Webhooks)  │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTPS / REST
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                     FastAPI Gateway                          │
│  (Authentication, Rate Limiting, Request Validation)         │
└──┬─────────────┬──────────────┬──────────────┬──────────────┘
   │             │              │              │
   ↓             ↓              ↓              ↓
┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────┐
│Workflow │ │   LLM   │ │Retrieval │ │  Knowledge   │
│ Engine  │ │ Service │ │ Service  │ │   Manager    │
└────┬────┘ └────┬────┘ └────┬─────┘ └──────┬───────┘
     │           │           │              │
     └───────────┴───────────┴──────────────┘
                         ↓
            ┌────────────────────────┐
            │    Celery Workers      │
            │ (Async Task Execution) │
            └───────────┬────────────┘
                        │
       ┌────────────────┼────────────────┐
       ↓                ↓                ↓
┌─────────────┐  ┌────────────┐  ┌────────────┐
│ PostgreSQL  │  │   Redis    │  │  pgvector  │
│ (Business   │  │  (Queue &  │  │  (Vector   │
│  Data)      │  │   Cache)   │  │   Store)   │
└─────────────┘  └────────────┘  └────────────┘
```

### 2.2 Service Responsibilities

#### FastAPI Gateway
- HTTP request handling and routing
- JWT authentication and tenant extraction
- Request validation (Pydantic models)
- Rate limiting (per tenant, per endpoint)
- CORS configuration
- OpenAPI documentation

#### Workflow Engine
- State machine execution (`INGESTED → CLASSIFIED → RETRIEVED → DRAFTED → ROUTED → RESOLVED`)
- Event sourcing for auditability
- Transition validation and error handling
- Workflow pause/resume for human-in-the-loop
- Timeout and retry policies

#### LLM Service
- Unified provider interface (`OpenAIProvider`, `ClaudeProvider`, `LocalProvider`)
- Chat completion with structured output
- Embedding generation
- Automatic retry with exponential backoff
- Fallback to secondary provider on failure
- Token usage and cost tracking

#### Retrieval Service
- Document chunking and embedding
- Vector search via pgvector or ChromaDB
- MMR (Maximal Marginal Relevance) re-ranking
- Hybrid retrieval (dense + sparse BM25)
- Query rewriting and expansion

#### Knowledge Manager
- Document ingestion from files, URLs, APIs
- Metadata extraction and tagging
- Incremental index updates
- Deduplication and versioning

---

## 3. Data Model

### 3.1 Core Entities

#### Ticket
```python
class Ticket:
    id: UUID
    tenant_id: UUID
    external_id: str | None  # Client's ticket ID
    subject: str
    body: str
    source: str  # email | web | chat | api
    status: TicketStatus
    category: str | None
    priority: Priority | None
    sentiment: Sentiment | None
    urgency: int | None  # 1-10 scale
    assigned_team: str | None
    created_at: datetime
    updated_at: datetime
```

#### WorkflowExecution
```python
class WorkflowExecution:
    id: UUID
    ticket_id: UUID
    tenant_id: UUID
    state: WorkflowState
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None
    retry_count: int
```

#### WorkflowEvent
```python
class WorkflowEvent:
    id: UUID
    execution_id: UUID
    event_type: str  # state_entered | action_executed | transition_failed
    from_state: str | None
    to_state: str | None
    payload: dict  # JSON metadata
    timestamp: datetime
```

#### KnowledgeDocument
```python
class KnowledgeDocument:
    id: UUID
    tenant_id: UUID
    title: str
    content: str
    source: str
    tags: list[str]
    embedding: list[float] | None
    indexed_at: datetime
```

#### LLMRequest
```python
class LLMRequest:
    id: UUID
    tenant_id: UUID
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    latency_ms: int
    created_at: datetime
```

### 3.2 Database Schema Design

**Principles:**
- Every table includes `tenant_id` for multi-tenancy
- Use UUIDs for primary keys (distributed-friendly)
- Timestamps: `created_at`, `updated_at` on mutable entities
- JSON columns for flexible metadata
- Indexes on foreign keys and query columns

**Key Indexes:**
- `tickets(tenant_id, status, created_at)` — List active tickets
- `tickets(tenant_id, category)` — Filter by category
- `workflow_events(execution_id, timestamp)` — Replay event log
- `knowledge_documents(tenant_id)` + GIN index on tags

---

## 4. LLM Integration Layer

### 4.1 Provider Abstraction

```python
class LLMProvider(ABC):
    @abstractmethod
    async def chat_completion(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> LLMResponse:
        """Generate chat completion."""

    @abstractmethod
    async def create_embedding(
        self,
        text: str,
        model: str,
    ) -> list[float]:
        """Generate text embedding."""

    @abstractmethod
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
    ) -> float:
        """Estimate cost in USD."""
```

### 4.2 Implemented Providers

#### OpenAIProvider
- Uses `openai` Python SDK
- Supports GPT-4o, GPT-4o-mini, o1-preview, o1-mini
- Embeddings via `text-embedding-3-small` / `text-embedding-3-large`
- Automatic retry on rate limit (429) with exponential backoff

#### ClaudeProvider
- Uses `anthropic` Python SDK
- Supports Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
- Prompt caching for system instructions
- Structured output via tool use

#### LocalProvider
- Wrapper for Ollama / vLLM / HuggingFace Inference
- Configurable base URL
- No cost tracking (free inference)

### 4.3 LLM Service Usage Patterns

**Classification Task:**
```python
messages = [
    {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
    {"role": "user", "content": f"Ticket: {ticket.subject}\n\n{ticket.body}"},
]

response = await llm_service.chat_completion(
    messages=messages,
    model="gpt-4o-mini",
    temperature=0.3,
    response_format={"type": "json_object"},
)

classification = json.loads(response.content)
# {"category": "billing", "priority": "high", "sentiment": "frustrated", "urgency": 8}
```

**Draft Reply Task:**
```python
context = await retrieval_service.search(ticket.body, top_k=3)

messages = [
    {"role": "system", "content": REPLY_SYSTEM_PROMPT},
    {"role": "user", "content": f"Ticket: {ticket.body}\n\nContext:\n{context}"},
]

response = await llm_service.chat_completion(
    messages=messages,
    model="claude-3-5-sonnet-20241022",
    temperature=0.7,
)

draft = response.content
```

---

## 5. Workflow Engine Design

### 5.1 State Machine Definition

```python
class WorkflowState(str, Enum):
    INGESTED = "ingested"
    CLASSIFIED = "classified"
    RETRIEVED = "retrieved"
    DRAFTED = "drafted"
    ROUTED = "routed"
    HUMAN_REVIEW = "human_review"
    RESOLVED = "resolved"
    FAILED = "failed"

TRANSITIONS = {
    WorkflowState.INGESTED: [WorkflowState.CLASSIFIED, WorkflowState.FAILED],
    WorkflowState.CLASSIFIED: [WorkflowState.RETRIEVED, WorkflowState.FAILED],
    WorkflowState.RETRIEVED: [WorkflowState.DRAFTED, WorkflowState.FAILED],
    WorkflowState.DRAFTED: [WorkflowState.ROUTED, WorkflowState.HUMAN_REVIEW, WorkflowState.FAILED],
    WorkflowState.ROUTED: [WorkflowState.RESOLVED, WorkflowState.HUMAN_REVIEW],
    WorkflowState.HUMAN_REVIEW: [WorkflowState.RESOLVED, WorkflowState.DRAFTED],
    WorkflowState.RESOLVED: [],
    WorkflowState.FAILED: [],
}
```

### 5.2 Execution Flow

1. **INGESTED** → **CLASSIFIED**
   - Celery task: `classify_ticket(ticket_id)`
   - LLM extracts: category, priority, sentiment, urgency
   - Confidence score recorded
   - If confidence < threshold → route to HUMAN_REVIEW

2. **CLASSIFIED** → **RETRIEVED**
   - Celery task: `retrieve_knowledge(ticket_id)`
   - Query pgvector with ticket body embedding
   - Return top-k documents
   - Store retrieved context in workflow metadata

3. **RETRIEVED** → **DRAFTED**
   - Celery task: `draft_reply(ticket_id)`
   - LLM generates response using ticket + retrieved context
   - Optionally check for PII and redact
   - Store draft in ticket metadata

4. **DRAFTED** → **ROUTED**
   - Rule engine assigns team based on category
   - Optional: LLM-powered routing for ambiguous cases
   - Update `ticket.assigned_team`

5. **ROUTED** → **RESOLVED** or **HUMAN_REVIEW**
   - If auto-reply enabled and confidence high → send draft, mark RESOLVED
   - Otherwise → assign to human agent for review

### 5.3 Event Sourcing

Every state transition emits a `WorkflowEvent`:
```python
{
    "event_type": "state_entered",
    "from_state": "classified",
    "to_state": "retrieved",
    "payload": {
        "documents_retrieved": 3,
        "retrieval_latency_ms": 120,
        "top_score": 0.87,
    },
    "timestamp": "2026-07-08T14:32:01.123Z",
}
```

Events enable:
- Full audit trail for compliance
- Replay for debugging
- Metrics and analytics
- Workflow visualization

---

## 6. Retrieval Service (RAG)

### 6.1 Vector Store Options

**pgvector (Production Default)**
- PostgreSQL extension for vector similarity search
- Stores embeddings directly in `knowledge_documents` table
- Supports HNSW and IVFFlat indexes
- Co-locates vectors with metadata (single query)

**ChromaDB (Development Alternative)**
- Lightweight embedded vector database
- Fast local setup, no infrastructure
- Sufficient for MVP and testing
- Easy migration path to pgvector

### 6.2 Retrieval Pipeline

1. **Query Processing**
   - Clean and normalize query text
   - Optional: LLM query rewriting for better recall
   - Generate query embedding

2. **Vector Search**
   - Cosine similarity search in pgvector
   - Return top-k candidates (k=10-20)

3. **Re-ranking**
   - MMR to reduce redundancy
   - Optional: Cross-encoder re-ranker
   - Filter by metadata (tenant_id, tags, date range)

4. **Context Assembly**
   - Format retrieved documents
   - Truncate to fit LLM context window
   - Include metadata (source, title, confidence)

### 6.3 Indexing Strategy

**Chunking:**
- Max chunk size: 512 tokens
- Overlap: 50 tokens
- Preserve sentence boundaries

**Batch Processing:**
- Celery task: `index_documents(document_ids)`
- Batch embed up to 100 chunks per LLM call
- Store embeddings in single transaction

**Incremental Updates:**
- Mark documents as `needs_reindex` on edit
- Nightly task re-embeds modified documents

---

## 7. API Design

### 7.1 REST Principles

- **Resource-oriented URLs** — `/tickets/{id}`, not `/getTicket`
- **HTTP verbs** — GET (read), POST (create), PUT/PATCH (update), DELETE
- **Status codes** — 200 (OK), 201 (Created), 202 (Accepted), 400 (Bad Request), 401 (Unauthorized), 404 (Not Found), 500 (Server Error)
- **Pagination** — Cursor-based for large collections
- **Versioning** — `/api/v1/` prefix

### 7.2 Authentication & Authorization

**JWT-based authentication:**
- Client obtains token from auth service (not in scope of this project)
- Token includes `tenant_id` and `user_id` claims
- FastAPI dependency extracts and validates token on every request

**Tenant Isolation:**
```python
async def get_current_tenant(token: str = Depends(oauth2_scheme)) -> Tenant:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    tenant_id = payload["tenant_id"]
    tenant = await tenant_repo.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=401)
    return tenant
```

All database queries filtered by `tenant_id`:
```python
tickets = await session.execute(
    select(Ticket).where(
        Ticket.tenant_id == tenant.id,
        Ticket.status == "open",
    )
)
```

### 7.3 Rate Limiting

**Strategy:** Token bucket per tenant
- 100 requests/minute for standard tier
- 1000 requests/minute for premium tier
- Enforced via Redis-backed middleware

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 73
X-RateLimit-Reset: 1720451523
```

### 7.4 Error Handling

**Consistent error response format:**
```json
{
  "error": {
    "code": "TICKET_NOT_FOUND",
    "message": "Ticket with id a3c7f8b2 not found",
    "details": null
  }
}
```

**Error codes:**
- `VALIDATION_ERROR` — Invalid request data
- `NOT_FOUND` — Resource does not exist
- `UNAUTHORIZED` — Missing or invalid token
- `RATE_LIMIT_EXCEEDED` — Too many requests
- `LLM_PROVIDER_ERROR` — Upstream LLM API failure
- `WORKFLOW_TRANSITION_ERROR` — Invalid state transition

---

## 8. Asynchronous Processing

### 8.1 Celery Architecture

**Broker:** Redis (task queue)  
**Result Backend:** Redis (task results, optional)  
**Worker Pool:** `prefork` (multiple processes) or `gevent` (coroutines)

**Task Definition:**
```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def classify_ticket(self, ticket_id: str):
    try:
        ticket = ticket_repo.get(ticket_id)
        classification = llm_service.classify(ticket)
        ticket_repo.update(ticket_id, classification)
        workflow_engine.transition(ticket_id, WorkflowState.CLASSIFIED)
    except LLMProviderError as exc:
        raise self.retry(exc=exc)
```

### 8.2 Task Priorities

**High priority** (routed to dedicated queue `high`):
- Urgent tickets (urgency >= 8)
- VIP customer tickets

**Normal priority** (default queue):
- Standard ticket processing

**Low priority** (queue `low`):
- Batch indexing
- Nightly maintenance tasks

### 8.3 Observability

**Task Monitoring:**
- Celery Flower dashboard (task status, worker health)
- Prometheus metrics (task count, latency, failure rate)
- Sentry error tracking

**Logging:**
- Structured JSON logs
- Correlation ID traces request → worker task → LLM call
- CloudWatch Logs (AWS) or ELK stack

---

## 9. Testing Strategy

### 9.1 Test Pyramid

**Unit Tests (70%)**
- Pure functions (LLM response parsing, state transitions)
- Repository methods (mocked database)
- Service logic (mocked LLM provider)

**Integration Tests (25%)**
- API endpoints with test database
- Celery tasks with test Redis
- Vector search with in-memory ChromaDB

**E2E Tests (5%)**
- Full workflow from ticket ingestion to resolution
- Real LLM provider (expensive, run sparingly)

### 9.2 Test Fixtures

**Factories:**
```python
@pytest.fixture
def sample_ticket():
    return Ticket(
        id=uuid4(),
        tenant_id=TEST_TENANT_ID,
        subject="Cannot log in to my account",
        body="I've tried resetting my password but the link doesn't work.",
        source="email",
        status=TicketStatus.OPEN,
    )
```

**Mocks:**
```python
@pytest.fixture
def mock_llm_provider(mocker):
    provider = mocker.Mock(spec=LLMProvider)
    provider.chat_completion.return_value = LLMResponse(
        content='{"category": "account_access", "priority": "high"}',
        prompt_tokens=100,
        completion_tokens=20,
    )
    return provider
```

### 9.3 Coverage Target

- Minimum 80% line coverage
- 100% coverage for critical paths (workflow engine, authentication)
- Generate HTML report: `pytest --cov=app --cov-report=html`

---

## 10. Deployment Architecture

### 10.1 Local Development

**Docker Compose stack:**
- `db`: PostgreSQL 15 with pgvector extension
- `redis`: Redis 7 for Celery
- `api`: FastAPI application (hot reload)
- `worker`: Celery worker (auto-restart)

**Run:**
```bash
docker-compose up --build
```

### 10.2 Production (AWS ECS Fargate)

**Services:**
- **API Service** — ECS tasks behind Application Load Balancer
  - Auto-scaling: 2-10 tasks based on CPU/memory
  - Health check: `GET /api/v1/health`

- **Worker Service** — ECS tasks (no load balancer)
  - Auto-scaling: 1-5 tasks based on Celery queue depth
  - Graceful shutdown: `SIGTERM` drains active tasks

**Data Layer:**
- **RDS PostgreSQL** — Multi-AZ deployment, automated backups
- **ElastiCache Redis** — Replication group for HA
- **S3** — Attachment storage, audit log archives

**Networking:**
- VPC with public/private subnets
- API in public subnets (ALB)
- Workers, RDS, Redis in private subnets
- NAT Gateway for outbound (LLM API calls)

**CI/CD:**
- GitHub Actions workflow on push to `main`
- Build Docker image → Push to ECR → Deploy to ECS
- Blue/Green deployment via CodeDeploy

### 10.3 Scaling Considerations

**Horizontal Scaling:**
- API: Stateless, scale tasks freely
- Workers: Scale based on queue backlog

**Database Scaling:**
- Read replicas for analytics queries
- Connection pooling (SQLAlchemy + PgBouncer)

**Cost Optimization:**
- Use Fargate Spot for workers (70% cost savings)
- Cache frequent queries in Redis
- Batch LLM calls (classify 10 tickets in single prompt)

---

## 11. Security Considerations

### 11.1 Secrets Management

- Store API keys in AWS Secrets Manager or environment variables
- Never commit secrets to Git
- Rotate secrets quarterly
- Use IAM roles for AWS service access (no hardcoded credentials)

### 11.2 Data Privacy

**PII Handling:**
- Redact PII before logging (emails, phone numbers, SSNs)
- Option to disable LLM processing for sensitive tickets
- Encrypt PII fields at rest (database-level encryption)

**Audit Requirements:**
- Log all data access with user ID and timestamp
- Retain audit logs for 7 years (configurable)
- Support GDPR data export and deletion

### 11.3 Network Security

- HTTPS only (TLS 1.2+)
- API key rotation every 90 days
- IP allowlisting for admin endpoints
- WAF rules to block common attacks (SQL injection, XSS)

---

## 12. Monitoring & Observability

### 12.1 Metrics

**Application Metrics:**
- API request rate, latency (p50, p95, p99), error rate
- Celery task throughput, queue depth, task latency
- LLM call count, tokens used, cost per tenant
- Workflow completion rate, average processing time

**Infrastructure Metrics:**
- ECS CPU/memory utilization
- RDS connections, query latency
- Redis memory usage, eviction rate

**Collection:** Prometheus + Grafana or CloudWatch

### 12.2 Logging

**Log Levels:**
- DEBUG: Detailed traces (dev only)
- INFO: Normal operations (ticket created, workflow transition)
- WARNING: Recoverable errors (retry, fallback)
- ERROR: Unrecoverable failures (task crash, DB timeout)

**Log Format:** JSON with correlation ID
```json
{
  "timestamp": "2026-07-08T14:32:01.123Z",
  "level": "INFO",
  "correlation_id": "a3c7f8b2",
  "service": "worker",
  "message": "Ticket classified successfully",
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "category": "billing",
  "latency_ms": 340
}
```

### 12.3 Alerting

**Critical Alerts (PagerDuty):**
- API error rate > 5%
- Worker queue depth > 1000 for > 5 minutes
- Database connection pool exhausted

**Warning Alerts (Slack):**
- LLM provider failure (fallback used)
- Workflow failure rate > 2%
- Cost spike (daily spend > $500)

---

## 13. Open Questions & Future Work

### 13.1 Phase 1 (MVP) Scope

**In Scope:**
- Core API endpoints (ticket CRUD, classification, drafting)
- Single LLM provider (OpenAI)
- Simple vector store (ChromaDB for dev, pgvector for prod)
- Basic workflow engine (fixed state machine)
- Docker Compose local environment

**Deferred to Phase 2:**
- Multi-provider fallback
- Advanced retrieval (hybrid search, re-ranking)
- Multi-agent orchestration
- Real-time webhooks
- Admin dashboard UI

### 13.2 Technical Debt & Risks

**Risks:**
- LLM API rate limits during traffic spikes → Mitigation: Circuit breaker, request queuing
- Vector search accuracy on diverse knowledge base → Mitigation: Hybrid retrieval, fine-tune embeddings
- State machine rigidity for complex workflows → Mitigation: Parameterized transitions, sub-workflows

**Technical Debt:**
- No integration tests for Celery tasks (deferred to Phase 2)
- Placeholder authentication (real OAuth2 in production)
- Manual database schema migrations (automate with Alembic CI check)

---

## 14. Success Metrics

### 14.1 Technical KPIs

- **API Availability:** > 99.9%
- **P95 Latency:** < 500ms (ticket creation), < 5s (classification)
- **Test Coverage:** > 80%
- **Deployment Frequency:** Daily (via CI/CD)

### 14.2 Business KPIs

- **Automation Rate:** % of tickets resolved without human intervention
- **Classification Accuracy:** % of tickets correctly categorized (validated by human review)
- **Response Time:** Time from ticket creation to draft reply ready
- **Cost Efficiency:** Cost per ticket processed (LLM + infra)

---

## 15. Appendix

### 15.1 Technology Alternatives Considered

| Category | Chosen | Alternatives Considered | Rationale |
|----------|--------|-------------------------|-----------|
| API Framework | FastAPI | Flask, Django REST | Async support, auto-docs, Pydantic validation |
| Task Queue | Celery | Dramatiq, RQ | Mature, wide adoption, feature-rich |
| Vector Store | pgvector | Pinecone, Weaviate, Qdrant | Co-location with relational data, cost |
| LLM Framework | Custom abstraction | LangChain, LlamaIndex | Simplicity, no over-abstraction |
| Deployment | ECS Fargate | EKS, Lambda | Balance of control and managed services |

### 15.2 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html#best-practices)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)

---

**End of Design Specification**
