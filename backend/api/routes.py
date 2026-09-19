from fastapi import APIRouter, HTTPException, Query
from langgraph.checkpoint.memory import InMemorySaver

from agent import build_agent
from models.schemas import ChatRequest, ChatResponse
from services.ticketmaster import TicketmasterError, search_events

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
async def chat(request: ChatRequest) -> ChatResponse:
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": request.message}]},
        {"configurable": {"thread_id": request.session_id}},
    )

    events_result = result.get("structured_response")
    if events_result is None:
        return ChatResponse(
            response=result["messages"][-1].content,
            session_id=request.session_id,
        )

    return ChatResponse(
        response=events_result.summary,
        session_id=request.session_id,
        events=events_result.events,
    )
