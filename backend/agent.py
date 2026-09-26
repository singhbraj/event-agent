from functools import lru_cache

from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy
from langgraph.checkpoint.memory import InMemorySaver

from middlewares import build_hitl_middleware
from models.schemas import EventSearchResult
from prompts.system_prompt import build_system_prompt
from providers import build_chat_model
from tools import ALL_TOOLS


@lru_cache(maxsize=1)
def get_agent():
    model, _provider = build_chat_model()
    return create_agent(
        model=model,
        tools=ALL_TOOLS,
        system_prompt=build_system_prompt(),
        middleware=[build_hitl_middleware()],
        response_format=ProviderStrategy(EventSearchResult),
        # Remembers each conversation by thread_id, including a paused booking.
        # In-memory only: a server restart forgets every conversation.
        checkpointer=InMemorySaver(),
        name="event-agent",
    )
