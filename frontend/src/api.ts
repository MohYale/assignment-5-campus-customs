import type { AgentEvent, Cash, RunResult, Ticket } from './types'

export const API = 'http://localhost:8000'

async function read<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  })
  const body = (await response.json().catch(() => ({}))) as { detail?: unknown }
  if (!response.ok) {
    const detail = body.detail
    const message =
      typeof detail === 'string'
        ? detail
        : `The desk could not complete that request (${response.status}).`
    throw new Error(message)
  }
  return body as T
}

export function fetchTickets(): Promise<{ tickets: Ticket[] }> {
  return read('/api/tickets')
}

export function fetchCash(): Promise<Cash> {
  return read('/api/cash')
}

export function fetchEvents(): Promise<{ events: AgentEvent[] }> {
  return read('/api/events?limit=200')
}

export function runTicket(ticketId: number): Promise<RunResult> {
  return read(`/api/tickets/${ticketId}/run`, { method: 'POST' })
}

export function approvePayment(body: {
  kind: string
  ref_id: number
  sku: string
  size: string
  qty: number
}): Promise<{ amount: number; balance: number; detail: string }> {
  return read('/api/approve', { method: 'POST', body: JSON.stringify(body) })
}
