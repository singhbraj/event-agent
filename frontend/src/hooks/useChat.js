import { useCallback, useState } from 'react'

import { decideBooking, streamChatMessage } from '../api/chat'
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

function describeStatus(status) {
  if (status.stage === 'tool') {
    if (status.tool === 'get_event_details_tool') return 'Loading event details...'
    if (status.tool === 'proceed_to_booking') return 'Preparing booking...'
    return 'Searching for events...'
  }
  if (status.stage === 'writing') return 'Writing the answer...'
  return 'Thinking...'
}

export function useChat() {
  const [messages, setMessages] = useState([])
  const [isSending, setIsSending] = useState(false)
  const [status, setStatus] = useState('')

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
      setStatus('Thinking...')

      try {
        const reply = await streamChatMessage({
          message: text,
          sessionId: getSessionId(),
          onStatus: (update) => setStatus(describeStatus(update)),
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
        setStatus('')
      }
    },
    [append, isSending],
  )

  const decide = useCallback(
    async (approved, actionId) => {
      if (isSending) return

      setMessages((current) =>
        current.map((message) =>
          message.pendingBooking?.action_id === actionId
            ? { ...message, decisionPending: true }
            : message,
        ),
      )
      setIsSending(true)

      try {
        const reply = await decideBooking({
          approved,
          sessionId: getSessionId(),
          actionId,
        })
        setMessages((current) =>
          current.map((message) =>
            message.pendingBooking?.action_id === actionId
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
            message.pendingBooking?.action_id === actionId
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
    status,
    send,
    newChat,
    approve: (actionId) => decide(true, actionId),
    reject: (actionId) => decide(false, actionId),
  }
}
