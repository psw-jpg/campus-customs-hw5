// Who plays which agent, how each one "sounds", and how raw audit events become
// readable lines in the live feed. Flavor lines are only ever added on top of the
// real data; every number shown comes straight from the backend.
import type { AuditEvent } from './api'

export type AgentKey = 'boss' | 'inventory' | 'accounting' | 'facilities' | 'customer_service'

export interface CrewMember {
  key: AgentKey
  character: string
  role: string
  job: string
  color: string // accent
  ink: string // text on the accent
  catchphrases: string[] // shown when the character is handed a task
}

export const CREW: Record<AgentKey, CrewMember> = {
  boss: {
    key: 'boss',
    character: 'Mr. Krabs',
    role: 'Boss',
    job: 'Reads the ticket, hands out the work, makes the final call.',
    color: '#e2452f',
    ink: '#fff',
    catchphrases: ['Argh! Let\'s see what this ticket costs me.', 'Money, money, money! What have we got?'],
  },
  inventory: {
    key: 'inventory',
    character: 'SpongeBob',
    role: 'Inventory',
    job: 'Stock, shortfalls, restock costs and vendor arrival dates.',
    color: '#ffe23d',
    ink: '#3a2c00',
    catchphrases: ['I\'m ready! I\'m ready! To the stockroom!', 'Ooh, a stock check! Best. Day. Ever.'],
  },
  accounting: {
    key: 'accounting',
    character: 'Squidward',
    role: 'Accounting',
    job: 'Cash, invoices, payment and purchase requests, discount quotes.',
    color: '#7cc3b4',
    ink: '#0f2f29',
    catchphrases: ['*sigh* Fine. I\'ll check the till.', 'Another bill. How delightful.'],
  },
  facilities: {
    key: 'facilities',
    character: 'Sandy',
    role: 'Facilities',
    job: 'The Chapel Street lease, rent dates and where stock lives.',
    color: '#c98a4b',
    ink: '#2b1606',
    catchphrases: ['Howdy! Let me check the lease, partner.', 'Hold your horses, I\'ll verify that notice.'],
  },
  customer_service: {
    key: 'customer_service',
    character: 'Patrick',
    role: 'Customer Service',
    job: 'Drafts friendly messages. Drafts only, never sent.',
    color: '#ff9fb3',
    ink: '#4a0f1f',
    catchphrases: ['Is this the customer? No, this is Patrick! Drafting...', 'I can write a nice note!'],
  },
}

export const CREW_ORDER: AgentKey[] = ['boss', 'inventory', 'accounting', 'facilities', 'customer_service']

export const isAgent = (a?: string): a is AgentKey => !!a && a in CREW

const TOOL_LABELS: Record<string, [string, string]> = {
  get_ticket: ['🎫', 'Read the ticket'],
  list_tickets: ['📋', 'Read the board'],
  update_ticket: ['📌', 'Updated the ticket'],
  get_shop_date: ['📅', "Checked today's date"],
  check_restock: ['🔍', 'Checked the stockroom'],
  get_inventory: ['📦', 'Counted the shelves'],
  get_low_stock: ['📉', 'Scanned for low stock'],
  list_vendors: ['🚚', 'Checked the vendors'],
  list_purchase_orders: ['🧾', 'Looked at purchase orders'],
  pay_bill: ['💰', 'Prepared a payment'],
  request_restock_purchase: ['🛒', 'Requested a restock purchase'],
  quote_bulk_price: ['🏷️', 'Priced the bulk order'],
  get_cash_balance: ['🏦', 'Checked the till'],
  list_invoices: ['📄', 'Read the invoices'],
  list_payments: ['📒', 'Read the payment log'],
  list_payment_approvals: ['⏳', 'Checked pending approvals'],
  list_leases: ['🏠', 'Pulled up the lease'],
  draft_customer_message: ['✉️', 'Drafted a message (not sent)'],
  list_message_drafts: ['🗂️', 'Looked at drafts'],
}

export function toolLabel(tool = ''): [string, string] {
  if (tool.startsWith('delegate_to_')) {
    const who = tool.replace('delegate_to_', '')
    return ['📣', `Called ${isAgent(who) ? CREW[who].character : who}`]
  }
  return TOOL_LABELS[tool] ?? ['🔧', tool]
}

export type FeedKind = 'task' | 'speech' | 'tool' | 'handoff' | 'report' | 'alert' | 'done'

export interface FeedItem {
  id: string
  agent: AgentKey | 'system'
  kind: FeedKind
  text: string
  detail?: string
  icon?: string
  sensitive?: string | null
  depth: number
  at: string
}

