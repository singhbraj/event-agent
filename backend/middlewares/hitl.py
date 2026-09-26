from langchain.agents.middleware import HumanInTheLoopMiddleware


def build_hitl_middleware() -> HumanInTheLoopMiddleware:
    # Only booking needs a human. Search and details tools run straight away.
    return HumanInTheLoopMiddleware(
        interrupt_on={
            "proceed_to_booking": {
                "allowed_decisions": ["approve", "reject"],
                "description": "Continue to Ticketmaster to buy this ticket",
            }
        }
    )
