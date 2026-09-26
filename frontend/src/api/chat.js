import { postJson } from './client'

function mapEvents(events) {
  return (events ?? []).map((event) => ({
    id: event.id,
    name: event.name,
    venue: event.venue,
    city: event.city,
    date: event.date,
    time: event.time,
    url: event.url,
    address: event.address,
    price: event.price,
    info: event.info,
    genre: event.genre,
  }))
}

function mapReply(data) {
  return {
    text: data.response,
    sessionId: data.session_id,
    events: mapEvents(data.events),
    pendingBooking: data.pending_booking ?? null,
    bookingUrl: data.booking_url ?? null,
  }
}

export async function sendChatMessage({ message, sessionId, signal }) {
  const data = await postJson(
    '/chat',
    { message, session_id: sessionId },
    { signal },
  )
  return mapReply(data)
}

export async function decideBooking({ approved, sessionId, signal }) {
  const path = approved ? '/approve' : '/reject'
  const data = await postJson(path, { session_id: sessionId }, { signal })
  return mapReply(data)
}
