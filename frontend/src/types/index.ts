export interface OrderItem {
  name: string
  quantity: number
  is_core_item: boolean
  is_heavy: boolean
}

export interface OrderTimestamps {
  received: string | null
  picking_started: string | null
  picked: string | null
  dispatched: string | null
  delivered: string | null
}

export type OrderStatus = 'received' | 'picking' | 'picked' | 'dispatched' | 'delivered' | 'failed'
export type RiskLevel = 'green' | 'yellow' | 'red'

export interface Order {
  id: string
  customer_name: string
  items: OrderItem[]
  delivery_window: string
  zone: string
  status: OrderStatus
  assigned_driver: string | null
  timestamps: OrderTimestamps
  missing_items: string[]
  notes: string
  risk_level: RiskLevel
  items_picked: number
  total_items: number
  has_heavy_items: boolean
  needs_driver: boolean
}

export type DriverType = 'biker' | 'driver'
export type DriverStatus = 'available' | 'on_delivery' | 'called_out'

export interface Driver {
  id: string
  name: string
  type: DriverType
  zones: string[]
  status: DriverStatus
  current_orders: string[]
  company: string
}

export type ExceptionType = 'late_risk' | 'missing_item' | 'coverage_gap' | 'delivery_dispute' | 'driver_reservation'
export type ExceptionSeverity = 'low' | 'medium' | 'high'
export type ExceptionStatus = 'open' | 'escalated' | 'resolved'

export interface Exception {
  id: string
  type: ExceptionType
  order_id: string | null
  severity: ExceptionSeverity
  description: string
  agent_recommendation: string
  status: ExceptionStatus
  cs_notified: boolean
  created_at: string
  resolved_at: string | null
}

export type CSNotificationStatus = 'pending_batch' | 'pending' | 'handled'
export type CSNotificationSubtype = 'immediate' | 'batched' | 'standard'

export interface CSNotification {
  id: string
  order_id: string | null
  customer_name: string | null
  issue_type: string
  details: string
  customer_message: string
  status: CSNotificationStatus
  notification_subtype: CSNotificationSubtype
  created_at: string
  handled_at: string | null
}

export interface WindowStats {
  total: number
  delivered: number
  dispatched: number
  at_risk: number
  items_picked: number
  total_picking_items: number
  picking_orders: number
}

export interface CompanyStats {
  expected: number
  present: number
  called_out: number
  drivers: Driver[]
}

export interface Stats {
  total_orders: number
  status_breakdown: Record<string, number>
  window_stats: Record<string, WindowStats>
  drivers: {
    total: number
    available: number
    on_delivery: number
    called_out: number
    by_company: Record<string, CompanyStats>
  }
  open_exceptions: number
  pending_notifications: number
}

export interface ShiftSummaryStructured {
  handoff_status: 'clean' | 'issues' | 'critical'
  critical_issues: Array<{ title: string; detail: string; action: string }>
  next_priorities: string[]
  operational_notes: string
}

export interface AgentStatus {
  status?: string
  exceptions_detected?: number
  notifications_created?: number
  summary?: string
  timestamp?: string
  error?: string
}
