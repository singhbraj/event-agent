import Composer from './components/Composer'
import MessageList from './components/MessageList'
import { useChat } from './hooks/useChat'
import styles from './App.module.css'

export default function App() {
  const { messages, isSending, send } = useChat()

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <h1 className={styles.title}>Event Agent</h1>
      </header>

      <main className={styles.thread}>
        <MessageList messages={messages} isSending={isSending} />
      </main>

      <Composer onSend={send} disabled={isSending} />
    </div>
  )
}
