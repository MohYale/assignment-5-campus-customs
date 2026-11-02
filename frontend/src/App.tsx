import { useEffect, useMemo, useState } from 'react'
import { approvePayment, fetchCash, fetchEvents, fetchTickets, runTicket } from './api'
import { agentLabel, LamassuYard } from './lamassu'
import type { AgentEvent, Cash, PaymentDraft, Ticket } from './types'

function money(amount: number | null): string {
  if (amount == null || Number.isNaN(amount)) return '—'
  return amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}

function eventKey(event: AgentEvent): string {
  return `${event.run_id}|${event.step}|${event.agent}|${event.time}`
}

function purchaseDraft(ticket: Ticket, qty: number): PaymentDraft {
  const amount = ticket.unit_cost == null ? null : Math.round(ticket.unit_cost * qty * 100) / 100
  return {
    kind: 'purchase_order',
    ref_id: 0,
    sku: ticket.sku ?? '',
    size: ticket.size ?? '',
    qty,
    title: 'Purchase order',
    detail: `${qty} × ${ticket.item_name ?? ticket.sku}, size ${ticket.size ?? ''}`,
    amount,
  }
}

function rentDraft(ticket: Ticket): PaymentDraft {
  return {
    kind: 'rent_payment',
    ref_id: ticket.lease_id ?? 0,
    sku: '',
    size: '',
    qty: 0,
    title: 'Rent payment',
    detail: ticket.space_name ?? `Lease ${ticket.lease_id}`,
    amount: ticket.monthly_rent,
  }
}

function invoiceDraft(ticket: Ticket): PaymentDraft {
  return {
    kind: 'invoice_payment',
    ref_id: ticket.invoice_id ?? 0,
    sku: '',
    size: '',
    qty: 0,
    title: 'Invoice payment',
    detail: `Invoice ${ticket.invoice_id}`,
    amount: ticket.invoice_amount,
  }
}

function preparedDraft(ticket: Ticket): PaymentDraft | null {
  if (ticket.lease_id && !ticket.sku) return rentDraft(ticket)
  if (ticket.sku && ticket.shortfall && ticket.shortfall > 0) return purchaseDraft(ticket, ticket.shortfall)
  if (ticket.invoice_id) return invoiceDraft(ticket)
  return null
}

function askedDraft(ticket: Ticket, events: AgentEvent[]): PaymentDraft | null {
  const asks = events.filter(
    (event) =>
      event.needs_human_approval &&
      (event.approval_kind === 'payment' || event.approval_kind === 'purchase_order'),
  )
  const last = asks[asks.length - 1]
  if (!last) return null
  if (last.approval_kind === 'purchase_order' && ticket.sku) {
    const qty = ticket.shortfall && ticket.shortfall > 0 ? ticket.shortfall : (ticket.qty ?? 0)
    if (qty > 0) return purchaseDraft(ticket, qty)
  }
  if (last.approval_kind === 'payment' && ticket.lease_id) return rentDraft(ticket)
  if (last.approval_kind === 'payment' && ticket.invoice_id) return invoiceDraft(ticket)
  return null
}

