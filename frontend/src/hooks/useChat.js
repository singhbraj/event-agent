import { useCallback, useState } from 'react'

import { decideBooking, sendChatMessage } from '../api/chat'
import { getSessionId, startNewSession } from '../lib/session'

function createMessage(
  role,
  text,
  { events = [], isError = false, pendingBooking = null, bookingUrl = null } = {},
) {
  return {
    id: crypto.randomUUID(),
    role,
    text,
    events,
    isError,
    pendingBooking,
    bookingUrl,
    decisionPending: false,
  }
}

export function useChat() {
  const [messages, setMessages] = useState([])
  const [isSending, setIsSending] = useState(false)

  const append = useCallback((message) => {
    setMessages((current) => [...current, message])
  }, [])

  const newChat = useCallback(() => {
    startNewSession()
    setMessages([])
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
        append(
          createMessage('agent', reply.text, {
            events: reply.events,
            pendingBooking: reply.pendingBooking,
            bookingUrl: reply.bookingUrl,
          }),
        )
      } catch (error) {
        append(createMessage('agent', error.message, { isError: true }))
      } finally {
        setIsSending(false)
      }
    },
    [append, isSending],
  )

  const decide = useCallback(
    async (approved) => {
      if (isSending) return

      setMessages((current) =>
        current.map((message) =>
          message.pendingBooking ? { ...message, decisionPending: true } : message,
        ),
      )
      setIsSending(true)

      try {
        const reply = await decideBooking({
          approved,
          sessionId: getSessionId(),
        })
        setMessages((current) =>
          current.map((message) =>
            message.pendingBooking
              ? { ...message, pendingBooking: null, decisionPending: false }
              : message,
          ),
        )
        append(
          createMessage('agent', reply.text, {
            events: reply.events,
            bookingUrl: reply.bookingUrl,
          }),
        )
      } catch (error) {
        setMessages((current) =>
          current.map((message) =>
            message.pendingBooking
              ? { ...message, decisionPending: false }
              : message,
          ),
        )
        append(createMessage('agent', error.message, { isError: true }))
      } finally {
        setIsSending(false)
      }
    },
    [append, isSending],
  )

  return {
    messages,
    isSending,
    send,
    newChat,
    approve: () => decide(true),
    reject: () => decide(false),
  }
}
