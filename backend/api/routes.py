from fastapi import APIRouter, HTTPException, Query

from services.ticketmaster import TicketmasterError, search_events

router = APIRouter()


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"mesaage":"Pong"}


@router.get("/events")
def get_events(
    keyword: str = Query(..., min_length=1),
    city: str = Query(..., min_length=1),
) -> dict:
    try:
        return search_events(keyword=keyword, city=city)
    except TicketmasterError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
