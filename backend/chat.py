import json
from datetime import date, datetime

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from agent import build_agent
from providers import select_provider


def format_when(event) -> str:
    if not event.date:
        return "Date TBA"

    try:
        day = date.fromisoformat(event.date).strftime("%a, %d %b %Y")
    except ValueError:
        day = event.date

    if not event.time:
        return day

    try:
        clock = datetime.strptime(event.time, "%H:%M:%S").strftime("%I:%M %p").lstrip("0")
    except ValueError:
        clock = event.time

    return f"{day} at {clock}"


def current_turn_messages(messages: list) -> list:
    for index in range(len(messages) - 1, -1, -1):
        if getattr(messages[index], "type", None) == "human":
            return messages[index:]
    return messages


def pending_booking(agent, thread) -> dict | None:
    snapshot = agent.get_state(thread)
    interrupts = getattr(snapshot, "interrupts", None) or ()
    if not interrupts:
        return None
    payload = interrupts[0].value
    return payload if isinstance(payload, dict) else None


def print_pending(payload: dict) -> None:
    print("\nYou selected:\n")
    print(f"  {payload.get('name')}")
    if payload.get("venue"):
        print(f"  {payload['venue']}")
    if payload.get("city"):
        print(f"  {payload['city']}")
    if payload.get("date"):
        print(f"  {payload['date']}")
    if payload.get("time"):
        print(f"  {payload['time']}")
    if payload.get("price"):
        print(f"  {payload['price']}")
    print("\nWould you like to continue to Ticketmaster to purchase the ticket?")
    print("Type approve or reject.")


def print_result(result) -> None:
    tool_calls = [
        call
        for message in current_turn_messages(result["messages"])
        for call in getattr(message, "tool_calls", []) or []
    ]

    if tool_calls:
        print("\nTools called:")
        for call in tool_calls:
            args = dict(call["args"])
            if call["name"] == "proceed_to_booking":
                args.pop("event_url", None)
            print(f"  {call['name']} {json.dumps(args)}")
    else:
        print("\nTools called: none")

    events_result = result.get("structured_response")
    if events_result is None:
        print(result["messages"][-1].content)
        return

    print(f"\n{events_result.summary}\n")
    for index, event in enumerate(events_result.events, start=1):
        location = ", ".join(part for part in (event.venue, event.city) if part)
        print(f"  {index}. {event.name}")
        if location:
            print(f"     {location}")
        if event.address:
            print(f"     {event.address}")
        print(f"     {format_when(event)}")
        if event.price:
            print(f"     {event.price}")
        if event.info:
            print(f"     {event.info}")
        print()


def main() -> None:
    provider = select_provider()
    agent = build_agent(checkpointer=InMemorySaver())
    thread = {"configurable": {"thread_id": "cli"}}
    print(f"Event agent ready using {provider.name} ({provider.model}).")
    print("Ask about events, or type quit to exit.")

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input or user_input.lower() in {"quit", "exit"}:
            break

        waiting = pending_booking(agent, thread)
        if waiting and user_input.lower() in {"approve", "reject"}:
            result = agent.invoke(
                Command(resume={"approved": user_input.lower() == "approve"}),
                thread,
            )
            print_result(result)
            continue

        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            thread,
        )
        waiting = pending_booking(agent, thread)
        if waiting:
            print_pending(waiting)
            continue
        print_result(result)


if __name__ == "__main__":
    main()
