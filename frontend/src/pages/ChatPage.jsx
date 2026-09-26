import { useEffect, useRef } from 'react'

import Composer from '../components/Composer'
import MessageList from '../components/MessageList'
import { useChat } from '../hooks/useChat'
import styles from './ChatPage.module.css'

export default function ChatPage() {
  const { messages, isSending, send, newChat, approve, reject } = useChat()
  const threadRef = useRef(null)

  useEffect(() => {
    const thread = threadRef.current
    if (!thread) return
    thread.scrollTop = thread.scrollHeight
  }, [messages, isSending])

  return (
    <div className={styles.page}>
      {messages.length > 0 && (
        <div className={styles.toolbar}>
          <button
            className={styles.newChat}
            type="button"
            onClick={newChat}
            disabled={isSending}
          >
            New chat
          </button>
        </div>
      )}

      <div className={styles.thread} ref={threadRef} aria-busy={isSending}>
        <MessageList
          messages={messages}
          isSending={isSending}
          onApprove={approve}
          onReject={reject}
          onSuggest={send}
        />
      </div>

      <Composer onSend={send} disabled={isSending} />
    </div>
  )
}
