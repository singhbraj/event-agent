import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphInterrupt
from langgraph.types import Command

from agent import build_agent
from models.schemas import EventItem, EventSearchResult, PendingBooking

logger = logging.getLogger(__name__)


class BookingDecisionError(Exception):
    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class ToolStarted:
    tool: str
    args: dict
    elapsed: float


@dataclass(frozen=True)
class ToolFinished:
    elapsed: float


@dataclass(frozen=True)
class TurnResult:
    session_id: str
    text: str
    events: list[EventItem]
    timings: dict[str, float] = field(default_factory=dict)
    pending_booking: PendingBooking | None = None
    booking_url: str | None = None
    user_created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    agent_created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


TurnUpdate = ToolStarted | ToolFinished | TurnResult


@lru_cache(maxsize=1)
def get_agent():
    return build_agent(checkpointer=InMemorySaver())


class Stopwatch:
    def __init__(self) -> None:
        self._started = time.perf_counter()
        self.marks: dict[str, float] = {}

    def mark(self, label: str) -> float:
        elapsed = round(time.perf_counter() - self._started, 2)
        self.marks[label] = elapsed
        return elapsed


def _thread(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


def _text_of(messages: list) -> str:
    for message in reversed(messages or []):
        content = getattr(message, "content", "")
        if isinstance(content, str) and content:
            return content
    return ""


def _without_urls(events: list[EventItem]) -> list[EventItem]:
    return [event.model_copy(update={"url": None}) for event in events]


def _booking_url_from(messages: list) -> str | None:
    for message in reversed(messages or []):
        if getattr(message, "name", None) != "proceed_to_booking":
            continue
        content = getattr(message, "content", "")
        if isinstance(content, str) and content.startswith("http"):
            return content
    return None


def _selected_text(booking: PendingBooking) -> str:
    lines = ["You selected:", booking.name]
    if booking.venue:
        lines.append(booking.venue)
    if booking.city:
        lines.append(booking.city)
    if booking.date:
        lines.append(booking.date)
    if booking.time:
        lines.append(booking.time)
    if booking.price:
        lines.append(booking.price)
    lines.append("")
    lines.append("Would you like to continue to Ticketmaster to purchase the ticket?")
    return "\n".join(lines)


def _pending_from_snapshot(snapshot) -> PendingBooking | None:
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


def _build_result(
    *,
    session_id: str,
    structured: EventSearchResult | None,
    fallback_text: str,
    timings: dict[str, float],
    user_created_at: datetime,
    pending_booking: PendingBooking | None = None,
    messages: list | None = None,
) -> TurnResult:
    if pending_booking is not None:
        return TurnResult(
            session_id=session_id,
            text=_selected_text(pending_booking),
            events=[],
            timings=timings,
            pending_booking=pending_booking,
            user_created_at=user_created_at,
            agent_created_at=datetime.now(timezone.utc),
        )

    booking_url = _booking_url_from(messages or [])
    events = structured.events if structured else []
    if not booking_url:
        events = _without_urls(events)

    return TurnResult(
        session_id=session_id,
        text=structured.summary if structured else fallback_text,
        events=events,
        timings=timings,
        booking_url=booking_url,
        user_created_at=user_created_at,
        agent_created_at=datetime.now(timezone.utc),
    )


def _progress(node: str, payload: dict, watch: Stopwatch) -> list[TurnUpdate]:
    updates: list[TurnUpdate] = []

    for message in payload.get("messages", []) or []:
        for call in getattr(message, "tool_calls", []) or []:
            args = dict(call["args"])
            if call["name"] == "proceed_to_booking":
                args.pop("event_url", None)
            updates.append(
                ToolStarted(
                    tool=call["name"],
                    args=args,
                    elapsed=watch.mark(f"call:{call['name']}"),
                )
            )

    if node == "tools":
        updates.append(ToolFinished(elapsed=watch.mark("tool_done")))

    return updates


def _log_timings(marks: dict[str, float]) -> None:
    logger.info(
        "chat turn timings: %s",
        ", ".join(f"{label}={value:.2f}s" for label, value in marks.items()),
    )


async def _finish(
    *,
    session_id: str,
    watch: Stopwatch,
    structured: EventSearchResult | None,
    fallback_text: str,
    user_created_at: datetime,
    messages: list | None = None,
) -> TurnResult:
    snapshot = await get_agent().aget_state(_thread(session_id))
    pending = _pending_from_snapshot(snapshot)
    if pending is None and structured is None:
        structured = snapshot.values.get("structured_response")
        messages = messages or snapshot.values.get("messages")
        fallback_text = fallback_text or _text_of(snapshot.values.get("messages") or [])

    watch.mark("total")
    _log_timings(watch.marks)
    return _build_result(
        session_id=session_id,
        structured=structured,
        fallback_text=fallback_text,
        timings=watch.marks,
        user_created_at=user_created_at,
        pending_booking=pending,
        messages=messages or snapshot.values.get("messages"),
    )


async def run_turn(*, message: str, session_id: str) -> TurnResult:
    user_created_at = datetime.now(timezone.utc)
    watch = Stopwatch()
    agent = get_agent()
    existing = _pending_from_snapshot(await agent.aget_state(_thread(session_id)))
    if existing is not None:
        return await _finish(
            session_id=session_id,
            watch=watch,
            structured=None,
            fallback_text=_selected_text(existing),
            user_created_at=user_created_at,
        )

    try:
        state = await agent.ainvoke(
            {"messages": [{"role": "user", "content": message}]},
            _thread(session_id),
        )
    except GraphInterrupt:
        state = {}

    return await _finish(
        session_id=session_id,
        watch=watch,
        structured=state.get("structured_response"),
        fallback_text=_text_of(state.get("messages") or []),
        user_created_at=user_created_at,
        messages=state.get("messages"),
    )


async def stream_turn(
    *,
    message: str,
    session_id: str,
) -> AsyncIterator[TurnUpdate]:
    user_created_at = datetime.now(timezone.utc)
    watch = Stopwatch()
    agent = get_agent()
    existing = _pending_from_snapshot(await agent.aget_state(_thread(session_id)))
    if existing is not None:
        yield await _finish(
            session_id=session_id,
            watch=watch,
            structured=None,
            fallback_text=_selected_text(existing),
            user_created_at=user_created_at,
        )
        return

    structured: EventSearchResult | None = None
    fallback_text = ""
    messages: list = []

    try:
        async for update in agent.astream(
            {"messages": [{"role": "user", "content": message}]},
            _thread(session_id),
            stream_mode="updates",
        ):
            for node, payload in update.items():
                if node == "__interrupt__" or not isinstance(payload, dict):
                    continue

                structured = payload.get("structured_response") or structured
                node_messages = payload.get("messages", []) or []
                if node_messages:
                    messages = node_messages
                fallback_text = _text_of(node_messages) or fallback_text

                for progress in _progress(node, payload, watch):
                    yield progress
    except GraphInterrupt:
        pass

    yield await _finish(
        session_id=session_id,
        watch=watch,
        structured=structured,
        fallback_text=fallback_text,
        user_created_at=user_created_at,
        messages=messages,
    )


async def resume_turn(
    *,
    session_id: str,
    action_id: str,
    approved: bool,
) -> TurnResult:
    user_created_at = datetime.now(timezone.utc)
    watch = Stopwatch()
    agent = get_agent()
    snapshot = await agent.aget_state(_thread(session_id))
    pending = _pending_from_snapshot(snapshot)
    if pending is None:
        raise BookingDecisionError("No booking is waiting for approval.", status_code=404)
    if pending.action_id != action_id:
        raise BookingDecisionError("This booking action is no longer active.", status_code=409)

    try:
        state = await agent.ainvoke(
            Command(resume={"approved": approved}),
            _thread(session_id),
        )
    except GraphInterrupt:
        state = {}
    return await _finish(
        session_id=session_id,
        watch=watch,
        structured=state.get("structured_response"),
        fallback_text=_text_of(state.get("messages") or []),
        user_created_at=user_created_at,
        messages=state.get("messages"),
    )


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
