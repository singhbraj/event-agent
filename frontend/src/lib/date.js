export function eventDateBadge(date) {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(date ?? '')
  if (!match) return null

  const stamp = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
  if (Number.isNaN(stamp.getTime())) return null

  return {
    month: stamp.toLocaleString(undefined, { month: 'short' }),
    day: String(stamp.getDate()),
  }
}

export function formatEventDate({ date, time }) {
  if (!date) return 'Date to be announced'

  const stamp = new Date(`${date}T${time ?? '00:00:00'}`)
  if (Number.isNaN(stamp.getTime())) return date

  return stamp.toLocaleString(undefined, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    ...(time ? { hour: 'numeric', minute: '2-digit' } : {}),
  })
}

export function formatTimestamp(value) {
  const stamp = new Date(value)
  if (Number.isNaN(stamp.getTime())) return value

  return stamp.toLocaleString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}