function clip(text: string, max = 280): string {
  const clean = text.replace(/\s+/g, ' ').trim()
  if (clean.length <= max) return clean
  return `${clean.slice(0, max - 1)}…`
}

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [cash, setCash] = useState<Cash | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [events, setEvents] = useState<AgentEvent[]>([])
  const [runningId, setRunningId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [runNote, setRunNote] = useState('')
  const [approving, setApproving] = useState(false)
  const [paidNote, setPaidNote] = useState('')
  const [postedKey, setPostedKey] = useState('')
  const [balanceFell, setBalanceFell] = useState(false)

  const selected = tickets.find((ticket) => ticket.id === selectedId) ?? null

  async function loadDesk() {
    const [ticketBody, cashBody] = await Promise.all([fetchTickets(), fetchCash()])
    setTickets(ticketBody.tickets)
    setCash(cashBody)
    setSelectedId((current) => current ?? ticketBody.tickets[0]?.id ?? null)
  }

  useEffect(() => {
    loadDesk().catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : 'The desk could not reach the backend.')
    })
  }, [])

  useEffect(() => {
    if (selectedId == null || runningId !== null) return
    let ignore = false
    fetchEvents()
      .then((body) => {
        if (ignore) return
        const mine = body.events.filter((event) => event.ticket_id === selectedId)
        const lastRun = mine[mine.length - 1]?.run_id
        setEvents(lastRun ? mine.filter((event) => event.run_id === lastRun) : [])
      })
      .catch(() => undefined)
    return () => {
      ignore = true
    }
  }, [selectedId, runningId])

  async function startTeam() {
    if (!selected || runningId !== null) return
    setError('')
    setRunNote('')
    setPaidNote('')
    setEvents([])
    const prior = await fetchEvents()
    const seen = new Set(prior.events.filter((event) => event.ticket_id === selected.id).map(eventKey))
    setRunningId(selected.id)
    let timer = 0
    const pull = async () => {
      const body = await fetchEvents()
      setEvents(body.events.filter((event) => event.ticket_id === selected.id && !seen.has(eventKey(event))))
    }
    timer = window.setInterval(() => {
      pull().catch(() => undefined)
    }, 1200)
    try {
      const result = await runTicket(selected.id)
      await pull()
      await loadDesk()
      const finished = result.resolved || result.status === 'resolved'
      setRunNote(
        finished
          ? `Ticket ${selected.id} is resolved. ${clip(result.summary || '', 220)}`
          : clip(result.summary || 'The run finished without marking the ticket resolved.', 240),
      )
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : 'The team run failed.')
    } finally {
      window.clearInterval(timer)
      setRunningId(null)
    }
  }

  async function approve(draft: PaymentDraft) {
    if (approving) return
    setApproving(true)
    setError('')
    const before = cash?.balance ?? null
    try {
      const result = await approvePayment({
        kind: draft.kind,
        ref_id: draft.ref_id,
        sku: draft.sku,
        size: draft.size,
        qty: draft.qty,
      })
      setCash((current) => (current ? { ...current, balance: result.balance } : current))
      setBalanceFell(before != null && result.balance < before)
      setPostedKey(`${draft.kind}:${draft.ref_id}:${draft.sku}:${draft.qty}`)
      setPaidNote(`Paid ${money(result.amount)}. Checking is now ${money(result.balance)}.`)
      window.setTimeout(() => setBalanceFell(false), 2500)
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : 'The payment was not posted.')
    } finally {
      setApproving(false)
    }
  }

  const latest = events[events.length - 1] ?? null
  const activeAgent = runningId !== null ? (latest?.agent ?? 'boss') : (latest?.agent ?? null)
  const litAgents = useMemo(() => [...new Set(events.map((event) => event.agent))], [events])
  const edges = useMemo(
    () =>
      events
        .filter((event) => event.caller && event.agent)
        .map((event) => ({ from: event.caller as string, to: event.agent })),
    [events],
  )
  const latestEdge = latest?.caller && latest.agent ? { from: latest.caller, to: latest.agent } : null
  const request = selected ? askedDraft(selected, events) ?? preparedDraft(selected) : null
  const asked = selected ? askedDraft(selected, events) !== null : false
  const messageAsk = [...events].reverse().find((event) => event.approval_kind === 'customer_message' && event.needs_human_approval)

  const summaries = useMemo(() => {
    const order = ['boss', 'inventory', 'accounting', 'facilities', 'customer_service']
    return order
      .map((agent) => {
        const steps = events.filter((event) => event.agent === agent)
        if (steps.length === 0) return null
        const last = steps[steps.length - 1]
        const tools = [...new Set(steps.flatMap((step) => step.tools))]
        return { agent, said: last.said, tools, steps: steps.length }
      })
      .filter((row): row is { agent: string; said: string; tools: string[]; steps: number } => row !== null)
  }, [events])

  return (
    <div className="page">
      <header className="mast">
        <img
          className="dan"
          src="/handsome-dan.jpg"
          alt="The original Handsome Dan, a bulldog photographed in profile around 1889"
        />
        <div className="mast-copy">
          <p className="eyebrow">Yale · Campus Customs</p>
          <h1>The agent desk</h1>
          <p>Pick a ticket, watch Splinter and the turtles work it, and approve any payment yourself.</p>
        </div>
        <img
          className="dan live"
          src="/handsome-dan-kingman.jpg"
          alt="Handsome Dan XIX, Kingman, the Yale bulldog, sitting on Cross Campus"
        />
        <div className={balanceFell ? 'cash down' : 'cash'}>
          <span>Checking</span>
          <strong>{cash ? money(cash.balance) : '—'}</strong>
          <small>{cash?.date ? `as of ${cash.date}` : 'campus_customs_new.db'}</small>
        </div>
      </header>

      <section className="photos" aria-label="Yale campus">
        <figure>
          <img src="/harkness.jpg" alt="Harkness Tower rising above the Yale campus in stone Gothic" />
          <figcaption>Harkness Tower</figcaption>
        </figure>
        <figure>
          <img src="/evans.jpg" alt="Evans Hall, the Yale School of Management, seen from the front court" />
          <figcaption>Evans Hall</figcaption>
        </figure>
        <figure>
          <img src="/pierson.jpg" alt="The stone gate of Pierson College at Yale" />
          <figcaption>Pierson College</figcaption>
        </figure>
      </section>

      {error ? <p className="banner bad">{error}</p> : null}
      {runNote ? <p className="banner">{runNote}</p> : null}

      <main className="board">
        <section className="tickets" aria-label="Open tickets">
          <h2>Tickets</h2>
          {tickets.map((ticket) => {
            const working = runningId === ticket.id
            return (
              <button
                key={ticket.id}
                type="button"
                className={ticket.id === selectedId ? 'ticket on' : 'ticket'}
                aria-pressed={ticket.id === selectedId}
                onClick={() => {
                  setSelectedId(ticket.id)
                  setRunNote('')
                  setPaidNote('')
                  setPostedKey('')
                }}
              >
                <span className="tid">{ticket.id}</span>
                <span className={ticket.resolved ? 'pill done' : working ? 'pill work' : 'pill'}>
                  {working ? 'Working' : ticket.resolved ? 'Resolved' : 'Open'}
                </span>
                <strong>{ticket.requester}</strong>
                <em>{ticket.type.replaceAll('_', ' ')}</em>
                <p>{ticket.subject}</p>
                {ticket.sku ? (
                  <small>
                    {ticket.item_name ?? ticket.sku} · size {ticket.size} · on hand {ticket.on_hand ?? 0}
                    {ticket.shortfall ? ` · short ${ticket.shortfall}` : ''}
                  </small>
                ) : (
                  <small>{ticket.space_name ?? 'Shop lease'}</small>
                )}
              </button>
            )
          })}
          <button type="button" className="start" disabled={!selected || runningId !== null} onClick={() => startTeam()}>
            {runningId !== null ? 'The team is working…' : selected?.resolved ? 'Run the team again' : 'Start the team'}
          </button>
        </section>

        <section className="stage">
          <div className="stage-head">
            <div>
              <h2>Splinter’s team</h2>
              <p>
                {latest
                  ? `${agentLabel(latest.agent)} is ${runningId ? 'speaking' : 'the last voice'}${
                      latest.caller ? `, called by ${agentLabel(latest.caller)}` : ''
                    }.`
                  : 'Splinter stands above the four turtles. A highlighted turtle is the one speaking, and a lit line is the handoff.'}
              </p>
            </div>
          </div>
          <LamassuYard activeAgent={activeAgent} litAgents={litAgents} edges={edges} latest={latestEdge} />

          <div className="work">
            <div>
              <h2>Thought chain</h2>
              {events.length === 0 ? (
                <p className="empty">
                  {runningId
                    ? 'Waiting for the first step. Each thought, tool, and reply will land here as the audit is written.'
                    : 'Start a ticket to watch the chain. Steps stay in the order the agents took them.'}
                </p>
              ) : (
                <ol className="chain">
                  {events.map((event) => (
                    <li key={eventKey(event)} className={event === latest ? 'step on' : 'step'}>
                      <header>
                        <span>Step {event.step}</span>
                        <strong>{agentLabel(event.agent)}</strong>
                        {event.caller ? <em>called by {agentLabel(event.caller)}</em> : <em>opened the ticket</em>}
                        {event.final_call ? <b>Final call</b> : null}
                      </header>
                      {event.thoughts.map((thought, index) => (
                        <p key={`${eventKey(event)}-thought-${index}`} className="thought">
                          {thought}
                        </p>
                      ))}
                      {event.said ? <p className="said">{event.said}</p> : null}
                      {event.tools.length > 0 ? (
                        <ul className="tools">
                          {event.tools.map((tool, index) => (
                            <li key={`${tool}-${index}`}>{tool}</li>
                          ))}
                        </ul>
                      ) : null}
                    </li>
                  ))}
                </ol>
              )}
            </div>

            <div className="side">
              <h2>What each agent did</h2>
              {summaries.length === 0 ? (
                <p className="empty">A short summary for each agent appears here once that agent has spoken.</p>
              ) : (
                <ul className="sums">
                  {summaries.map((row) => (
                    <li key={row.agent}>
                      <strong>{agentLabel(row.agent)}</strong>
                      <p>{clip(row.said || 'No reply text on the last step.')}</p>
                      {row.tools.length > 0 ? <small>{row.tools.join(' · ')}</small> : null}
                    </li>
                  ))}
                </ul>
              )}

              <article className={asked ? 'approve asked' : 'approve'}>
                <h2>{asked ? 'An agent asked you to approve this' : 'Human approval'}</h2>
                {request && selected ? (
                  <>
                    <p className="approve-title">{request.title}</p>
                    <p>{request.detail}</p>
                    <p className="approve-amount">{money(request.amount)}</p>
                    <button
                      type="button"
                      disabled={
                        approving ||
                        runningId !== null ||
                        postedKey === `${request.kind}:${request.ref_id}:${request.sku}:${request.qty}`
                      }
                      onClick={() => approve(request)}
                    >
                      {approving ? 'Posting…' : `Approve ${money(request.amount)}`}
                    </button>
                    <small>
                      {asked
                        ? 'The team only prepared this. Posting it is what changes checking.'
                        : 'Prepared for this ticket. The button is the human step that changes checking. It is marked when an agent asks.'}
                    </small>
                  </>
                ) : (
                  <p className="empty">This ticket has no payment or purchase ready to approve.</p>
                )}
                {paidNote ? <p className="paid">{paidNote}</p> : null}
                {messageAsk ? (
                  <p className="draft-note">
                    Customer service prepared a message. It was not sent. {clip(messageAsk.said, 180)}
                  </p>
                ) : null}
              </article>
            </div>
          </div>
        </section>
      </main>

      <footer>
        <p>
          Harkness Tower, Ad Meskens, CC BY-SA 3.0. Evans Hall, Nick Allen, CC BY-SA 3.0. Pierson College gate, Emilie
          Foyer, CC BY-SA 3.0. Handsome Dan XIX, Joeshmonobody, CC BY-SA 4.0. Original Handsome Dan, Pach Brothers,
          public domain. Photographs via Wikimedia Commons.
        </p>
      </footer>
    </div>
  )
}
