from datetime import datetime

from sqlalchemy import case, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from db import AsyncSessionFactory
from models.orm import Message, Ticket


async def persist_turn(payload: dict) -> None:
    user_created_at = datetime.fromisoformat(payload["user_created_at"])
    agent_created_at = datetime.fromisoformat(payload["agent_created_at"])

    async with AsyncSessionFactory() as session:
        ticket_insert = insert(Ticket).values(
            id=payload["session_id"],
            title=payload["user_message"][:160],
            created_at=user_created_at,
            updated_at=agent_created_at,
        )
        await session.execute(
            ticket_insert.on_conflict_do_update(
                index_elements=[Ticket.id],
                set_={"updated_at": agent_created_at},
            )
        )

        messages = [
            {
                "id": f"{payload['turn_id']}:user",
                "ticket_id": payload["session_id"],
                "role": "user",
                "content": payload["user_message"],
                "events": [],
                "created_at": user_created_at,
            },
            {
                "id": f"{payload['turn_id']}:agent",
                "ticket_id": payload["session_id"],
                "role": "agent",
                "content": payload["agent_message"],
                "events": payload["events"],
                "created_at": agent_created_at,
            },
        ]
        await session.execute(
            insert(Message).values(messages).on_conflict_do_nothing(
                index_elements=[Message.id]
            )
        )
        await session.commit()


async def list_tickets(session: AsyncSession) -> list[Ticket]:
    result = await session.scalars(
        select(Ticket).order_by(Ticket.updated_at.desc())
    )
    return list(result)


async def get_ticket_messages(
    session: AsyncSession,
    ticket_id: str,
) -> tuple[Ticket | None, list[Message]]:
    ticket = await session.get(Ticket, ticket_id)
    if ticket is None:
        return None, []

    role_order = case((Message.role == "user", 0), else_=1)
    result = await session.scalars(
        select(Message)
        .where(Message.ticket_id == ticket_id)
        .order_by(Message.created_at.asc(), role_order.asc())
    )
    return ticket, list(result)
