import { eventDateBadge, formatEventDate } from '../lib/date'
import styles from './EventCard.module.css'

export default function EventCard({ event }) {
  const location = [event.venue, event.city].filter(Boolean).join(', ')
  const badge = eventDateBadge(event.date)

  return (
    <article className={styles.card}>
      <div className={styles.badge} aria-hidden="true">
        {badge ? (
          <>
            <span>{badge.month}</span>
            <strong>{badge.day}</strong>
          </>
        ) : (
          <span className={styles.tba}>TBA</span>
        )}
      </div>
      <div className={styles.body}>
        <div className={styles.titleRow}>
          <h3 className={styles.name}>{event.name}</h3>
          {event.genre && <span className={styles.genre}>{event.genre}</span>}
        </div>
        {location && <p className={styles.meta}>{location}</p>}
        {event.address && <p className={styles.meta}>{event.address}</p>}
        <div className={styles.footer}>
          <p className={styles.meta}>{formatEventDate(event)}</p>
          {event.price && <p className={styles.price}>{event.price}</p>}
        </div>
        {event.info && <p className={styles.info}>{event.info}</p>}
      </div>
    </article>
  )
}
