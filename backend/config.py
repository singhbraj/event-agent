import os 
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")