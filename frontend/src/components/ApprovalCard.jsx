import { formatEventDate } from '../lib/date'
import styles from './ApprovalCard.module.css'

export default function ApprovalCard({ booking, disabled, onApprove, onReject }) {
  const location = [booking.venue, booking.city].filter(Boolean).join(', ')

  return (
    <div className={styles.card}>
      <p className={styles.label}>Continue to Ticketmaster?</p>
      <h3 className={styles.name}>{booking.name}</h3>
      {location && <p className={styles.meta}>{location}</p>}
      <p className={styles.meta}>{formatEventDate(booking)}</p>
      {booking.price && <p className={styles.meta}>{booking.price}</p>}
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
