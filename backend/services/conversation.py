import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from agent import build_agent
from models.schemas import EventItem, PendingBooking

logger = logging.getLogger(__name__)


class BookingDecisionError(Exception):
    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class TurnResult:
    session_id: str
    text: str
    events: list[EventItem]
    pending_booking: PendingBooking | None = None
    booking_url: str | None = None
    user_created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    agent_created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@lru_cache(maxsize=1)
def get_agent():
    return build_agent(checkpointer=InMemorySaver())


def _thread(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


def _text_of(messages: list) -> str:
    for message in reversed(messages or []):
        content = getattr(message, "content", "")
        if isinstance(content, str) and content:
            return content
    return ""


def _booking_url_from(messages: list) -> str | None:
    """The approved purchase URL, or None if the booking was never approved."""
    for message in reversed(messages or []):
        if getattr(message, "name", None) != "proceed_to_booking":
            continue
        content = getattr(message, "content", "")
        if isinstance(content, str) and content.startswith("http"):
            return content
    return None


def _selected_text(booking: PendingBooking) -> str:
    details = [
        booking.name,
        booking.venue,
        booking.city,
        booking.date,
        booking.time,
        booking.price,
    ]
    lines = ["You selected:", *[detail for detail in details if detail], ""]
    lines.append("Would you like to continue to Ticketmaster to purchase the ticket?")
    return "\n".join(lines)


def _pending_from_snapshot(snapshot) -> PendingBooking | None:
    """The booking waiting for approval, or None if the turn ran to completion."""
    interrupts = getattr(snapshot, "interrupts", None) or ()
    if not interrupts:
        return None
    payload = interrupts[0].value
    if not isinstance(payload, dict) or not payload.get("action_id"):
        return None
    return PendingBooking(
        action_id=payload["action_id"],
        name=payload.get("name") or "Selected event",
        venue=payload.get("venue"),
        city=payload.get("city"),
        date=payload.get("date"),
        time=payload.get("time"),
        price=payload.get("price"),
    )


async def _result(session_id: str, user_created_at: datetime) -> TurnResult:
    """Read the checkpoint and turn whatever the agent left there into a reply."""
    snapshot = await get_agent().aget_state(_thread(session_id))
    pending = _pending_from_snapshot(snapshot)
    if pending is not None:
        return TurnResult(
            session_id=session_id,
            text=_selected_text(pending),
            events=[],
            pending_booking=pending,
            user_created_at=user_created_at,
        )

    messages = snapshot.values.get("messages") or []
    structured = snapshot.values.get("structured_response")
    booking_url = _booking_url_from(messages)
    events = list(structured.events) if structured else []
    if not booking_url:
        events = [event.model_copy(update={"url": None}) for event in events]

    return TurnResult(
        session_id=session_id,
        text=structured.summary if structured else _text_of(messages),
        events=events,
        booking_url=booking_url,
        user_created_at=user_created_at,
    )


async def run_turn(*, message: str, session_id: str) -> TurnResult:
    user_created_at = datetime.now(timezone.utc)
    agent = get_agent()
    snapshot = await agent.aget_state(_thread(session_id))

    # A booking is parked on this thread, so re-show the card instead of
    # starting a new turn on a paused graph.
    if _pending_from_snapshot(snapshot) is None:
        await agent.ainvoke(
            {"messages": [{"role": "user", "content": message}]},
            _thread(session_id),
        )

    return await _result(session_id, user_created_at)


async def resume_turn(
    *,
    session_id: str,
    action_id: str,
    approved: bool,
) -> TurnResult:
    user_created_at = datetime.now(timezone.utc)
    agent = get_agent()
    pending = _pending_from_snapshot(await agent.aget_state(_thread(session_id)))
    if pending is None:
        raise BookingDecisionError("No booking is waiting for approval.", status_code=404)
    if pending.action_id != action_id:
        raise BookingDecisionError("This booking action is no longer active.", status_code=409)

    await agent.ainvoke(Command(resume={"approved": approved}), _thread(session_id))
    return await _result(session_id, user_created_at)


def build_turn_payload(result: TurnResult, *, user_message: str) -> dict:
    events = [event.model_dump(mode="json") for event in result.events]
    if result.booking_url:
        events = [
            {**event, "url": result.booking_url} if event.get("url") is None else event
            for event in events
        ]
    return {
        "turn_id": str(uuid4()),
        "session_id": result.session_id,
        "user_message": user_message,
        "agent_message": result.text,
        "events": events,
        "user_created_at": result.user_created_at.isoformat(),
        "agent_created_at": result.agent_created_at.isoformat(),
    }
