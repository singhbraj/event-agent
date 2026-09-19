import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { getTicket } from '../api/tickets'
import MessageList from '../components/MessageList'
import { formatTimestamp } from '../lib/date'
import styles from './TicketDetailPage.module.css'

export default function TicketDetailPage() {
  const { ticketId } = useParams()
  const [ticket, setTicket] = useState(null)
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    const controller = new AbortController()

    getTicket(ticketId, { signal: controller.signal })
      .then((item) => {
        setTicket(item)
        setStatus('ready')
      })
      .catch((error) => {
        if (error.name !== 'AbortError') setStatus('error')
      })

    return () => controller.abort()
  }, [ticketId])

  if (status === 'loading') return <p>Loading ticket...</p>
  if (status === 'error') return <p>Could not load this ticket.</p>

  return (
    <section>
      <Link className={styles.back} to="/tickets">
        Back to tickets
      </Link>
      <div className={styles.heading}>
        <h2>{ticket.title}</h2>
        <span>Updated {formatTimestamp(ticket.updatedAt)}</span>
      </div>
      <MessageList messages={ticket.messages} isSending={false} />
    </section>
  )
}
