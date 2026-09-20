from datetime import datetime

import requests

from config import TICKETMASTER_API_KEY

EVENTS_URL = "https://app.ticketmaster.com/discovery/v2/events.json"
EVENT_URL = "https://app.ticketmaster.com/discovery/v2/events/{event_id}.json"
MAX_SEARCH_RESULTS = 4


class TicketmasterError(Exception):
    pass


def search_events(
    *,
    keyword: str,
    city: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    if not TICKETMASTER_API_KEY:
        raise TicketmasterError("TICKETMASTER_API_KEY is not configured")

    params = {
        "apikey": TICKETMASTER_API_KEY,
        "keyword": keyword,
        "city": city,
        "size": MAX_SEARCH_RESULTS,
        "sort": "date,asc",
    }
    start = _to_ticketmaster_datetime(start_date)
    end = _to_ticketmaster_datetime(end_date, end_of_day=True)
    if start:
        params["startDateTime"] = start
    if end:
        params["endDateTime"] = end

    response = requests.get(
        EVENTS_URL,
        params=params,
        timeout=15,
    )

    if not response.ok:
        raise TicketmasterError(
            f"Ticketmaster request failed with status {response.status_code}"
        )

    payload = response.json()
    raw_events = payload.get("_embedded", {}).get("events", [])
    return {"events": [_map_event(event) for event in raw_events]}


def get_event(*, event_id: str) -> dict:
    if not TICKETMASTER_API_KEY:
        raise TicketmasterError("TICKETMASTER_API_KEY is not configured")

    response = requests.get(
        EVENT_URL.format(event_id=event_id),
        params={"apikey": TICKETMASTER_API_KEY},
        timeout=15,
    )

    if response.status_code == 404:
        raise TicketmasterError(f"Event {event_id} was not found")

    if not response.ok:
        raise TicketmasterError(
            f"Ticketmaster request failed with status {response.status_code}"
        )

    return {"event": _map_event_details(response.json())}


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
