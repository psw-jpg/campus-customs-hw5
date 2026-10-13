// After a run: Mr. Krabs' final call plus a short card for every crew member who worked the ticket.
import { CHARACTER_ART } from './characterArt'
import { CREW, CREW_ORDER, OUTCOME_LABEL, isAgent, toolLabel } from '../crew'
import type { TicketSummary } from '../api'

export function ShiftReport({ summary, running }: { summary: TicketSummary | null; running: boolean }) {
  const agents = (summary?.agents ?? [])
    .filter((a) => isAgent(a.agent))
    .sort((a, b) => CREW_ORDER.indexOf(a.agent as never) - CREW_ORDER.indexOf(b.agent as never))
  const d = summary?.decision

  return (
    <section className="panel report" aria-labelledby="report-title">
      <header className="panel-head">
        <h2 id="report-title">
          <span aria-hidden="true">📝</span> Shift Report
        </h2>
        {summary?.run_id && <span className="panel-hint">{summary.run_id}</span>}
      </header>

      {!summary || agents.length === 0 ? (
        <div className="empty small">
          <span className="empty-emoji" aria-hidden="true">
            🍍
          </span>
          {running ? 'The report prints when the crew finishes.' : 'Run a ticket to see what each crew member did.'}
        </div>
      ) : (
        <>
          {d && (
            <div className={`verdict verdict-${d.status}`}>
              <div className="verdict-top">
                <span className="verdict-label">Mr. Krabs' final call</span>
                <span className={`outcome outcome-${d.status}`}>{OUTCOME_LABEL[d.status] ?? d.status}</span>
              </div>
              <p className="verdict-summary">{d.summary}</p>
              <details>
                <summary>Why</summary>
                <p>{d.reasoning}</p>
              </details>
            </div>
          )}
          <ul className="cards">
            {agents.map((a) => {
              const key = a.agent as keyof typeof CREW
              const m = CREW[key]
              const Art = CHARACTER_ART[key]
              const said = a.summaries[a.summaries.length - 1]
              return (
                <li
                  key={a.agent}
                  className="card"
                  style={{ ['--accent' as string]: m.color, ['--ink' as string]: m.ink }}
                >
                  <div className="card-head">
                    <Art size={40} />
                    <div>
                      <strong>{m.character}</strong>
                      <span>{m.role}</span>
                    </div>
                    <span className="card-tokens" title="Model tokens used">
                      {a.tokens.toLocaleString()} tok
                    </span>
                  </div>
                  {said && <p className="card-said">{said}</p>}
                  <div className="chips">
                    {a.tools.map((t) => {
                      const [icon, label] = toolLabel(t)
                      return (
                        <span key={t} className="chip" title={t}>
                          {icon} {label}
                        </span>
                      )
                    })}
                    {a.delegated_to.map((t) => (
                      <span key={t} className="chip chip-handoff">
                        📣 {isAgent(t) ? CREW[t].character : t}
                      </span>
                    ))}
                  </div>
                </li>
              )
            })}
          </ul>
        </>
      )}
    </section>
  )
}
