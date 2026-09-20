import { ApiError, BASE_URL, postJson } from './client'

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

export async function sendChatMessage({ message, sessionId, signal }) {
  const data = await postJson(
    '/chat',
    { message, session_id: sessionId },
    { signal },
  )

  return {
    text: data.response,
    sessionId: data.session_id,
    events: mapEvents(data.events),
  }
}

function parseFrame(frame) {
  const lines = frame.split('\n')
  const event = lines
    .find((line) => line.startsWith('event:'))
    ?.slice(6)
    .trim()
  const data = lines
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.slice(5).trim())
    .join('')

  if (!event || !data) return null
  return { event, data: JSON.parse(data) }
}

export async function streamChatMessage({
  message,
  sessionId,
  onStatus,
  signal,
}) {
  let response

  try {
    response = await fetch(`${BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId }),
      signal,
    })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError('Could not reach the server. Is the backend running?')
  }

  if (!response.ok || !response.body) {
    throw new ApiError('Request to /chat/stream failed.', response.status)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let result = null

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const frames = buffer.split('\n\n')
    buffer = frames.pop() ?? ''

    for (const frame of frames) {
      const parsed = parseFrame(frame)
      if (!parsed) continue

      if (parsed.event === 'status') {
        onStatus?.(parsed.data)
      } else if (parsed.event === 'result') {
        result = {
          text: parsed.data.response,
          sessionId: parsed.data.session_id,
          events: mapEvents(parsed.data.events),
          timings: parsed.data.timings,
        }
      }
    }
  }

  if (!result) throw new ApiError('The server did not return a response.')
  return result
}
