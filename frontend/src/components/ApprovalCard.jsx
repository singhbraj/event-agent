import { eventDateBadge, formatEventDate } from '../lib/date'
import styles from './ApprovalCard.module.css'

export default function ApprovalCard({ booking, disabled, onApprove, onReject }) {
  const location = [booking.venue, booking.city].filter(Boolean).join(', ')
  const badge = eventDateBadge(booking.date)

  return (
    <div className={styles.card}>
      <div className={styles.heading}>
        {badge && (
          <div className={styles.badge} aria-hidden="true">
            <span>{badge.month}</span>
            <strong>{badge.day}</strong>
          </div>
        )}
        <div>
          <p className={styles.label}>Approve this booking</p>
          <h3 className={styles.name}>{booking.name}</h3>
        </div>
      </div>
      {location && <p className={styles.meta}>{location}</p>}
      <p className={styles.meta}>{formatEventDate(booking)}</p>
      {booking.price && <p className={styles.price}>{booking.price}</p>}
      <div className={styles.actions}>
        <button
          className={styles.approve}
          type="button"
          disabled={disabled}
          onClick={onApprove}
        >
          Approve
        </button>
        <button
          className={styles.reject}
          type="button"
          disabled={disabled}
          onClick={onReject}
        >
          Reject
        </button>
      </div>
    </div>
  )
}
