import { useCallback, useState } from 'react'

import { streamChatMessage } from '../api/chat'
import { getSessionId, startNewSession } from '../lib/session'

function createMessage(role, text, { events = [], isError = false } = {}) {
  return { id: crypto.randomUUID(), role, text, events, isError }
}

function describeStatus(status) {
  if (status.stage === 'tool') {
    return status.tool === 'get_event_details_tool'
      ? 'Loading event details...'
      : 'Searching for events...'
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
        append(createMessage('agent', reply.text, { events: reply.events }))
      } catch (error) {
        append(createMessage('agent', error.message, { isError: true }))
      } finally {
        setIsSending(false)
        setStatus('')
      }
    },
    [append, isSending],
  )

  return { messages, isSending, status, send, newChat }
}
