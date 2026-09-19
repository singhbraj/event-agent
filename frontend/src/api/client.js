const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function postJson(path, body, { signal } = {}) {
  let response

  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
    })
  } catch {
    throw new ApiError('Could not reach the server. Is the backend running?')
  }

  if (!response.ok) {
    throw new ApiError(`Request to ${path} failed.`, response.status)
  }

  return response.json()
}
