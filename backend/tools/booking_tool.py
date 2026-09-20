from uuid import uuid4

from langchain_core.tools import tool
from langgraph.types import interrupt


@tool
def proceed_to_booking(
    event_url: str,
    name: str,
    venue: str | None = None,
    city: str | None = None,
    date: str | None = None,
    time: str | None = None,
    price: str | None = None,
) -> str:
    """Prepare a Ticketmaster booking for one already-found event.

    Call this when the user wants to book, buy, or continue to tickets for a
    specific event from a previous search. This pauses for human approval.
    Never paste the event URL in your reply until this tool has returned it.

    Args:
        event_url: Ticketmaster purchase URL from a previous search result.
        name: Event or artist name.
        venue: Venue name.
        city: City where the event is held.
        date: Local start date as YYYY-MM-DD.
        time: Local start time as HH:MM:SS.
        price: Ticket price range if known.
    """
    decision = interrupt(
        {
            "action_id": str(uuid4()),
            "name": name,
            "venue": venue,
            "city": city,
            "date": date,
            "time": time,
            "price": price,
        }
    )
    approved = isinstance(decision, dict) and decision.get("approved") is True
    if not approved:
        return "REJECTED"
    return event_url
