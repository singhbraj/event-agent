"""One turn of the event agent.

A turn is one call into the agent graph:

    start_turn    the user said something
    resume_turn   the user approved or rejected a booking

The graph either finishes with an answer, or pauses because the model wants to
book a ticket. Either way you get back a TurnResult.
"""

from dataclasses import dataclass, field

from langgraph.types import Command

from agent import get_agent
from models.schemas import EventItem, PendingBooking

APPROVAL_TEXT = "Please approve or reject this booking."


class NothingToApprove(Exception):
    pass


@dataclass
class TurnResult:
    text: str
    events: list[EventItem] = field(default_factory=list)
    pending_booking: PendingBooking | None = None  # set while waiting for the human
    booking_url: str | None = None  # set once the human approved


async def start_turn(thread_id: str, message: str) -> TurnResult:
    # A paused graph needs approve or reject, not another message.
    if (booking := await _paused_on(thread_id)) is not None:
        return _needs_approval(booking)

    return await _run(thread_id, {"messages": [{"role": "user", "content": message}]})


async def resume_turn(thread_id: str, approved: bool) -> TurnResult:
    booking = await _paused_on(thread_id)
    if booking is None:
        raise NothingToApprove("No booking is waiting for approval.")

    decision = (
        {"type": "approve"}
        if approved
        else {"type": "reject", "message": "The user declined this booking."}
    )
    result = await _run(thread_id, Command(resume={"decisions": [decision]}))

    # Approved, so the user may now open the link. This is the only way a
    # Ticketmaster link ever reaches the browser.
    if approved and result.pending_booking is None:
        result.booking_url = booking["event_url"]
    return result


async def _run(thread_id: str, graph_input) -> TurnResult:
    output = await get_agent().ainvoke(graph_input, _config(thread_id), version="v2")

    if (booking := _booking_call(output.interrupts)) is not None:
        return _needs_approval(booking)

    answer = output.value.get("structured_response")
    if answer is None:
        return TurnResult(text="Sorry, I could not put that answer together.")

    return TurnResult(
        text=answer.summary,
        events=[event.model_copy(update={"url": None}) for event in answer.events],
    )


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


async def _paused_on(thread_id: str) -> dict | None:
    state = await get_agent().aget_state(_config(thread_id))
    return _booking_call(state.interrupts)


def _booking_call(interrupts) -> dict | None:
    """Arguments of the booking the graph is paused on, or None if it is running."""
    if not interrupts:
        return None
    return interrupts[0].value["action_requests"][0]["args"]


def _needs_approval(booking: dict) -> TurnResult:
    """The approval card. It shows the event but never the purchase link."""
    return TurnResult(
        text=APPROVAL_TEXT,
        pending_booking=PendingBooking(
            name=booking.get("name") or "Selected event",
            venue=booking.get("venue"),
            city=booking.get("city"),
            date=booking.get("date"),
            time=booking.get("time"),
            price=booking.get("price"),
        ),
    )
