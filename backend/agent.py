from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy

from models.schemas import EventSearchResult
from prompts.system_prompt import build_system_prompt
from providers import build_chat_model
from tools import ALL_TOOLS


def build_agent():
    model, _provider = build_chat_model()
    return create_agent(
        model=model,
        tools=ALL_TOOLS,
        system_prompt=build_system_prompt(),
        response_format=ProviderStrategy(EventSearchResult),
        name="event-agent",
    )
