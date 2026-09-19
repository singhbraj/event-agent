import Composer from '../components/Composer'
import MessageList from '../components/MessageList'
import { useChat } from '../hooks/useChat'
import styles from './ChatPage.module.css'

export default function ChatPage() {
  const { messages, isSending, send, newChat } = useChat()

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <h2 className={styles.title}>Chat</h2>
        <button
          className={styles.newChat}
          type="button"
          onClick={newChat}
          disabled={isSending}
        >
          New chat
        </button>
      </div>

      <div className={styles.thread}>
        <MessageList messages={messages} isSending={isSending} />
      </div>

      <Composer onSend={send} disabled={isSending} />
    </div>
  )
}
