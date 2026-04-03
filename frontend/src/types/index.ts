export interface OrderItem {
  name: string
  quantity: number
  is_core_item: boolean
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
}

export type ExceptionType = 'late_risk' | 'missing_item' | 'coverage_gap' | 'delivery_dispute'
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

export type CSNotificationStatus = 'pending' | 'handled'

export interface CSNotification {
  id: string
  order_id: string | null
  customer_name: string | null
  issue_type: string
  details: string
  customer_message: string
  status: CSNotificationStatus
  created_at: string
  handled_at: string | null
}

export interface WindowStats {
  total: number
  delivered: number
  dispatched: number
  at_risk: number
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
  }
  open_exceptions: number
  pending_notifications: number
}

export interface AgentStatus {
  status?: string
  exceptions_detected?: number
  notifications_created?: number
  summary?: string
  timestamp?: string
  error?: string
}
