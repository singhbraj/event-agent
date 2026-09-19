from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from langgraph.checkpoint.memory import InMemorySaver
from sqlalchemy.ext.asyncio import AsyncSession

from agent import build_agent
from db import get_db
from models.schemas import (
    ChatRequest,
    ChatResponse,
    TicketDetail,
    TicketMessage,
    TicketSummary,
)
from services.tickets import get_ticket_messages, list_tickets
from services.ticketmaster import TicketmasterError, search_events
from task_queue import enqueue_turn

router = APIRouter()

agent = build_agent(checkpointer=InMemorySaver())


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"message": "Pong"}


@router.get("/events")
def get_events(
    keyword: str = Query(..., min_length=1),
    city: str = Query(..., min_length=1),
) -> dict:
    try:
        return search_events(keyword=keyword, city=city)
    except TicketmasterError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/chat")
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
) -> ChatResponse:
    user_created_at = datetime.now(timezone.utc)
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": request.message}]},
        {"configurable": {"thread_id": request.session_id}},
    )
    agent_created_at = datetime.now(timezone.utc)

    events_result = result.get("structured_response")
    if events_result is None:
        response_text = result["messages"][-1].content
        response_events = []
    else:
        response_text = events_result.summary
        response_events = events_result.events

    background_tasks.add_task(
        enqueue_turn,
        {
            "turn_id": str(uuid4()),
            "session_id": request.session_id,
            "user_message": request.message,
            "agent_message": response_text,
            "events": [
                event.model_dump(mode="json") for event in response_events
            ],
            "user_created_at": user_created_at.isoformat(),
            "agent_created_at": agent_created_at.isoformat(),
        },
    )

    return ChatResponse(
        response=response_text,
        session_id=request.session_id,
        events=response_events,
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
