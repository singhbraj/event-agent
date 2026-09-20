import { formatEventDate } from '../lib/date'
import styles from './EventCard.module.css'

export default function EventCard({ event }) {
  const location = [event.venue, event.city].filter(Boolean).join(', ')

  return (
    <article className={styles.card}>
      <h3 className={styles.name}>{event.name}</h3>
      {location && <p className={styles.meta}>{location}</p>}
      {event.address && <p className={styles.meta}>{event.address}</p>}
      <p className={styles.meta}>{formatEventDate(event)}</p>
      {event.price && <p className={styles.meta}>{event.price}</p>}
      {event.info && <p className={styles.info}>{event.info}</p>}
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
