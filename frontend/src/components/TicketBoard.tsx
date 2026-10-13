// The order-slip board: every ticket, its state, and the "send in the crew" button.
import type { Ticket } from '../api'
import { OUTCOME_LABEL, TICKET_LOOK } from '../crew'

function detailLine(t: Ticket) {
  // Agents append dated notes on new lines; the slip shows only the original request.
  if (t.type === 'rent_notice') return `Lease ${t.lease_id} · ${(t.notes ?? '').split('\n')[0]}`
  const item = [t.qty && `${t.qty} ×`, t.sku, t.size && `size ${t.size}`].filter(Boolean).join(' ')
  return item || t.notes || ''
}

export function TicketBoard({
  tickets,
  selectedId,
  runningId,
  onSelect,
  onRun,
  backendDown,
}: {
  tickets: Ticket[]
  selectedId: number | null
  runningId: number | null
  onSelect: (id: number) => void
  onRun: (id: number) => void
  backendDown: boolean
}) {
  return (
    <section className="panel board" aria-labelledby="board-title">
      <header className="panel-head">
        <h2 id="board-title">
          <span aria-hidden="true">🍔</span> Order Board
        </h2>
        <span className="panel-hint">Pick a ticket, then send in the crew</span>
      </header>

      <ul className="slips" role="listbox" aria-label="Tickets">
        {tickets.map((t, i) => {
          const look = TICKET_LOOK[t.type] ?? { emoji: '🎫', label: t.type }
          const selected = t.id === selectedId
          const running = t.id === runningId || t.state === 'running'
          const state = running ? 'running' : t.state
          return (
            <li key={t.id} style={{ ['--tilt' as string]: `${[-1.2, 0.8, -0.6][i % 3]}deg` }}>
              <button
                role="option"
                aria-selected={selected}
                className={`slip slip-${state} ${selected ? 'is-selected' : ''}`}
                onClick={() => onSelect(t.id)}
              >
                <span className="slip-pin" aria-hidden="true" />
                <span className="slip-top">
                  <span className="slip-no">#{t.id}</span>
                  <span className={`state-pill state-${state}`}>
                    {state === 'running' ? (
                      <>
                        <span className="dot-pulse" aria-hidden="true" /> Crew working
                      </>
                    ) : state === 'resolved' ? (
                      '✓ Resolved'
                    ) : (
                      'Open'
                    )}
                  </span>
                </span>
                <span className="slip-title">
                  <span aria-hidden="true">{look.emoji}</span> {t.subject}
                </span>
                <span className="slip-meta">
                  {look.label} · from <strong>{t.requester}</strong>
                </span>
                <span className="slip-detail">{detailLine(t)}</span>
                {state === 'resolved' && (
                  <span className={`outcome outcome-${t.status}`}>
                    Outcome: {OUTCOME_LABEL[t.status] ?? t.status}
                  </span>
                )}
                {state === 'resolved' && <span className="stamp" aria-hidden="true">DONE</span>}
              </button>
            </li>
          )
        })}
      </ul>

      {selectedId !== null && (
        <button
          className="btn btn-run"
          onClick={() => onRun(selectedId)}
          disabled={runningId !== null || backendDown}
          aria-describedby="run-help"
        >
          {runningId === selectedId ? (
            <>
              <span className="spinner" aria-hidden="true" /> Crew is on it…
            </>
          ) : runningId !== null ? (
            'Crew busy on another ticket'
          ) : (
            <>🦀 Send in the crew for #{selectedId}</>
          )}
        </button>
      )}
      <p id="run-help" className="fine-print">
        Runs use gpt-6-luna. Mr. Krabs reads the ticket and delegates; payments wait for your OK.
      </p>
    </section>
  )
}
