"""API routes for system metrics and monitoring."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import MetricsResponse
from app.api.tickets import MOCK_TENANT_ID
from app.core.database import get_db
from app.models.tables import LLMRequest, Ticket, WorkflowExecution

router = APIRouter(prefix="/api/v1", tags=["metrics"])


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    db: AsyncSession = Depends(get_db),
) -> MetricsResponse:
    """Get system metrics and statistics."""
    # Total tickets
    total_result = await db.execute(
        select(func.count(Ticket.id)).where(Ticket.tenant_id == MOCK_TENANT_ID)
    )
    total_tickets = total_result.scalar() or 0

    # Tickets by status
    status_result = await db.execute(
        select(Ticket.status, func.count(Ticket.id))
        .where(Ticket.tenant_id == MOCK_TENANT_ID)
        .group_by(Ticket.status)
    )
    tickets_by_status = {status: count for status, count in status_result.all()}

    # Tickets by priority
    priority_result = await db.execute(
        select(Ticket.priority, func.count(Ticket.id))
        .where(Ticket.tenant_id == MOCK_TENANT_ID, Ticket.priority.isnot(None))
        .group_by(Ticket.priority)
    )
    tickets_by_priority = {priority: count for priority, count in priority_result.all()}

    # Average processing time (completed workflows)
    completed_workflows = await db.execute(
        select(WorkflowExecution).where(
            WorkflowExecution.tenant_id == MOCK_TENANT_ID,
            WorkflowExecution.completed_at.isnot(None),
        )
    )
    workflows = completed_workflows.scalars().all()

    if workflows:
        processing_times = [
            (wf.completed_at - wf.started_at).total_seconds()
            for wf in workflows
            if wf.completed_at
        ]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
    else:
        avg_processing_time = 0.0

    # Automation rate (resolved without human review)
    resolved_result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.tenant_id == MOCK_TENANT_ID,
            Ticket.status == "resolved",
        )
    )
    resolved_count = resolved_result.scalar() or 0
    automation_rate = (resolved_count / total_tickets * 100) if total_tickets > 0 else 0.0

    # Total LLM cost (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    cost_result = await db.execute(
        select(func.sum(LLMRequest.cost_usd)).where(
            LLMRequest.tenant_id == MOCK_TENANT_ID,
            LLMRequest.created_at >= thirty_days_ago,
        )
    )
    total_cost = float(cost_result.scalar() or 0.0)

    return MetricsResponse(
        total_tickets=total_tickets,
        tickets_by_status=tickets_by_status,
        tickets_by_priority=tickets_by_priority,
        avg_processing_time_seconds=avg_processing_time,
        automation_rate=automation_rate,
        total_llm_cost_usd=total_cost,
    )
