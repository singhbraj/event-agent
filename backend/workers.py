from arq.connections import RedisSettings

from config import REDIS_URL
from db import init_db
from services.tickets import persist_turn as persist_turn_to_db


async def startup(_ctx: dict) -> None:
    await init_db()


async def persist_turn(_ctx: dict, payload: dict) -> None:
    await persist_turn_to_db(payload)


class WorkerSettings:
    functions = [persist_turn]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(REDIS_URL)
    max_tries = 5
