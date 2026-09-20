from langchain_core.tools import tool

from services.ticketmaster import (
    TicketmasterError,
    get_event,
    search_events,
    search_events_by_date,
    search_events_by_location,
)


@tool
def search_events_tool(
    keyword: str,
    city: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Search Ticketmaster for live events by keyword and city.

    This is the default search. Use the location or date tools only when the
    user cares mainly about where or when, rather than what.

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
def search_events_by_location_tool(
    city: str | None = None,
    state_code: str | None = None,
    country_code: str | None = None,
    postal_code: str | None = None,
    latlong: str | None = None,
    radius: int | None = None,
    keyword: str | None = None,
) -> dict:
    """Search events by place, including postal code or a radius around a point.

    Use this when the user asks about a place rather than an artist, for example
    "anything near SW1A 1AA" or "events within 10 miles of these coordinates".
    At least one of city, state_code, country_code, postal_code, or latlong is
    required.

    Args:
        city: City name, e.g. London.
        state_code: State or province code, e.g. NY.
        country_code: Two letter country code, e.g. GB.
        postal_code: Postal or zip code.
        latlong: Latitude and longitude as "51.5074,-0.1278".
        radius: Search radius in miles around the location.
        keyword: Optional artist, genre, or event type to narrow the search.
    """
    try:
        return search_events_by_location(
            city=city,
            state_code=state_code,
            country_code=country_code,
            postal_code=postal_code,
            latlong=latlong,
            radius=radius,
            keyword=keyword,
        )
    except TicketmasterError as exc:
        return {"events": [], "error": str(exc)}


@tool
def search_events_by_date_tool(
    start_date: str,
    end_date: str | None = None,
    city: str | None = None,
    keyword: str | None = None,
) -> dict:
    """Search events inside a date range.

    Use this when the timeframe is the main filter, for example "what is on this
    weekend" or "anything in London next month". Convert phrases like "tonight"
    or "this weekend" into dates using today's date before calling.

    Args:
        start_date: Earliest start as YYYY-MM-DD or ISO datetime.
        end_date: Optional latest start as YYYY-MM-DD or ISO datetime.
        city: Optional city name to limit the search.
        keyword: Optional artist, genre, or event type to narrow the search.
    """
    try:
        return search_events_by_date(
            start_date=start_date,
            end_date=end_date,
            city=city,
            keyword=keyword,
        )
    except TicketmasterError as exc:
        return {"events": [], "error": str(exc)}


@tool
def get_event_details_tool(event_id: str) -> dict:
    """Get details for one Ticketmaster event by id.

    Use this after a search when the user asks for more information about a
    specific event, such as price, description, or address.

    Args:
        event_id: Ticketmaster event id from a previous search result.
    """
    try:
        return get_event(event_id=event_id)
    except TicketmasterError as exc:
        return {"event": None, "error": str(exc)}
