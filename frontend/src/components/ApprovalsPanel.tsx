// "Needs your OK": payments and purchases the agents prepared. Only a human click moves money.
import { useState } from 'react'
import type { Approval, PurchaseOrder } from '../api'
import { money } from '../api'

const KIND_LOOK: Record<Approval['kind'], { emoji: string; label: string; parade: string }> = {
  invoice: { emoji: '📄', label: 'Vendor invoice', parade: 'Plankton' },
  rent: { emoji: '🏠', label: 'Rent', parade: 'Plankton' },
  purchase: { emoji: '🛒', label: 'Restock purchase', parade: 'Gary' },
}

export function ApprovalsPanel({
  approvals,
  purchaseOrders,
  approver,
  setApprover,
  busyId,
  balance,
  onApprove,
  onReject,
}: {
  approvals: Approval[]
  purchaseOrders: PurchaseOrder[]
  approver: string
  setApprover: (v: string) => void
  busyId: number | null
  balance: number | null
  onApprove: (a: Approval) => void
  onReject: (a: Approval) => void
}) {
  const [touched, setTouched] = useState(false)
  const pending = approvals.filter((a) => a.status === 'pending' || a.status === 'approved')
  const history = approvals.filter((a) => a.status === 'paid' || a.status === 'rejected').slice(-4).reverse()
  const nameMissing = approver.trim().length === 0
  const pendingTotal = pending.reduce((s, a) => s + a.amount, 0)
  const ordered = purchaseOrders.filter((p) => p.status === 'ordered')

  return (
    <section className="panel approvals" aria-labelledby="approvals-title">
      <header className="panel-head">
        <h2 id="approvals-title">
          <span aria-hidden="true">🔐</span> Needs Your OK
        </h2>
        {pending.length > 0 && <span className="count-badge">{pending.length}</span>}
      </header>

      <label className="approver">
        <span>Approving as</span>
        <input
          value={approver}
          onChange={(e) => setApprover(e.target.value)}
          onBlur={() => setTouched(true)}
          placeholder="Your name"
          aria-invalid={touched && nameMissing}
          maxLength={60}
        />
      </label>
      {touched && nameMissing && <p className="field-error">Add your name so the payment log shows who approved it.</p>}

      {pending.length === 0 ? (
        <div className="empty small">
          <span className="empty-emoji" aria-hidden="true">
            🦀
          </span>
          Nothing waiting. Squidward files payment and purchase requests here during a run.
        </div>
      ) : (
        <>
          {balance !== null && (
            <p className={`cover-check ${pendingTotal > balance ? 'short' : ''}`}>
              Waiting: <strong>{money(pendingTotal)}</strong> ·{' '}
              {pendingTotal > balance
                ? `${money(pendingTotal - balance)} more than the till holds. Some will be refused.`
                : `leaves ${money(balance - pendingTotal)} if all are approved`}
            </p>
          )}
          <ul className="asks">
            {pending.map((a) => {
              const look = KIND_LOOK[a.kind]
              const busy = busyId === a.id
              return (
                <li key={a.id} className={`ask ask-${a.kind}`}>
                  <div className="ask-top">
                    <span className="ask-kind">
                      <span aria-hidden="true">{look.emoji}</span> {look.label}
                    </span>
                    <span className="ask-amount">{money(a.amount)}</span>
                  </div>
                  <p className="ask-reason">{a.reason}</p>
                  <p className="ask-meta">
                    Requested by {a.requested_by} · approval #{a.id}
                    {a.status === 'approved' && ' · approved earlier, payment still due'}
                  </p>
                  <div className="ask-actions">
                    <button
                      className="btn btn-approve"
                      disabled={busy || nameMissing}
                      onClick={() => onApprove(a)}
                      title={nameMissing ? 'Add your name first' : `Approve and pay ${money(a.amount)}`}
                    >
                      {busy ? <span className="spinner" aria-hidden="true" /> : '✓'} Approve & pay
                    </button>
                    {a.status === 'pending' && (
                      <button className="btn btn-reject" disabled={busy || nameMissing} onClick={() => onReject(a)}>
                        Reject
                      </button>
                    )}
                  </div>
                  <span className="ask-parade" aria-hidden="true">
                    {look.parade === 'Gary' ? '🐌' : '🦠'} {look.parade} is on standby
                  </span>
                </li>
              )
            })}
          </ul>
        </>
      )}

      {(history.length > 0 || ordered.length > 0) && (
        <div className="ledger">
          <h3>Recent decisions</h3>
          <ul>
            {history.map((a) => (
              <li key={a.id} className={`ledger-${a.status}`}>
                <span>{KIND_LOOK[a.kind].emoji}</span>
                <span className="ledger-what">{a.reason}</span>
                <span className="ledger-amt">{a.status === 'paid' ? `−${money(a.amount)}` : 'rejected'}</span>
                <span className="ledger-who">by {a.approved_by}</span>
              </li>
            ))}
            {ordered.map((p) => (
              <li key={`po-${p.id}`} className="ledger-ordered">
                <span>🚚</span>
                <span className="ledger-what">
                  {p.qty} × {p.sku} {p.size} from {p.vendor_name}
                </span>
                <span className="ledger-amt">arrives {p.expected_arrival}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}
