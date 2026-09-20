from langchain_core.tools import tool

from services.ticketmaster import TicketmasterError, get_venue, search_venues


@tool
def search_venues_tool(
    keyword: str | None = None,
    city: str | None = None,
    country_code: str | None = None,
) -> dict:
    """Search Ticketmaster for venues such as arenas, clubs, and theatres.

    Use this when the user asks about places rather than events, for example
    "which arenas are in Manchester" or "find the Vortex Jazz Club".
    At least one of keyword or city is required.

    Args:
        keyword: Venue name or type, e.g. Wembley, jazz club.
        city: City name, e.g. London.
        country_code: Two letter country code, e.g. GB.
    """
    try:
        return search_venues(
            keyword=keyword,
            city=city,
            country_code=country_code,
        )
    except TicketmasterError as exc:
        return {"venues": [], "error": str(exc)}


@tool
def get_venue_details_tool(venue_id: str) -> dict:
    """Get details for one Ticketmaster venue by id.

    Use this after search_venues_tool when the user asks about parking,
    accessibility, box office hours, or the exact address of a venue.

    Args:
        venue_id: Ticketmaster venue id from a previous venue search.
    """
    try:
        return get_venue(venue_id=venue_id)
    except TicketmasterError as exc:
        return {"venue": None, "error": str(exc)}
