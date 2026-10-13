// Mr. Krabs' treasure chest: the live checking balance. Counts down smoothly
// when money leaves and floats the amount that just went out.
import { useEffect, useRef, useState } from 'react'
import { money } from '../api'

export function CashChest({ balance, date, error }: { balance: number | null; date?: string; error?: boolean }) {
  const [shown, setShown] = useState<number | null>(balance)
  const [delta, setDelta] = useState<{ amount: number; key: number } | null>(null)
  const prev = useRef<number | null>(balance)

  useEffect(() => {
    if (balance === null) return
    const from = prev.current ?? balance
    prev.current = balance
    if (from === balance) {
      setShown(balance)
      return
    }
    setDelta({ amount: balance - from, key: Date.now() })
    const start = performance.now()
    const dur = 1400
    let raf = 0
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / dur)
      const eased = 1 - Math.pow(1 - p, 3)
      setShown(from + (balance - from) * eased)
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [balance])

  return (
    <div className="chest" aria-live="polite">
      {delta && <span className="chest-flash" key={`flash-${delta.key}`} aria-hidden="true" />}
      <div className="chest-icon" aria-hidden="true">
        <svg viewBox="0 0 64 52" width="54">
          <rect x="4" y="20" width="56" height="28" rx="4" fill="#9b5b22" stroke="#4d2a0a" strokeWidth="2" />
          <path d="M4 22 q28 -26 56 0" fill="#b8742f" stroke="#4d2a0a" strokeWidth="2" />
          <rect x="4" y="24" width="56" height="5" fill="#e3b341" />
          <rect x="27" y="26" width="10" height="12" rx="2" fill="#e3b341" stroke="#4d2a0a" />
          <circle cx="16" cy="16" r="5" fill="#ffd84a" stroke="#b8860b" />
          <circle cx="46" cy="14" r="4" fill="#ffd84a" stroke="#b8860b" />
          <circle cx="32" cy="10" r="5" fill="#ffd84a" stroke="#b8860b" />
        </svg>
      </div>
      <div>
        <div className="chest-label">Checking balance</div>
        <div className="chest-amount">{error ? '—' : shown === null ? '…' : money(shown)}</div>
        <div className="chest-sub">{date ? `as of shop date ${date}` : 'cash only goes out'}</div>
      </div>
      {delta && delta.amount !== 0 && (
        <span className={`chest-delta ${delta.amount < 0 ? 'out' : 'in'}`} key={`delta-${delta.key}`}>
          {delta.amount < 0 ? '−' : '+'}
          {money(Math.abs(delta.amount))}
        </span>
      )}
    </div>
  )
}
