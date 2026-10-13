// The Krusty Krab line-up: each character with their role, status and latest line.
import { CHARACTER_ART } from './characterArt'
import { CREW, CREW_ORDER, type AgentKey } from '../crew'

export function CrewStage({
  active,
  finished,
  involved,
  lastLine,
  running,
}: {
  active: AgentKey | null
  finished: Set<AgentKey>
  involved: Set<AgentKey>
  lastLine: Partial<Record<AgentKey, string>>
  running: boolean
}) {
  return (
    <section className="panel stage" aria-labelledby="crew-title">
      <header className="panel-head">
        <h2 id="crew-title">
          <span aria-hidden="true">⚓</span> The Crew
        </h2>
        <span className="panel-hint">{running ? 'Live: watch who is talking' : 'Standing by'}</span>
      </header>
      <ol className="crew">
        {CREW_ORDER.map((key) => {
          const m = CREW[key]
          const Art = CHARACTER_ART[key]
          const isActive = running && active === key
          const isDone = finished.has(key)
          const isIdle = !involved.has(key)
          const status = isActive ? 'Talking' : isDone ? 'Done' : involved.has(key) ? 'Waiting' : 'Idle'
          return (
            <li
              key={key}
              className={`member member-${key} ${isActive ? 'is-active' : ''} ${isDone ? 'is-done' : ''} ${
                isIdle ? 'is-idle' : ''
              }`}
              style={{ ['--accent' as string]: m.color, ['--ink' as string]: m.ink }}
            >
              <div className="member-art">
                <Art size={key === 'boss' ? 104 : 92} title={m.character} />
                {isDone && (
                  <span className="member-check" aria-hidden="true">
                    ✓
                  </span>
                )}
              </div>
              <div className="member-name">{m.character}</div>
              <div className="member-role">{m.role}</div>
              <div className={`member-status status-${status.toLowerCase()}`}>
                {isActive && <span className="dot-pulse" aria-hidden="true" />} {status}
              </div>
              {lastLine[key] && (
                <div className={`speech speech-${key}`} aria-live={isActive ? 'polite' : 'off'}>
                  {lastLine[key]}
                </div>
              )}
            </li>
          )
        })}
      </ol>
    </section>
  )
}
