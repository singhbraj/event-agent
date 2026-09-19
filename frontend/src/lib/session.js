const STORAGE_KEY = 'event-agent:session-id'

export function getSessionId() {
  const existing = sessionStorage.getItem(STORAGE_KEY)
  if (existing) return existing

  const created = crypto.randomUUID()
  sessionStorage.setItem(STORAGE_KEY, created)
  return created
}
