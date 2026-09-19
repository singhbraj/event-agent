import { getJson } from './client'

export async function listTickets({ signal } = {}) {
  const tickets = await getJson('/tickets', { signal })
  return tickets.map((ticket) => ({
    id: ticket.id,
    title: ticket.title,
    createdAt: ticket.created_at,
    updatedAt: ticket.updated_at,
  }))
}

export async function getTicket(ticketId, { signal } = {}) {
  const ticket = await getJson(
    `/tickets/${encodeURIComponent(ticketId)}`,
    { signal },
  )

  return {
    id: ticket.session_id,
    title: ticket.title,
    createdAt: ticket.created_at,
    updatedAt: ticket.updated_at,
    messages: ticket.messages.map((message) => ({
      id: message.id,
      role: message.role,
      text: message.content,
      events: message.events ?? [],
      createdAt: message.created_at,
    })),
  }
}
