import { postJson } from './client'

export async function sendChatMessage({ message, sessionId, signal }) {
  const data = await postJson(
    '/chat',
    { message, session_id: sessionId },
    { signal },
  )

  return {
    text: data.response,
    sessionId: data.session_id,
    events: (data.events ?? []).map((event) => ({
      name: event.name,
      venue: event.venue,
      city: event.city,
      date: event.date,
      time: event.time,
      url: event.url,
    })),
  }
}
