from langchain_core.tools import tool

from services.ticketmaster import TicketmasterError, search_events


@tool
def search_events_tool(keyword: str, city: str) -> dict:
    """Search Ticketmaster for live events.

    Args:
        keyword: Artist, genre, or event type, e.g. concert, jazz, Taylor Swift.
        city: City name, e.g. London.
    """
    try:
        return search_events(keyword=keyword, city=city)
    except TicketmasterError as exc:
        return {"events": [], "error": str(exc)}
