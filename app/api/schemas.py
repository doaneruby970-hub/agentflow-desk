"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# Ticket Schemas
class TicketCreate(BaseModel):
    """Schema for creating a new ticket."""

    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    source: str = Field(default="api", max_length=50)
    external_id: str | None = Field(default=None, max_length=255)


class TicketResponse(BaseModel):
    """Schema for ticket response."""

    id: UUID
    tenant_id: UUID
    external_id: str | None
    subject: str
    body: str
    source: str
    status: str
    category: str | None
    priority: str | None
    sentiment: str | None
    urgency: int | None
    assigned_team: str | None
    metadata: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    """Schema for paginated ticket list."""

    tickets: list[TicketResponse]
    total: int
    page: int
    page_size: int


# Workflow Schemas
class WorkflowExecutionResponse(BaseModel):
    """Schema for workflow execution response."""

    id: UUID
    ticket_id: UUID
    tenant_id: UUID
    state: str
    error_message: str | None
    retry_count: int
    metadata: dict
    started_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class WorkflowEventResponse(BaseModel):
    """Schema for workflow event response."""

    id: UUID
    execution_id: UUID
    event_type: str
    from_state: str | None
    to_state: str | None
    payload: dict
    timestamp: datetime

    class Config:
        from_attributes = True


# Classification Schemas
class ClassificationResult(BaseModel):
    """Schema for ticket classification result."""

    category: str
    priority: str
    sentiment: str
    urgency: int = Field(..., ge=1, le=10)
    confidence: float = Field(..., ge=0.0, le=1.0)


class DraftReplyResponse(BaseModel):
    """Schema for draft reply response."""

    ticket_id: UUID
    draft: str
    retrieved_context: list[dict]
    confidence: float


# Knowledge Base Schemas
class KnowledgeDocumentCreate(BaseModel):
    """Schema for creating a knowledge document."""

    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    source: str = Field(..., max_length=255)
    tags: list[str] = Field(default_factory=list)


class KnowledgeDocumentResponse(BaseModel):
    """Schema for knowledge document response."""

    id: UUID
    tenant_id: UUID
    title: str
    content: str
    source: str
    tags: list[str]
    metadata: dict
    indexed_at: datetime

    class Config:
        from_attributes = True


class KnowledgeSearchRequest(BaseModel):
    """Schema for knowledge search request."""

    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeSearchResponse(BaseModel):
    """Schema for knowledge search response."""

    documents: list[dict]
    query: str
    took_ms: int


# Metrics Schemas
class MetricsResponse(BaseModel):
    """Schema for system metrics response."""

    total_tickets: int
    tickets_by_status: dict[str, int]
    tickets_by_priority: dict[str, int]
    avg_processing_time_seconds: float
    automation_rate: float
    total_llm_cost_usd: float
