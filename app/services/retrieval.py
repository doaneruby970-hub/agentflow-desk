"""Knowledge base and retrieval service."""

import time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import KnowledgeDocument
from app.services.llm import llm_service


class RetrievalService:
    """Knowledge base retrieval service using vector similarity."""

    async def index_document(
        self,
        tenant_id: UUID,
        title: str,
        content: str,
        source: str,
        tags: list[str],
        db: AsyncSession,
    ) -> KnowledgeDocument:
        """Index a new document with embedding."""
        # Generate embedding
        embedding = await llm_service.create_embedding(content)

        # Create document
        document = KnowledgeDocument(
            tenant_id=tenant_id,
            title=title,
            content=content,
            source=source,
            tags=tags,
            embedding=embedding,
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        return document

    async def search(
        self,
        query: str,
        tenant_id: UUID,
        top_k: int,
        db: AsyncSession,
    ) -> tuple[list[dict], int]:
        """Search knowledge base using vector similarity."""
        start_time = time.time()

        # Generate query embedding
        query_embedding = await llm_service.create_embedding(query)

        # In production, use pgvector's <=> operator for cosine similarity
        # For MVP, fetch all documents and compute similarity in Python
        result = await db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.tenant_id == tenant_id)
        )
        documents = result.scalars().all()

        # Compute cosine similarity
        scored_docs = []
        for doc in documents:
            if doc.embedding:
                similarity = self._cosine_similarity(query_embedding, doc.embedding)
                scored_docs.append(
                    {
                        "id": str(doc.id),
                        "title": doc.title,
                        "content": doc.content,
                        "source": doc.source,
                        "tags": doc.tags,
                        "score": similarity,
                    }
                )

        # Sort by similarity and return top_k
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        top_docs = scored_docs[:top_k]

        latency_ms = int((time.time() - start_time) * 1000)

        return top_docs, latency_ms

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(y * y for y in b) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)


# Global retrieval service instance
retrieval_service = RetrievalService()
