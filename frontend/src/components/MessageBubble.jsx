import ApprovalCard from './ApprovalCard'
import EventCard from './EventCard'
import styles from './MessageBubble.module.css'

export default function MessageBubble({ message, onApprove, onReject }) {
  if (message.isError) {
    return (
      <div className={styles.error}>
        <p className={styles.text}>{message.text}</p>
      </div>
    )
  }

  if (message.role === 'user') {
    return (
      <div className={styles.user}>
        <p className={styles.text}>{message.text}</p>
      </div>
    )
  }

  return (
    <article className={styles.agent}>
      {message.text && <p className={styles.text}>{message.text}</p>}
      {message.events?.length > 0 && (
        <div className={styles.events}>
          {message.events.map((event, index) => (
            <EventCard key={`${event.name}-${event.date}-${index}`} event={event} />
          ))}
        </div>
      )}
      {message.bookingUrl && (
        <a
          className={styles.link}
          href={message.bookingUrl}
          target="_blank"
          rel="noreferrer"
        >
          Continue to Ticketmaster
        </a>
      )}
      {message.pendingBooking && (
        <ApprovalCard
          booking={message.pendingBooking}
          disabled={message.decisionPending}
          onApprove={() => onApprove?.()}
          onReject={() => onReject?.()}
        />
      )}
    </article>
  )
}
