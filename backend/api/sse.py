import json
from collections.abc import AsyncIterator

from services.conversation import ToolFinished, ToolStarted, TurnResult, TurnUpdate

SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
MEDIA_TYPE = "text/event-stream"


def frame(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def encode(update: TurnUpdate) -> str:
    if isinstance(update, ToolStarted):
        return frame(
            "status",
            {
                "stage": "tool",
                "tool": update.tool,
                "args": update.args,
                "elapsed": update.elapsed,
            },
        )

    if isinstance(update, ToolFinished):
        return frame("status", {"stage": "writing", "elapsed": update.elapsed})

    payload = {
        "response": update.text,
        "session_id": update.session_id,
        "events": [event.model_dump(mode="json") for event in update.events],
        "timings": update.timings,
        "pending_booking": (
            update.pending_booking.model_dump(mode="json")
            if update.pending_booking
            else None
        ),
        "booking_url": update.booking_url,
    }
    return frame("result", payload)


async def event_stream(
    updates: AsyncIterator[TurnUpdate],
    *,
    on_result=None,
) -> AsyncIterator[str]:
    yield frame("status", {"stage": "thinking"})

    result: TurnResult | None = None
    async for update in updates:
        if isinstance(update, TurnResult):
            result = update
            if update.pending_booking is not None:
                yield frame(
                    "approval",
                    update.pending_booking.model_dump(mode="json"),
                )
        yield encode(update)

    if result is not None and on_result is not None:
        await on_result(result)

    yield frame("done", {"elapsed": result.timings.get("total") if result else None})
