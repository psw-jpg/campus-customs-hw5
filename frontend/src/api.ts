// Thin client for the FastAPI backend on port 8000 (backend/main.py).

export const API_BASE = 'http://localhost:8000'

export type TicketState = 'open' | 'running' | 'resolved'

export interface Ticket {
  id: number
  type: 'customer_order' | 'rent_notice' | 'price_override' | string
  requester: string
  subject: string
  sku: string | null
  size: string | null
  qty: number | null
  lease_id: number | null
  invoice_id: number | null
  status: string
  notes: string | null
  created_at: string
  state: TicketState
}

export interface Cash {
  name: string
  balance: number
  date: string
}

export interface Approval {
  id: number
  kind: 'invoice' | 'rent' | 'purchase'
  ref_id: number
  amount: number
  account: string
  reason: string | null
  requested_by: string
  status: 'pending' | 'approved' | 'rejected' | 'paid'
  approved_by: string | null
  created_at: string
  decided_at: string | null
}

export interface PurchaseOrder {
  id: number
  sku: string
  size: string
  qty: number
  vendor_name: string
  total: number
  status: 'pending_approval' | 'ordered' | 'rejected'
  expected_arrival: string | null
  ticket_id: number | null
}

// One entry from output/audit_trail.json.
export interface AuditEvent {
  at: string
  event: string
  run_id?: string
  ticket_id?: number
  agent?: string
  chain?: string
  depth?: number
  loop_step?: number
  task?: string
  text?: string | null
  tool?: string
  args?: string
  result?: string
  target?: string
  reason?: string
  error?: string
  summary?: string
  status?: string
  input_tokens?: number
  output_tokens?: number
  sensitive?: string | null
  output?: Record<string, unknown>
}

export interface RunInfo {
  run_id: string
  ticket_id: number
  state: 'running' | 'done' | 'error'
  started_at: string
  finished_at?: string
  result?: {
    decision: Decision | null
    error: string | null
    requests: number
    input_tokens: number
    output_tokens: number
  }
}

export interface Decision {
  ticket_id: number
  status: string
  summary: string
  reasoning: string
  pending_approval_ids: number[]
  draft_ids: number[]
  actions: { agent: string; action: string; result: string }[]
}

export interface AgentSummary {
  agent: string
  summaries: string[]
  tools: string[]
  delegated_to: string[]
  tokens: number
  steps: number
}

export interface TicketSummary {
  ticket_id: number
  run_id: string | null
  agents: AgentSummary[]
  decision: Decision | null
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  const body = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = body?.detail
    const message =
      typeof detail === 'string' ? detail : detail?.message ?? `${res.status} ${res.statusText}`
    throw new Error(message)
  }
  return body as T
}

export const api = {
  health: () => request<{ ok: boolean; model: string }>('/api/health'),
  tickets: () => request<Ticket[]>('/api/tickets'),
  cash: () => request<Cash>('/api/cash'),
  approvals: () => request<Approval[]>('/api/approvals'),
  purchaseOrders: () => request<PurchaseOrder[]>('/api/purchase-orders'),
  runTicket: (id: number) => request<RunInfo>(`/api/tickets/${id}/run`, { method: 'POST' }),
  run: (runId: string) => request<RunInfo>(`/api/runs/${runId}`),
  events: (q: { runId?: string; ticketId?: number; limit?: number }) => {
    const p = new URLSearchParams()
    if (q.runId) p.set('run_id', q.runId)
    if (q.ticketId !== undefined) p.set('ticket_id', String(q.ticketId))
    p.set('limit', String(q.limit ?? 400))
    return request<AuditEvent[]>(`/api/events?${p}`)
  },
  summary: (id: number) => request<TicketSummary>(`/api/tickets/${id}/summary`),
  approve: (id: number, approvedBy: string) =>
    request<{ approval_id: number; kind: Approval['kind']; payment: { new_balance: number; amount: number } }>(
      `/api/approvals/${id}/approve`,
      { method: 'POST', body: JSON.stringify({ approved_by: approvedBy }) },
    ),
  reject: (id: number, rejectedBy: string) =>
    request<Approval>(`/api/approvals/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ rejected_by: rejectedBy }),
    }),
  reset: () => request<{ ok: boolean; cash: Cash }>('/api/reset', { method: 'POST' }),
}

export const money = (n: number) =>
  n.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
