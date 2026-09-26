from langchain_core.tools import tool


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
    """Continue to Ticketmaster for one event the user already chose.

    Call this when the user wants to book, buy, or get tickets for a specific
    event from a previous search. Approval happens before this tool runs.
    Never paste the event URL in your reply. This tool returns it after approval.

    Args:
        event_url: Ticketmaster purchase URL from a previous search result.
        name: Event or artist name.
        venue: Venue name.
        city: City where the event is held.
        date: Local start date as YYYY-MM-DD.
        time: Local start time as HH:MM:SS.
        price: Ticket price range if known.
    """
    return event_url
