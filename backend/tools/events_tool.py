from langchain_core.tools import tool

from services.ticketmaster import TicketmasterError, get_event, search_events


@tool
def search_events_tool(
    keyword: str,
    city: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Search Ticketmaster for live events.

    Args:
        keyword: Artist, genre, or event type, e.g. concert, jazz, Taylor Swift.
        city: City name, e.g. London.
        start_date: Optional earliest start as YYYY-MM-DD or ISO datetime.
            Use only when the user named a timeframe.
        end_date: Optional latest start as YYYY-MM-DD or ISO datetime.
            Use only when the user named a timeframe.
    """
    try:
        return search_events(
            keyword=keyword,
            city=city,
            start_date=start_date,
            end_date=end_date,
        )
    except TicketmasterError as exc:
        return {"events": [], "error": str(exc)}


@tool
def get_event_details_tool(event_id: str) -> dict:
    """Get details for one Ticketmaster event by id.

    Use this after search_events_tool when the user asks for more information
    about a specific event, such as price, description, or address.

    Args:
        event_id: Ticketmaster event id from a previous search result.
    """
    try:
        return get_event(event_id=event_id)
    except TicketmasterError as exc:
        return {"event": None, "error": str(exc)}
