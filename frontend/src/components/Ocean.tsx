// Bikini Bottom backdrop: sun rays, drifting bubbles, sea flowers and sand.
import { useMemo } from 'react'

export function Ocean() {
  const bubbles = useMemo(
    () =>
      Array.from({ length: 22 }, (_, i) => ({
        left: (i * 37) % 100,
        size: 6 + ((i * 13) % 18),
        delay: (i * 1.7) % 14,
        duration: 12 + ((i * 7) % 12),
      })),
    [],
  )
  const flowers = useMemo(
    () =>
      Array.from({ length: 9 }, (_, i) => ({
        left: 4 + i * 11.5,
        top: 6 + ((i * 29) % 70),
        size: 70 + ((i * 41) % 90),
        hue: ['#7ad3ff', '#b7f0a3', '#ffd0e8', '#fff3a8', '#c9b6ff'][i % 5],
        rot: (i * 47) % 360,
      })),
    [],
  )
  return (
    <div className="ocean" aria-hidden="true">
      <div className="rays" />
      {flowers.map((f, i) => (
        <svg
          key={i}
          className="sea-flower"
          viewBox="0 0 100 100"
          style={{ left: `${f.left}%`, top: `${f.top}%`, width: f.size, transform: `rotate(${f.rot}deg)` }}
        >
          {[0, 72, 144, 216, 288].map((r) => (
            <ellipse key={r} cx="50" cy="26" rx="15" ry="24" fill={f.hue} transform={`rotate(${r} 50 50)`} />
          ))}
          <circle cx="50" cy="50" r="12" fill={f.hue} />
        </svg>
      ))}
      {bubbles.map((b, i) => (
        <span
          key={i}
          className="bubble"
          style={{
            left: `${b.left}%`,
            width: b.size,
            height: b.size,
            animationDelay: `${b.delay}s`,
            animationDuration: `${b.duration}s`,
          }}
        />
      ))}
      <div className="sand" />
    </div>
  )
}
