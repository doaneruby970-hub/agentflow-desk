"""API routes for knowledge base management."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.api.tickets import MOCK_TENANT_ID
from app.core.database import get_db
from app.models.tables import KnowledgeDocument
from app.services.retrieval import retrieval_service

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.post("/index", response_model=KnowledgeDocumentResponse, status_code=201)
async def index_document(
    doc_data: KnowledgeDocumentCreate,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeDocumentResponse:
    """Index a new knowledge document."""
    document = await retrieval_service.index_document(
        tenant_id=MOCK_TENANT_ID,
        title=doc_data.title,
        content=doc_data.content,
        source=doc_data.source,
        tags=doc_data.tags,
        db=db,
    )

    return KnowledgeDocumentResponse.model_validate(document)


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    search_request: KnowledgeSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeSearchResponse:
    """Search knowledge base using semantic similarity."""
    documents, latency_ms = await retrieval_service.search(
        query=search_request.query,
        tenant_id=MOCK_TENANT_ID,
        top_k=search_request.top_k,
        db=db,
    )

    return KnowledgeSearchResponse(
        documents=documents,
        query=search_request.query,
        took_ms=latency_ms,
    )


@router.get("/documents", response_model=list[KnowledgeDocumentResponse])
async def list_documents(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeDocumentResponse]:
    """List all knowledge documents."""
    result = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.tenant_id == MOCK_TENANT_ID)
        .limit(limit)
        .order_by(KnowledgeDocument.indexed_at.desc())
    )
    documents = result.scalars().all()

    return [KnowledgeDocumentResponse.model_validate(doc) for doc in documents]
