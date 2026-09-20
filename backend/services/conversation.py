import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver

from agent import build_agent
from models.schemas import EventItem, EventSearchResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolStarted:
    tool: str
    args: dict
    elapsed: float


@dataclass(frozen=True)
class ToolFinished:
    elapsed: float


@dataclass(frozen=True)
class TurnResult:
    session_id: str
    text: str
    events: list[EventItem]
    timings: dict[str, float] = field(default_factory=dict)
    user_created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    agent_created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


TurnUpdate = ToolStarted | ToolFinished | TurnResult


@lru_cache(maxsize=1)
def get_agent():
    return build_agent(checkpointer=InMemorySaver())


class Stopwatch:
    def __init__(self) -> None:
        self._started = time.perf_counter()
        self.marks: dict[str, float] = {}

    def mark(self, label: str) -> float:
        elapsed = round(time.perf_counter() - self._started, 2)
        self.marks[label] = elapsed
        return elapsed


def _thread(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


def _build_result(
    *,
    session_id: str,
    structured: EventSearchResult | None,
    fallback_text: str,
    timings: dict[str, float],
    user_created_at: datetime,
) -> TurnResult:
    return TurnResult(
        session_id=session_id,
        text=structured.summary if structured else fallback_text,
        events=structured.events if structured else [],
        timings=timings,
        user_created_at=user_created_at,
        agent_created_at=datetime.now(timezone.utc),
    )


def _text_of(messages: list) -> str:
    for message in reversed(messages or []):
        content = getattr(message, "content", "")
        if isinstance(content, str) and content:
            return content
    return ""


def _progress(node: str, payload: dict, watch: Stopwatch) -> list[TurnUpdate]:
    updates: list[TurnUpdate] = []

    for message in payload.get("messages", []) or []:
        for call in getattr(message, "tool_calls", []) or []:
            updates.append(
                ToolStarted(
                    tool=call["name"],
                    args=call["args"],
                    elapsed=watch.mark(f"call:{call['name']}"),
                )
            )

    if node == "tools":
        updates.append(ToolFinished(elapsed=watch.mark("tool_done")))

    return updates


def _log_timings(marks: dict[str, float]) -> None:
    logger.info(
        "chat turn timings: %s",
        ", ".join(f"{label}={value:.2f}s" for label, value in marks.items()),
    )


async def run_turn(*, message: str, session_id: str) -> TurnResult:
    user_created_at = datetime.now(timezone.utc)
    watch = Stopwatch()

    state = await get_agent().ainvoke(
        {"messages": [{"role": "user", "content": message}]},
        _thread(session_id),
    )
    watch.mark("total")
    _log_timings(watch.marks)

    return _build_result(
        session_id=session_id,
        structured=state.get("structured_response"),
        fallback_text=_text_of(state["messages"]),
        timings=watch.marks,
        user_created_at=user_created_at,
    )


async def stream_turn(
    *,
    message: str,
    session_id: str,
) -> AsyncIterator[TurnUpdate]:
    user_created_at = datetime.now(timezone.utc)
    watch = Stopwatch()
    agent = get_agent()
    structured: EventSearchResult | None = None
    fallback_text = ""

    async for update in agent.astream(
        {"messages": [{"role": "user", "content": message}]},
        _thread(session_id),
        stream_mode="updates",
    ):
        for node, payload in update.items():
            if not isinstance(payload, dict):
                continue

            structured = payload.get("structured_response") or structured
            fallback_text = _text_of(payload.get("messages", [])) or fallback_text

            for progress in _progress(node, payload, watch):
                yield progress

    if structured is None:
        snapshot = await agent.aget_state(_thread(session_id))
        structured = snapshot.values.get("structured_response")

    watch.mark("total")
    _log_timings(watch.marks)

    yield _build_result(
        session_id=session_id,
        structured=structured,
        fallback_text=fallback_text,
        timings=watch.marks,
        user_created_at=user_created_at,
    )


def build_turn_payload(result: TurnResult, *, user_message: str) -> dict:
    return {
        "turn_id": str(uuid4()),
        "session_id": result.session_id,
        "user_message": user_message,
        "agent_message": result.text,
        "events": [event.model_dump(mode="json") for event in result.events],
        "user_created_at": result.user_created_at.isoformat(),
        "agent_created_at": result.agent_created_at.isoformat(),
    }
