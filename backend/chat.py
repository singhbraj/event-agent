"""Terminal version of the chat. Same turns as the web app, approval asked with y/n."""

import asyncio

from providers import select_provider
from runtime import TurnResult, resume_turn, start_turn

THREAD_ID = "cli"


def ask_approval(result: TurnResult) -> bool:
    booking = result.pending_booking
    print("\n--- approval needed ---")
    for detail in (booking.name, booking.venue, booking.city, booking.date, booking.time, booking.price):
        if detail:
            print(f"  {detail}")
    return input("Continue to Ticketmaster? (y/N): ").strip().lower() in {"y", "yes"}


def show(result: TurnResult) -> None:
    print(f"\nAgent: {result.text}")
    for index, event in enumerate(result.events, start=1):
        where = ", ".join(part for part in (event.venue, event.city) if part)
        print(f"  {index}. {event.name} | {where} | {event.date or ''} {event.time or ''}")
    if result.booking_url:
        print(f"  Buy here: {result.booking_url}")


async def main() -> None:
    provider = select_provider()
    print(f"Event agent ready using {provider.name} ({provider.model}). Type quit to exit.")

    while True:
        message = input("\nYou: ").strip()
        if not message or message.lower() in {"quit", "exit"}:
            break

        result = await start_turn(THREAD_ID, message)
        while result.pending_booking is not None:
            result = await resume_turn(THREAD_ID, approved=ask_approval(result))
        show(result)


if __name__ == "__main__":
    asyncio.run(main())
