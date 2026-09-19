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
