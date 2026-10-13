import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, money, type Approval, type AuditEvent, type Cash, type PurchaseOrder, type Ticket, type TicketSummary } from './api'
import { crewActivity, toFeed } from './crew'
import { Ocean } from './components/Ocean'
import { CashChest } from './components/CashChest'
import { TicketBoard } from './components/TicketBoard'
import { CrewStage } from './components/CrewStage'
import { LiveFeed } from './components/LiveFeed'
import { ApprovalsPanel } from './components/ApprovalsPanel'
import { ShiftReport } from './components/ShiftReport'
import { Celebration, type Parade } from './components/Celebration'
import { MrKrabs } from './components/Characters'

type Toast = { id: number; tone: 'good' | 'bad' | 'info'; text: string }
type ActiveRun = { runId: string; ticketId: number }

const IDLE_POLL_MS = 4000
const RUN_POLL_MS = 1000

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [cash, setCash] = useState<Cash | null>(null)
  const [approvals, setApprovals] = useState<Approval[]>([])
  const [orders, setOrders] = useState<PurchaseOrder[]>([])
  const [backendDown, setBackendDown] = useState(false)

  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [activeRun, setActiveRun] = useState<ActiveRun | null>(null)
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [summary, setSummary] = useState<TicketSummary | null>(null)

  const [approver, setApprover] = useState(() => localStorage.getItem('cc-approver') ?? '')
  const [busyApproval, setBusyApproval] = useState<number | null>(null)
  const [parade, setParade] = useState<Parade | null>(null)
  const [toasts, setToasts] = useState<Toast[]>([])
  const [confirmReset, setConfirmReset] = useState(false)
  // Runs that finished before the last reset belong to an old shift; hide them.
  const [freshSince, setFreshSince] = useState(() => localStorage.getItem('cc-fresh-since') ?? '')

  const toastId = useRef(0)
  const toast = useCallback((tone: Toast['tone'], text: string) => {
    const id = ++toastId.current
    setToasts((t) => [...t, { id, tone, text }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 6000)
  }, [])

  useEffect(() => localStorage.setItem('cc-approver', approver), [approver])

  // ------------------------------------------------------------ data loading
  const refreshShop = useCallback(async () => {
    try {
      const [t, c, a, o] = await Promise.all([api.tickets(), api.cash(), api.approvals(), api.purchaseOrders()])
      setTickets(t)
      setCash(c)
      setApprovals(a)
      setOrders(o)
      setBackendDown(false)
      setSelectedId((s) => s ?? t[0]?.id ?? null)
      return t
    } catch {
      setBackendDown(true)
      return null
    }
  }, [])

  const loadTicketHistory = useCallback(
    async (ticketId: number) => {
      try {
        const s = await api.summary(ticketId)
        if (!s.run_id) {
          setSummary(null)
          setEvents([])
          return
        }
        const ev = await api.events({ runId: s.run_id })
        const stale = freshSince && ev.length > 0 && ev[0].at < freshSince
        setSummary(stale ? null : s)
        setEvents(stale ? [] : ev)
      } catch {
        /* backend banner covers this */
      }
    },
    [freshSince],
  )

  // Idle polling of tickets, cash and approvals.
  useEffect(() => {
    refreshShop()
    const t = setInterval(refreshShop, IDLE_POLL_MS)
    return () => clearInterval(t)
  }, [refreshShop])

  // If the page is refreshed mid-run, pick the run back up from the audit trail.
  useEffect(() => {
    if (activeRun) return
    const running = tickets.find((t) => t.state === 'running')
    if (!running) return
    api
      .events({ ticketId: running.id, limit: 600 })
      .then((ev) => {
        const starts = ev.filter((e) => e.event === 'run_start' && e.run_id)
        const runId = starts[starts.length - 1]?.run_id
        if (runId) {
          setActiveRun({ runId, ticketId: running.id })
          setSelectedId(running.id)
        }
      })
      .catch(() => {
        /* backend unreachable: the banner covers it, and the next poll retries */
      })
  }, [tickets, activeRun])

  // When the selected ticket changes (and nothing is running on it), show its last run.
  useEffect(() => {
    if (selectedId === null) return
    if (activeRun?.ticketId === selectedId) return
    loadTicketHistory(selectedId)
  }, [selectedId, activeRun, loadTicketHistory])

  // Live polling while a run is going.
  useEffect(() => {
    if (!activeRun) return
    let stopped = false
    const tick = async () => {
      try {
        const [ev, info] = await Promise.all([api.events({ runId: activeRun.runId, limit: 800 }), api.run(activeRun.runId).catch(() => null)])
        if (stopped) return
        if (selectedId === activeRun.ticketId) setEvents(ev)
        const ended = ev.some((e) => e.event === 'ticket_end') || (info && info.state !== 'running')
        refreshShop()
        if (ended) {
          stopped = true
          setActiveRun(null)
          const end = ev.find((e) => e.event === 'ticket_end')
          if (end?.error || info?.state === 'error') toast('bad', `Ticket #${activeRun.ticketId} hit a snag. See the Kitchen Radio.`)
          else toast('good', `Ticket #${activeRun.ticketId} done: Mr. Krabs says "${end?.status ?? 'finished'}".`)
          loadTicketHistory(activeRun.ticketId)
        }
      } catch {
        /* keep trying */
      }
    }
    tick()
    const t = setInterval(() => !stopped && tick(), RUN_POLL_MS)
    return () => {
      stopped = true
      clearInterval(t)
    }
  }, [activeRun, selectedId, refreshShop, toast, loadTicketHistory])

  // ------------------------------------------------------------ actions
  const startRun = async (ticketId: number) => {
    try {
      setSummary(null)
      setEvents([])
      const info = await api.runTicket(ticketId)
      setActiveRun({ runId: info.run_id, ticketId })
      toast('info', `Mr. Krabs is reading ticket #${ticketId}…`)
      refreshShop()
    } catch (e) {
      toast('bad', (e as Error).message)
    }
  }

  const approve = async (a: Approval) => {
    setBusyApproval(a.id)
    try {
      const res = await api.approve(a.id, approver.trim())
      setParade({
        kind: a.kind === 'purchase' ? 'purchase' : 'payment',
        amount: res.payment.amount,
        label: a.kind === 'purchase' ? 'restock ordered' : a.kind === 'rent' ? 'rent paid' : 'invoice paid',
        key: Date.now(),
      })
      setTimeout(() => setParade(null), a.kind === 'purchase' ? 7600 : 5200)
      toast('good', `${money(res.payment.amount)} paid. Checking now ${money(res.payment.new_balance)}.`)
    } catch (e) {
      toast('bad', `Not paid: ${(e as Error).message}`)
    } finally {
      setBusyApproval(null)
      refreshShop()
    }
  }

  const reject = async (a: Approval) => {
    setBusyApproval(a.id)
    try {
      await api.reject(a.id, approver.trim())
      toast('info', `Rejected approval #${a.id}. No money moved.`)
    } catch (e) {
      toast('bad', (e as Error).message)
    } finally {
      setBusyApproval(null)
      refreshShop()
    }
  }

  const doReset = async () => {
    setConfirmReset(false)
    try {
      await api.reset()
      // Local time, to match the audit trail's local timestamps.
      const d = new Date()
      const now = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 19)
      localStorage.setItem('cc-fresh-since', now)
      setFreshSince(now)
      setEvents([])
      setSummary(null)
      toast('info', 'Fresh shift! The shop database is back to its original values.')
      refreshShop()
    } catch (e) {
      toast('bad', (e as Error).message)
    }
  }

  // ------------------------------------------------------------ derived
  const running = activeRun !== null && activeRun.ticketId === selectedId
  const feed = useMemo(() => toFeed(events), [events])
  const activity = useMemo(() => crewActivity(events), [events])
  const resolvedCount = tickets.filter((t) => t.state === 'resolved').length
  const pendingCount = approvals.filter((a) => a.status === 'pending' || a.status === 'approved').length

  return (
    <>
      <Ocean />
      <div className="app">
        <a className="skip" href="#main">
          Skip to the board
        </a>
        <header className="topbar">
          <div className="brand">
            <MrKrabs size={64} />
            <div>
              <p className="kicker">Campus Customs · Multi-agent ops</p>
              <h1>The Krusty Krab Ops Board</h1>
            </div>
          </div>
          <div className="stats" aria-label="Shift progress">
            <div className="stat">
              <span className="stat-num">
                {resolvedCount}/{tickets.length || 3}
              </span>
              <span className="stat-label">tickets resolved</span>
            </div>
            <div className={`stat ${pendingCount ? 'stat-alert' : ''}`}>
              <span className="stat-num">{pendingCount}</span>
              <span className="stat-label">waiting on you</span>
            </div>
          </div>
          <CashChest balance={cash?.balance ?? null} date={cash?.date} error={backendDown} />
          <button className="btn btn-ghost" onClick={() => setConfirmReset(true)} disabled={activeRun !== null}>
            🔄 Fresh shift
          </button>
        </header>

        {backendDown && (
          <div className="banner" role="alert">
            🫧 Can't reach the kitchen at <code>localhost:8000</code>. Start it from <code>backend/</code> with{' '}
            <code>uvicorn main:app --reload --port 8000</code>. Retrying…
          </div>
        )}

        <main id="main" className="grid">
          <TicketBoard
            tickets={tickets}
            selectedId={selectedId}
            runningId={activeRun?.ticketId ?? null}
            onSelect={setSelectedId}
            onRun={startRun}
            backendDown={backendDown}
          />
          <div className="center">
            <CrewStage {...activity} running={running} />
            <LiveFeed items={feed} running={running} ticketId={selectedId} />
          </div>
          <div className="side">
            <ApprovalsPanel
              approvals={approvals}
              purchaseOrders={orders}
              approver={approver}
              setApprover={setApprover}
              busyId={busyApproval}
              balance={cash?.balance ?? null}
              onApprove={approve}
              onReject={reject}
            />
            <ShiftReport summary={summary} running={running} />
          </div>
        </main>

        <footer className="foot">
          Agents on <strong>gpt-6-luna</strong> via Portkey · every step logged to <code>output/audit_trail.json</code> ·
          customer messages are drafts only
        </footer>
      </div>

      <Celebration parade={parade} />

      <div className="toasts" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.tone}`}>
            {t.text}
          </div>
        ))}
      </div>

      {confirmReset && (
        <div className="modal-backdrop" onClick={() => setConfirmReset(false)}>
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="reset-title"
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => e.key === 'Escape' && setConfirmReset(false)}
          >
            <h2 id="reset-title">Start a fresh shift?</h2>
            <p>
              This copies the original <code>campus_customs.db</code> over the working copy: cash back to the start,
              every ticket open, and all approvals and purchases cleared. The audit trail is kept.
            </p>
            <div className="modal-actions">
              <button className="btn btn-ghost dark" onClick={() => setConfirmReset(false)} autoFocus>
                Cancel
              </button>
              <button className="btn btn-run" onClick={doReset}>
                Reset the shop
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
