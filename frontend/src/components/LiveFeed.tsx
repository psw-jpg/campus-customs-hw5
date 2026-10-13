// The radio chatter: every step of the run, in each character's own voice and colors.
import { useEffect, useRef } from 'react'
import { CHARACTER_ART } from './characterArt'
import { CREW, type FeedItem } from '../crew'

const KIND_TAG: Record<FeedItem['kind'], string> = {
  task: 'got a task',
  speech: 'says',
  tool: 'used a tool',
  handoff: 'handed off',
  report: 'reports back',
  alert: 'heads up',
  done: 'final call',
}

export function LiveFeed({
  items,
  running,
  ticketId,
}: {
  items: FeedItem[]
  running: boolean
  ticketId: number | null
}) {
  const box = useRef<HTMLOListElement>(null)

  useEffect(() => {
    // Follow new lines, but only if the reader is already near the bottom.
    const el = box.current
    if (el && el.scrollHeight - el.scrollTop - el.clientHeight < 200) el.scrollTop = el.scrollHeight
  }, [items.length])

  return (
    <section className="panel feed" aria-labelledby="feed-title">
      <header className="panel-head">
        <h2 id="feed-title">
          <span aria-hidden="true">📻</span> Kitchen Radio
        </h2>
        <span className="panel-hint">
          {ticketId === null ? 'Pick a ticket' : running ? `Live · ticket #${ticketId}` : `Last run · ticket #${ticketId}`}
        </span>
      </header>

      {items.length === 0 ? (
        <div className="empty">
          <span className="empty-emoji" aria-hidden="true">
            🫧
          </span>
          {ticketId === null
            ? 'Choose an order slip to hear the crew.'
            : running
              ? 'Mr. Krabs is reading the ticket…'
              : 'No run yet for this ticket. Send in the crew!'}
        </div>
      ) : (
        <ol className="lines" ref={box} aria-live="polite" aria-relevant="additions">
          {items.map((it) => {
            const m = it.agent === 'system' ? null : CREW[it.agent]
            const Art = it.agent === 'system' ? null : CHARACTER_ART[it.agent]
            return (
              <li
                key={it.id}
                className={`line line-${it.kind} voice-${it.agent}`}
                style={{
                  ['--accent' as string]: m?.color ?? '#8fb7d9',
                  ['--ink' as string]: m?.ink ?? '#0b2238',
                  marginLeft: `${Math.min(it.depth, 2) * 22}px`,
                }}
              >
                <span className="line-avatar" aria-hidden="true">
                  {Art ? <Art size={34} /> : '🫧'}
                </span>
                <div className="line-body">
                  <div className="line-head">
                    <strong>{m?.character ?? 'System'}</strong>
                    <span className="line-tag">{KIND_TAG[it.kind]}</span>
                    {it.sensitive && <span className={`flag flag-${it.sensitive}`}>{it.sensitive.replace('_', ' ')}</span>}
                    <time>{it.at.slice(11, 19)}</time>
                  </div>
                  <div className="line-text">
                    {it.icon && <span aria-hidden="true">{it.icon} </span>}
                    {it.text}
                  </div>
                  {it.detail && (
                    it.kind === 'tool' ? (
                      <details className="line-detail">
                        <summary>Show tool call</summary>
                        <pre>{it.detail}</pre>
                      </details>
                    ) : (
                      <div className="line-quote">{it.detail}</div>
                    )
                  )}
                </div>
              </li>
            )
          })}
          {running && (
            <li className="line line-typing" aria-hidden="true">
              <span className="typing">
                <i />
                <i />
                <i />
              </span>
            </li>
          )}
        </ol>
      )}
    </section>
  )
}