function pick<T>(arr: T[], seed: string): T {
  let h = 0
  for (const c of seed) h = (h * 31 + c.charCodeAt(0)) | 0
  return arr[Math.abs(h) % arr.length]
}

function shortJson(s?: string, max = 220): string {
  if (!s) return ''
  return s.length > max ? s.slice(0, max) + '…' : s
}

/** Turn audit trail entries into feed lines, in order. */
export function toFeed(events: AuditEvent[]): FeedItem[] {
  const items: FeedItem[] = []
  events.forEach((e, i) => {
    const agent: AgentKey | 'system' = isAgent(e.agent) ? e.agent : 'system'
    const base = { id: `${e.at}-${i}`, agent, depth: e.depth ?? 0, at: e.at }
    switch (e.event) {
      case 'agent_start': {
        const who = agent === 'system' ? null : CREW[agent]
        items.push({
          ...base,
          kind: 'task',
          text: who ? pick(who.catchphrases, e.at) : 'Starting…',
          detail: e.task ?? '',
        })
        break
      }
      case 'model_response':
        if (e.text) items.push({ ...base, kind: 'speech', text: e.text })
        break
      case 'tool_call': {
        if (e.tool?.startsWith('delegate_to_')) break // shown as a handoff instead
        const [icon, label] = toolLabel(e.tool)
        items.push({ ...base, kind: 'tool', icon, text: label, detail: `${e.tool}(${shortJson(e.args, 160)})`, sensitive: e.sensitive })
        break
      }
      case 'tool_result': {
        if (e.tool?.startsWith('delegate_to_')) break
        // Attach the result to the matching call line.
        for (let j = items.length - 1; j >= 0; j--) {
          const it = items[j]
          if (it.kind === 'tool' && it.agent === agent && it.detail?.startsWith(`${e.tool}(`) && !it.detail.includes('\n→')) {
            it.detail += `\n→ ${shortJson(e.result, 420)}`
            break
          }
        }
        break
      }
      case 'delegation': {
        const target = isAgent(e.target) ? CREW[e.target].character : e.target
        items.push({ ...base, kind: 'handoff', icon: '📣', text: `Hey ${target}!`, detail: e.task ?? '' })
        break
      }
      case 'delegation_refused':
        items.push({ ...base, kind: 'alert', icon: '🛑', text: 'Handoff refused', detail: e.reason ?? '' })
        break
      case 'agent_output':
        items.push({ ...base, kind: 'report', text: e.summary ?? '' })
        break
      case 'tool_retry_error':
      case 'budget_exceeded_error':
      case 'ticket_error':
        items.push({ ...base, kind: 'alert', icon: '⚠️', text: 'Something went sideways', detail: e.error ?? '' })
        break
      case 'ticket_end':
        items.push({ ...base, agent: 'boss', kind: 'done', icon: '🏁', text: `Ticket wrapped up: ${e.status ?? 'error'}` })
        break
    }
  })
  return items
}

/** The agent currently "talking" in a run, and every agent that has finished. */
export function crewActivity(events: AuditEvent[]) {
  let active: AgentKey | null = null
  const finished = new Set<AgentKey>()
  const involved = new Set<AgentKey>()
  const lastLine: Partial<Record<AgentKey, string>> = {}
  for (const e of events) {
    if (!isAgent(e.agent)) continue
    involved.add(e.agent)
    if (e.event === 'agent_start') {
      active = e.agent
      finished.delete(e.agent)
    }
    if (e.event === 'tool_call' && e.tool && !e.tool.startsWith('delegate_to_')) {
      lastLine[e.agent] = toolLabel(e.tool).join(' ')
      active = e.agent
    }
    if (e.event === 'model_response' && e.text) lastLine[e.agent] = e.text
    if (e.event === 'agent_output') {
      finished.add(e.agent)
      lastLine[e.agent] = e.summary ?? lastLine[e.agent]
      // Control returns to whoever delegated.
      const chain = (e.chain ?? '').split(' -> ')
      const parent = chain[chain.length - 2]
      active = isAgent(parent) ? parent : null
    }
  }
  return { active, finished, involved, lastLine }
}

export const TICKET_LOOK: Record<string, { emoji: string; label: string }> = {
  customer_order: { emoji: '👕', label: 'Customer order' },
  rent_notice: { emoji: '🏠', label: 'Rent notice' },
  price_override: { emoji: '🏷️', label: 'Bulk discount' },
}

export const OUTCOME_LABEL: Record<string, string> = {
  resolved: 'All done',
  waiting_approval: 'Waiting on your OK',
  blocked: 'Blocked',
  needs_human: 'Needs a human',
  open: 'Open',
  in_progress: 'In progress',
}
