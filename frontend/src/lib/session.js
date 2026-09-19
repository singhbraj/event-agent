const STORAGE_KEY = 'event-agent:session-id'

function createSessionId() {
  const created = crypto.randomUUID()
  sessionStorage.setItem(STORAGE_KEY, created)
  return created
}

export function getSessionId() {
  const existing = sessionStorage.getItem(STORAGE_KEY)
  if (existing) return existing

  return createSessionId()
}

export function startNewSession() {
  return createSessionId()
}
