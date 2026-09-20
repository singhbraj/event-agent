import MessageBubble from './MessageBubble'
import styles from './MessageList.module.css'

export default function MessageList({
  messages,
  isSending,
  status,
  onApprove,
  onReject,
}) {
  if (messages.length === 0 && !isSending) {
    return (
      <p className={styles.empty}>
        Ask about live events, for example: concerts in London this weekend.
      </p>
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
        <p className={styles.pending}>{status || 'Searching for events...'}</p>
      )}
    </div>
  )
}
