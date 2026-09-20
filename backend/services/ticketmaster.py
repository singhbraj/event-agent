from datetime import datetime

import requests

from config import TICKETMASTER_API_KEY

EVENTS_URL = "https://app.ticketmaster.com/discovery/v2/events.json"
EVENT_URL = "https://app.ticketmaster.com/discovery/v2/events/{event_id}.json"
VENUES_URL = "https://app.ticketmaster.com/discovery/v2/venues.json"
VENUE_URL = "https://app.ticketmaster.com/discovery/v2/venues/{venue_id}.json"
MAX_SEARCH_RESULTS = 4


class TicketmasterError(Exception):
    pass


def _get(url: str, params: dict, *, missing: str | None = None) -> dict:
    if not TICKETMASTER_API_KEY:
        raise TicketmasterError("TICKETMASTER_API_KEY is not configured")

    query = {key: value for key, value in params.items() if value is not None}
    query["apikey"] = TICKETMASTER_API_KEY

    response = requests.get(url, params=query, timeout=15)

    if response.status_code == 404 and missing:
        raise TicketmasterError(missing)

    if not response.ok:
        raise TicketmasterError(
            f"Ticketmaster request failed with status {response.status_code}"
        )

    return response.json()


def _search_events(params: dict) -> dict:
    payload = _get(
        EVENTS_URL,
        {
            **params,
            "size": MAX_SEARCH_RESULTS,
            "sort": "date,asc",
        },
    )
    raw_events = payload.get("_embedded", {}).get("events", [])
    return {"events": [_map_event(event) for event in raw_events]}


def search_events(
    *,
    keyword: str,
    city: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    return _search_events(
        {
            "keyword": keyword,
            "city": city,
            "startDateTime": _to_ticketmaster_datetime(start_date),
            "endDateTime": _to_ticketmaster_datetime(end_date, end_of_day=True),
        }
    )


def search_events_by_location(
    *,
    city: str | None = None,
    state_code: str | None = None,
    country_code: str | None = None,
    postal_code: str | None = None,
    latlong: str | None = None,
    radius: int | None = None,
    unit: str = "miles",
    keyword: str | None = None,
) -> dict:
    if not any([city, state_code, country_code, postal_code, latlong]):
        raise TicketmasterError("A city, postal code, or latlong is required")

    return _search_events(
        {
            "keyword": keyword,
            "city": city,
            "stateCode": state_code,
            "countryCode": country_code,
            "postalCode": postal_code,
            "latlong": latlong,
            "radius": radius,
            "unit": unit if radius else None,
        }
    )


def search_events_by_date(
    *,
    start_date: str,
    end_date: str | None = None,
    city: str | None = None,
    keyword: str | None = None,
) -> dict:
    return _search_events(
        {
            "keyword": keyword,
            "city": city,
            "startDateTime": _to_ticketmaster_datetime(start_date),
            "endDateTime": _to_ticketmaster_datetime(end_date, end_of_day=True),
        }
    )


def get_event(*, event_id: str) -> dict:
    payload = _get(
        EVENT_URL.format(event_id=event_id),
        {},
        missing=f"Event {event_id} was not found",
    )
    return {"event": _map_event_details(payload)}


def search_venues(
    *,
    keyword: str | None = None,
    city: str | None = None,
    country_code: str | None = None,
) -> dict:
    if not keyword and not city:
        raise TicketmasterError("A venue keyword or city is required")

    payload = _get(
        VENUES_URL,
        {
            "keyword": keyword,
            "city": city,
            "countryCode": country_code,
            "size": MAX_SEARCH_RESULTS,
        },
    )
    raw_venues = payload.get("_embedded", {}).get("venues", [])
    return {"venues": [_map_venue(venue) for venue in raw_venues]}


def get_venue(*, venue_id: str) -> dict:
    payload = _get(
        VENUE_URL.format(venue_id=venue_id),
        {},
        missing=f"Venue {venue_id} was not found",
    )
    return {"venue": _map_venue_details(payload)}


def _map_event(event: dict) -> dict:
    venues = event.get("_embedded", {}).get("venues", [])
    venue = venues[0] if venues else {}
    start = event.get("dates", {}).get("start", {})

    return {
        "id": event.get("id"),
        "name": event.get("name"),
        "url": event.get("url"),
        "date": start.get("localDate"),
        "time": start.get("localTime"),
        "venue": venue.get("name"),
        "venue_id": venue.get("id"),
        "city": (venue.get("city") or {}).get("name"),
    }


def _map_event_details(event: dict) -> dict:
    mapped = _map_event(event)
    venues = event.get("_embedded", {}).get("venues", [])
    venue = venues[0] if venues else {}
    address = venue.get("address") or {}
    classifications = event.get("classifications") or []
    classification = classifications[0] if classifications else {}
    attractions = event.get("_embedded", {}).get("attractions", [])

    return {
        **mapped,
        "info": event.get("info") or event.get("pleaseNote"),
        "price": _format_price(event.get("priceRanges") or []),
        "genre": (classification.get("genre") or {}).get("name"),
        "status": (event.get("dates") or {}).get("status", {}).get("code"),
        "address": address.get("line1"),
        "postal_code": venue.get("postalCode"),
        "country": (venue.get("country") or {}).get("name"),
        "attractions": [
            name
            for attraction in attractions
            if (name := attraction.get("name"))
        ],
    }


def _map_venue(venue: dict) -> dict:
    address = venue.get("address") or {}

    return {
        "id": venue.get("id"),
        "name": venue.get("name"),
        "city": (venue.get("city") or {}).get("name"),
        "address": address.get("line1"),
        "postal_code": venue.get("postalCode"),
        "country": (venue.get("country") or {}).get("name"),
        "url": venue.get("url"),
    }


def _map_venue_details(venue: dict) -> dict:
    location = venue.get("location") or {}
    general = venue.get("generalInfo") or {}
    box_office = venue.get("boxOfficeInfo") or {}

    return {
        **_map_venue(venue),
        "state": (venue.get("state") or {}).get("name"),
        "timezone": venue.get("timezone"),
        "parking": venue.get("parkingDetail"),
        "accessible_seating": venue.get("accessibleSeatingDetail"),
        "general_rule": general.get("generalRule"),
        "child_rule": general.get("childRule"),
        "box_office": box_office.get("openHoursDetail"),
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude"),
    }


def _to_ticketmaster_datetime(
    value: str | None,
    *,
    end_of_day: bool = False,
) -> str | None:
    if not value:
        return None

    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise TicketmasterError(f"Invalid date: {value}") from exc

    if len(raw) == 10 and end_of_day:
        parsed = parsed.replace(hour=23, minute=59, second=59)

    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_price(price_ranges: list[dict]) -> str | None:
    if not price_ranges:
        return None

    price = price_ranges[0]
    currency = price.get("currency") or ""
    minimum = price.get("min")
    maximum = price.get("max")

    if minimum is None and maximum is None:
        return None
    if minimum is not None and maximum is not None and minimum != maximum:
        amount = f"{minimum}-{maximum}"
    else:
        amount = str(minimum if minimum is not None else maximum)

    return f"{currency} {amount}".strip()
