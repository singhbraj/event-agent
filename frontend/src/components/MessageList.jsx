import MessageBubble from './MessageBubble'
import styles from './MessageList.module.css'

const SUGGESTIONS = [
  'Concerts in London this weekend',
  'Jazz in New York tonight',
  'Comedy shows in Chicago',
  'Festivals in Berlin this month',
]

export default function MessageList({
  messages,
  isSending,
  onApprove,
  onReject,
  onSuggest,
}) {
  const deciding = messages.some((message) => message.decisionPending)

  if (messages.length === 0 && !isSending) {
    if (!onSuggest) {
      return <p className={styles.quiet}>No messages in this conversation.</p>
    }

    return (
      <div className={styles.empty}>
        <p className={styles.kicker}>Ask for a night out</p>
        <h2 className={styles.heading}>What do you want to see?</h2>
        <p className={styles.copy}>
          Concerts, comedy, theatre, or festivals. I’ll find what’s on and
          check with you before any booking.
        </p>
        {onSuggest && (
          <div className={styles.suggestions}>
            {SUGGESTIONS.map((prompt) => (
              <button key={prompt} type="button" onClick={() => onSuggest(prompt)}>
                {prompt}
              </button>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={styles.list}>
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          onApprove={onApprove}
          onReject={onReject}
        />
      ))}
      {isSending && (
        <p className={styles.pending}>
          <span className={styles.dot} aria-hidden="true" />
          {deciding ? 'Confirming your decision…' : 'Looking up events…'}
        </p>
      )}
    </div>
  )
}
