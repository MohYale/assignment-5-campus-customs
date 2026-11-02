export type Ticket = {
  id: number
  type: string
  requester: string
  subject: string
  sku: string | null
  size: string | null
  qty: number | null
  item_name: string | null
  unit_cost: number | null
  invoice_id: number | null
  invoice_amount: number | null
  lease_id: number | null
  monthly_rent: number | null
  space_name: string | null
  on_hand: number | null
  shortfall: number | null
  status: string
  open: boolean
  resolved: boolean
}

export type AgentEvent = {
  time: string
  run_id: string
  ticket_id: number | null
  step: number
  agent: string
  caller: string | null
  said: string
  thoughts: string[]
  tools: string[]
  final_call: boolean
  needs_human_approval: boolean
  approval_kind: string
}

export type Cash = {
  name: string
  balance: number
  date: string
}

export type PaymentDraft = {
  kind: 'invoice_payment' | 'rent_payment' | 'purchase_order'
  ref_id: number
  sku: string
  size: string
  qty: number
  title: string
  detail: string
  amount: number | null
}

export type RunResult = {
  run_id?: string
  ticket_id?: number
  steps?: number
  summary?: string
  status?: string
  resolved?: boolean
  needs_human_approval?: boolean
}
