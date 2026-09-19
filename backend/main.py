from fastapi import FastAPI

from api.routes import router

app = FastAPI(title="event-agent-backend")
app.include_router(router)
