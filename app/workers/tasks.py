"""Celery worker tasks."""

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.tables import Ticket, WorkflowExecution, WorkflowEvent, WorkflowState
from app.services.llm import llm_service
from app.workers.celery_app import celery_app

# Create async engine for workers
engine = create_async_engine(settings.database_url)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


CLASSIFICATION_PROMPT = """You are a support ticket classifier. Analyze the following ticket and provide classification.

Ticket Subject: {subject}
Ticket Body: {body}

Respond in JSON format with:
- category: string (one of: billing, technical_issue, account_access, feature_request, refund, other)
- priority: string (one of: low, medium, high, urgent)
- sentiment: string (one of: positive, neutral, negative, frustrated)
- urgency: integer (1-10 scale)
- confidence: float (0.0-1.0)

Only output valid JSON, no other text."""


@celery_app.task(bind=True, max_retries=3)
def classify_ticket(self, ticket_id: str):
    """Classify a support ticket using LLM."""
    import asyncio
    return asyncio.run(_classify_ticket_async(UUID(ticket_id)))


async def _classify_ticket_async(ticket_id: UUID):
    """Async implementation of ticket classification."""
    async with AsyncSessionLocal() as session:
        # Fetch ticket
        result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()

        if not ticket:
            return {"error": "Ticket not found"}

        # Fetch workflow execution
        wf_result = await session.execute(
            select(WorkflowExecution).where(WorkflowExecution.ticket_id == ticket_id)
        )
        workflow = wf_result.scalar_one_or_none()

        try:
            # Call LLM
            messages = [
                {"role": "system", "content": "You are a support ticket classifier."},
                {
                    "role": "user",
                    "content": CLASSIFICATION_PROMPT.format(
                        subject=ticket.subject,
                        body=ticket.body,
                    ),
                },
            ]

            response = await llm_service.chat_completion(
                messages=messages,
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            # Parse classification
            classification = json.loads(response.content)

            # Update ticket
            ticket.category = classification["category"]
            ticket.priority = classification["priority"]
            ticket.sentiment = classification["sentiment"]
            ticket.urgency = classification["urgency"]
            ticket.metadata["classification"] = classification

            # Update workflow
            if workflow:
                workflow.state = WorkflowState.CLASSIFIED
                workflow.metadata["classification_response"] = {
                    "confidence": classification.get("confidence", 0.0),
                    "tokens": response.prompt_tokens + response.completion_tokens,
                }

                # Log event
                event = WorkflowEvent(
                    execution_id=workflow.id,
                    event_type="state_entered",
                    from_state=WorkflowState.INGESTED,
                    to_state=WorkflowState.CLASSIFIED,
                    payload={
                        "classification": classification,
                        "latency_ms": response.latency_ms,
                    },
                )
                session.add(event)

            await session.commit()

            return {
                "ticket_id": str(ticket_id),
                "classification": classification,
                "status": "success",
            }

        except Exception as e:
            if workflow:
                workflow.state = WorkflowState.FAILED
                workflow.error_message = str(e)
                workflow.retry_count += 1
                await session.commit()
            raise


@celery_app.task(bind=True, max_retries=3)
def draft_reply(self, ticket_id: str):
    """Generate draft reply for a ticket."""
    import asyncio
    return asyncio.run(_draft_reply_async(UUID(ticket_id)))


async def _draft_reply_async(ticket_id: UUID):
    """Async implementation of draft reply generation."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()

        if not ticket:
            return {"error": "Ticket not found"}

        wf_result = await session.execute(
            select(WorkflowExecution).where(WorkflowExecution.ticket_id == ticket_id)
        )
        workflow = wf_result.scalar_one_or_none()

        try:
            # Simple draft generation (no RAG for MVP)
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful customer support agent. Generate a professional, empathetic response.",
                },
                {
                    "role": "user",
                    "content": f"Customer inquiry:\nSubject: {ticket.subject}\n\n{ticket.body}\n\nGenerate a helpful response.",
                },
            ]

            response = await llm_service.chat_completion(messages=messages, temperature=0.7)

            draft = response.content

            # Update ticket metadata
            ticket.metadata["draft_reply"] = draft

            # Update workflow
            if workflow:
                workflow.state = WorkflowState.DRAFTED
                workflow.metadata["draft_generated"] = True

                event = WorkflowEvent(
                    execution_id=workflow.id,
                    event_type="state_entered",
                    from_state=WorkflowState.RETRIEVED,
                    to_state=WorkflowState.DRAFTED,
                    payload={"draft_length": len(draft), "latency_ms": response.latency_ms},
                )
                session.add(event)

            await session.commit()

            return {
                "ticket_id": str(ticket_id),
                "draft": draft,
                "status": "success",
            }

        except Exception as e:
            if workflow:
                workflow.state = WorkflowState.FAILED
                workflow.error_message = str(e)
                await session.commit()
            raise


@celery_app.task(bind=True, max_retries=3)
def route_ticket(self, ticket_id: str):
    """Route ticket to appropriate team based on classification."""
    import asyncio
    return asyncio.run(_route_ticket_async(UUID(ticket_id)))


async def _route_ticket_async(ticket_id: UUID):
    """Async implementation of ticket routing."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()

        if not ticket:
            return {"error": "Ticket not found"}

        wf_result = await session.execute(
            select(WorkflowExecution).where(WorkflowExecution.ticket_id == ticket_id)
        )
        workflow = wf_result.scalar_one_or_none()

        # Simple rule-based routing
        routing_map = {
            "billing": "billing-team",
            "technical_issue": "tech-support",
            "account_access": "account-team",
            "feature_request": "product-team",
            "refund": "billing-team",
            "other": "general-support",
        }

        team = routing_map.get(ticket.category or "other", "general-support")
        ticket.assigned_team = team

        # Update workflow
        if workflow:
            workflow.state = WorkflowState.ROUTED
            workflow.metadata["assigned_team"] = team

            event = WorkflowEvent(
                execution_id=workflow.id,
                event_type="state_entered",
                from_state=WorkflowState.DRAFTED,
                to_state=WorkflowState.ROUTED,
                payload={"team": team},
            )
            session.add(event)

        await session.commit()

        return {
            "ticket_id": str(ticket_id),
            "assigned_team": team,
            "status": "success",
        }
