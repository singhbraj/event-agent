from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api import sse
from db import get_db
from models.schemas import (
    ChatRequest,
    ChatResponse,
    TicketDetail,
    TicketMessage,
    TicketSummary,
)
from services.conversation import build_turn_payload, run_turn, stream_turn
from services.tickets import get_ticket_messages, list_tickets
from services.ticketmaster import TicketmasterError, get_event, search_events
from task_queue import enqueue_turn

router = APIRouter()


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"message": "Pong"}


@router.get("/events")
def get_events(
    keyword: str = Query(..., min_length=1),
    city: str = Query(..., min_length=1),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
) -> dict:
    try:
        return search_events(
            keyword=keyword,
            city=city,
            start_date=start_date,
            end_date=end_date,
        )
    except TicketmasterError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/events/{event_id}")
def get_event_details(event_id: str) -> dict:
    try:
        return get_event(event_id=event_id)
    except TicketmasterError as exc:
        status_code = 404 if "was not found" in str(exc) else 502
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/chat")
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
) -> ChatResponse:
    result = await run_turn(
        message=request.message,
        session_id=request.session_id,
    )

    background_tasks.add_task(
        enqueue_turn,
        build_turn_payload(result, user_message=request.message),
    )

    return ChatResponse(
        response=result.text,
        session_id=result.session_id,
        events=result.events,
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    async def persist(result) -> None:
        await enqueue_turn(build_turn_payload(result, user_message=request.message))

    updates = stream_turn(
        message=request.message,
        session_id=request.session_id,
    )

    return StreamingResponse(
        sse.event_stream(updates, on_result=persist),
        media_type=sse.MEDIA_TYPE,
        headers=sse.SSE_HEADERS,
    )


@router.get("/tickets", response_model=list[TicketSummary])
async def get_tickets(
    db: AsyncSession = Depends(get_db),
) -> list[TicketSummary]:
    tickets = await list_tickets(db)
    return [
        TicketSummary(
            id=ticket.id,
            title=ticket.title,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
        )
        for ticket in tickets
    ]


@router.get("/tickets/{session_id}", response_model=TicketDetail)
async def get_ticket(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> TicketDetail:
    ticket, messages = await get_ticket_messages(db, session_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return TicketDetail(
        session_id=ticket.id,
        title=ticket.title,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        messages=[
            TicketMessage(
                id=message.id,
                role=message.role,
                content=message.content,
                events=message.events,
                created_at=message.created_at,
            )
            for message in messages
        ],
    )
