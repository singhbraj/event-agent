import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { listTickets } from '../api/tickets'
import { formatTimestamp } from '../lib/date'
import styles from './TicketsPage.module.css'

export default function TicketsPage() {
  const [tickets, setTickets] = useState([])
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    const controller = new AbortController()

    listTickets({ signal: controller.signal })
      .then((items) => {
        setTickets(items)
        setStatus('ready')
      })
      .catch((error) => {
        if (error.name !== 'AbortError') setStatus('error')
      })

    return () => controller.abort()
  }, [])

  return (
    <section className={styles.page}>
      <header className={styles.header}>
        <h2 className={styles.title}>Tickets</h2>
        <p className={styles.subtitle}>Conversations you can reopen.</p>
      </header>

      {status === 'loading' && <p className={styles.state}>Loading tickets…</p>}
      {status === 'error' && (
        <p className={styles.state}>Could not load tickets. Check that the server is running.</p>
      )}
      {status === 'ready' && tickets.length === 0 && (
        <p className={styles.state}>No saved conversations yet. Start one from Chat.</p>
      )}

      <div className={styles.list}>
        {tickets.map((ticket) => (
          <Link
            className={styles.ticket}
            key={ticket.id}
            to={`/tickets/${ticket.id}`}
          >
            <strong>{ticket.title}</strong>
            <span>{formatTimestamp(ticket.updatedAt)}</span>
          </Link>
        ))}
      </div>
    </section>
  )
}
