import os 
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://event_agent:event_agent@localhost:5433/event_agent",
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")