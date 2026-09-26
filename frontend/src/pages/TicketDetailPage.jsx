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

  return (
    <section className={styles.page}>
      <Link className={styles.back} to="/tickets">
        Back to tickets
      </Link>

      {status === 'loading' && <p className={styles.state}>Loading ticket…</p>}
      {status === 'error' && <p className={styles.state}>Could not load this ticket.</p>}

      {status === 'ready' && (
        <>
          <div className={styles.heading}>
            <h2>{ticket.title}</h2>
            <span>Updated {formatTimestamp(ticket.updatedAt)}</span>
          </div>
          <MessageList messages={ticket.messages} isSending={false} />
        </>
      )}
    </section>
  )
}
