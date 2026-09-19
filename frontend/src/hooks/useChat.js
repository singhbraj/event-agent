import { useCallback, useState } from 'react'

import { sendChatMessage } from '../api/chat'
import { getSessionId } from '../lib/session'

function createMessage(role, text, { events = [], isError = false } = {}) {
  return { id: crypto.randomUUID(), role, text, events, isError }
}

export function useChat() {
  const [messages, setMessages] = useState([])
  const [isSending, setIsSending] = useState(false)

  const append = useCallback((message) => {
    setMessages((current) => [...current, message])
  }, [])

  const send = useCallback(
    async (rawText) => {
      const text = rawText.trim()
      if (!text || isSending) return

      append(createMessage('user', text))
      setIsSending(true)

      try {
        const reply = await sendChatMessage({
          message: text,
          sessionId: getSessionId(),
        })
        append(createMessage('agent', reply.text, { events: reply.events }))
      } catch (error) {
        append(createMessage('agent', error.message, { isError: true }))
      } finally {
        setIsSending(false)
      }
    },
    [append, isSending],
  )

  return { messages, isSending, send }
}
