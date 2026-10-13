// Full-width parades that play after a human approves money going out:
// Plankton dashes across leaving bubbles (payments), Gary slides across leaving slime (purchases).
import { useMemo } from 'react'
import { Gary, Plankton } from './Characters'
import { money } from '../api'

export type Parade = { kind: 'payment' | 'purchase'; amount: number; label: string; key: number }

export function Celebration({ parade }: { parade: Parade | null }) {
  const bubbles = useMemo(
    () =>
      Array.from({ length: 26 }, (_, i) => ({
        left: 2 + i * 3.8,
        size: 10 + ((i * 17) % 22),
        delay: 0.1 + i * 0.12,
        drift: ((i * 23) % 40) - 20,
      })),
    [],
  )
  if (!parade) return null

  return (
    <div className={`parade parade-${parade.kind}`} key={parade.key} role="status" aria-live="assertive">
      <div className="parade-banner">
        {parade.kind === 'payment' ? '💸 Payment approved' : '🛒 Purchase approved'} · {parade.label} ·{' '}
        <strong>{money(parade.amount)}</strong>
      </div>

      {parade.kind === 'payment' ? (
        <>
          {bubbles.map((b, i) => (
            <span
              key={i}
              className="trail-bubble"
              style={{
                left: `${b.left}%`,
                width: b.size,
                height: b.size,
                animationDelay: `${b.delay}s`,
                ['--drift' as string]: `${b.drift}px`,
              }}
            />
          ))}
          <div className="runner plankton-runner">
            <Plankton size={110} title="Plankton dashing across the screen" />
            <span className="runner-quip">"I'll get that formula yet!"</span>
          </div>
        </>
      ) : (
        <>
          <div className="slime-trail" />
          <div className="runner gary-runner">
            <Gary size={150} title="Gary the snail sliding across the screen" />
            <span className="runner-quip">"Meow."</span>
          </div>
        </>
      )}
    </div>
  )
}
