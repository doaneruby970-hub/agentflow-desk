"""API routes for tickets."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import TicketCreate, TicketListResponse, TicketResponse
from app.core.database import get_db
from app.models.tables import Ticket, WorkflowExecution, WorkflowState

router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])

# Mock tenant ID for MVP (replace with JWT extraction in production)
MOCK_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(
    ticket_data: TicketCreate,
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    """Create a new support ticket."""
    # Create ticket
    ticket = Ticket(
        tenant_id=MOCK_TENANT_ID,
        subject=ticket_data.subject,
        body=ticket_data.body,
        source=ticket_data.source,
        external_id=ticket_data.external_id,
        status="open",
    )
    db.add(ticket)
    await db.flush()

    # Create workflow execution
    workflow = WorkflowExecution(
        ticket_id=ticket.id,
        tenant_id=MOCK_TENANT_ID,
        state=WorkflowState.INGESTED,
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(ticket)

    # TODO: Enqueue Celery task for classification
    # classify_ticket.delay(str(ticket.id))

    return TicketResponse.model_validate(ticket)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    """Get ticket by ID."""
    result = await db.execute(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == MOCK_TENANT_ID,
        )
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return TicketResponse.model_validate(ticket)


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
) -> TicketListResponse:
    """List tickets with pagination."""
    query = select(Ticket).where(Ticket.tenant_id == MOCK_TENANT_ID)

    if status:
        query = query.where(Ticket.status == status)

    # Count total
    count_query = select(Ticket.id).where(Ticket.tenant_id == MOCK_TENANT_ID)
    if status:
        count_query = count_query.where(Ticket.status == status)

    total_result = await db.execute(count_query)
    total = len(total_result.all())

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Ticket.created_at.desc())

    result = await db.execute(query)
    tickets = result.scalars().all()

    return TicketListResponse(
        tickets=[TicketResponse.model_validate(t) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{ticket_id}/classify", status_code=202)
async def classify_ticket_endpoint(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger ticket classification."""
    result = await db.execute(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == MOCK_TENANT_ID,
        )
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # TODO: Enqueue Celery task
    # classify_ticket.delay(str(ticket_id))

    return {"message": "Classification task enqueued", "ticket_id": str(ticket_id)}


@router.post("/{ticket_id}/draft-reply", status_code=202)
async def draft_reply_endpoint(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate draft reply for ticket."""
    result = await db.execute(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == MOCK_TENANT_ID,
        )
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # TODO: Enqueue Celery task
    # draft_reply.delay(str(ticket_id))

    return {"message": "Draft reply task enqueued", "ticket_id": str(ticket_id)}


@router.post("/{ticket_id}/route", status_code=202)
async def route_ticket_endpoint(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Route ticket to appropriate team."""
    result = await db.execute(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.tenant_id == MOCK_TENANT_ID,
        )
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # TODO: Enqueue Celery task
    # route_ticket.delay(str(ticket_id))

    return {"message": "Routing task enqueued", "ticket_id": str(ticket_id)}
