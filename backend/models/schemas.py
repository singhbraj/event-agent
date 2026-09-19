from datetime import datetime

from pydantic import BaseModel, Field


class EventItem(BaseModel):
    name: str = Field(description="Event or artist name")
    venue: str | None = Field(default=None, description="Venue name")
    city: str | None = Field(default=None, description="City where the event is held")
    date: str | None = Field(default=None, description="Local start date as YYYY-MM-DD")
    time: str | None = Field(default=None, description="Local start time as HH:MM:SS")
    url: str | None = Field(default=None, description="Ticket or event URL")


class EventSearchResult(BaseModel):
    summary: str = Field(
        description="Short intro for the user, e.g. 'Here are some events I found'"
    )
    events: list[EventItem] = Field(
        default_factory=list,
        description="Events to show the user",
    )


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str = Field(default="default", min_length=1, max_length=64)


class ChatResponse(BaseModel):
    response: str
    session_id: str
    events: list[EventItem] = Field(default_factory=list)


class TicketSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class TicketMessage(BaseModel):
    id: str
    role: str
    content: str
    events: list[EventItem] = Field(default_factory=list)
    created_at: datetime


class TicketDetail(BaseModel):
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[TicketMessage]
