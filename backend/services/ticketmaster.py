import requests

from config import TICKETMASTER_API_KEY

EVENTS_URL = "https://app.ticketmaster.com/discovery/v2/events.json"


class TicketmasterError(Exception):
    pass


def search_events(*, keyword: str, city: str) -> dict:
    if not TICKETMASTER_API_KEY:
        raise TicketmasterError("TICKETMASTER_API_KEY is not configured")

    response = requests.get(
        EVENTS_URL,
        params={
            "apikey": TICKETMASTER_API_KEY,
            "keyword": keyword,
            "city": city,
        },
        timeout=15,
    )

    if not response.ok:
        raise TicketmasterError(
            f"Ticketmaster request failed with status {response.status_code}"
        )

    payload = response.json()
    raw_events = payload.get("_embedded", {}).get("events", [])
    return {"events": [_map_event(event) for event in raw_events]}


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
