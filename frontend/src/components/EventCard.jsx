import { formatEventDate } from '../lib/date'
import styles from './EventCard.module.css'

export default function EventCard({ event }) {
  const location = [event.venue, event.city].filter(Boolean).join(', ')

  return (
    <article className={styles.card}>
      <h3 className={styles.name}>{event.name}</h3>
      {location && <p className={styles.meta}>{location}</p>}
      <p className={styles.meta}>{formatEventDate(event)}</p>
      {event.url && (
        <a
          className={styles.link}
          href={event.url}
          target="_blank"
          rel="noreferrer"
        >
          View tickets
        </a>
      )}
    </article>
  )
}
