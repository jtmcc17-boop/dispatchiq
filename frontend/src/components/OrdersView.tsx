import { Clock, AlertTriangle, CheckCircle, Package, Truck, MapPin, User } from 'lucide-react'
import type { Order, Stats, RiskLevel } from '../types'

interface Props {
  orders: Order[]
  stats: Stats | null
  selectedWindow: string | null
  onSelectWindow: (w: string | null) => void
  onUpdateStatus: (id: string, status: string) => void
}

const WINDOWS = ['10:00-11:00', '11:00-12:00', '12:00-13:00', '13:00-14:00']

const STATUS_LABEL: Record<string, string> = {
  received: 'Received',
  picking: 'Picking',
  picked: 'Picked',
  dispatched: 'Dispatched',
  delivered: 'Delivered',
  failed: 'Failed',
}

const STATUS_NEXT: Record<string, string | null> = {
  received: 'picking',
  picking: 'picked',
  picked: 'dispatched',
  dispatched: 'delivered',
  delivered: null,
  failed: null,
}

export function OrdersView({ orders, stats, selectedWindow, onSelectWindow, onUpdateStatus }: Props) {
  const filteredOrders = selectedWindow
    ? orders.filter(o => o.delivery_window === selectedWindow)
    : orders

  const sorted = [...filteredOrders].sort((a, b) => {
    const riskOrder = { red: 0, yellow: 1, green: 2 }
    return (riskOrder[a.risk_level] ?? 2) - (riskOrder[b.risk_level] ?? 2)
  })

  return (
    <div className="flex flex-col flex-1 min-w-0">
      {/* Window selector */}
      <div className="bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-2 flex-wrap">
        <button
          onClick={() => onSelectWindow(null)}
          className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
            selectedWindow === null
              ? 'bg-blue-600 text-white'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          All Windows
        </button>
        {WINDOWS.map(w => {
          const ws = stats?.window_stats[w]
          const atRisk = ws?.at_risk ?? 0
          return (
            <button
              key={w}
              onClick={() => onSelectWindow(selectedWindow === w ? null : w)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                selectedWindow === w
                  ? 'bg-blue-600 text-white'
                  : atRisk > 0
                  ? 'bg-red-50 text-red-700 border border-red-200 hover:bg-red-100'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <Clock size={13} />
              {w}
              {ws && (
                <span className={`text-xs px-1.5 py-0.5 rounded font-bold ${
                  selectedWindow === w ? 'bg-blue-500' : 'bg-white text-slate-700'
                }`}>
                  {ws.total}
                </span>
              )}
              {atRisk > 0 && selectedWindow !== w && (
                <span className="text-xs bg-red-500 text-white px-1 py-0.5 rounded font-bold">
                  {atRisk} at risk
                </span>
              )}
            </button>
          )
        })}

        <span className="ml-auto text-xs text-slate-400">
          {sorted.length} order{sorted.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Orders table */}
      <div className="flex-1 overflow-auto p-4">
        {sorted.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-slate-400">
            <Package size={32} className="mb-2 opacity-40" />
            <p>No orders</p>
          </div>
        ) : (
          <div className="space-y-2">
            {sorted.map(order => (
              <OrderRow key={order.id} order={order} onUpdateStatus={onUpdateStatus} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function OrderRow({ order, onUpdateStatus }: { order: Order; onUpdateStatus: (id: string, status: string) => void }) {
  const riskStyles: Record<RiskLevel, string> = {
    green: 'border-l-green-400',
    yellow: 'border-l-amber-400',
    red: 'border-l-red-500',
  }

  const riskBg: Record<RiskLevel, string> = {
    green: 'bg-white',
    yellow: 'bg-amber-50',
    red: 'bg-red-50',
  }

  const nextStatus = STATUS_NEXT[order.status]

  return (
    <div
      className={`rounded-lg border border-slate-200 border-l-4 ${riskStyles[order.risk_level]} ${riskBg[order.risk_level]} p-3 flex items-center gap-3`}
    >
      {/* Risk indicator */}
      <RiskDot level={order.risk_level} />

      {/* Order ID + customer */}
      <div className="w-32 flex-shrink-0">
        <div className="text-xs font-mono text-slate-500">{order.id}</div>
        <div className="text-sm font-medium text-slate-800 truncate">{order.customer_name}</div>
      </div>

      {/* Zone + driver */}
      <div className="w-36 flex-shrink-0 text-xs text-slate-600">
        <div className="flex items-center gap-1">
          <MapPin size={11} />
          {order.zone}
        </div>
        <div className="flex items-center gap-1 mt-0.5 text-slate-500">
          <User size={11} />
          {order.assigned_driver ?? <span className="italic text-amber-600">Unassigned</span>}
        </div>
      </div>

      {/* Window */}
      <div className="w-24 flex-shrink-0 text-xs">
        <div className="flex items-center gap-1 text-slate-500">
          <Clock size={11} />
          {order.delivery_window}
        </div>
      </div>

      {/* Status badge */}
      <div className="flex-1 flex items-center gap-2 flex-wrap">
        <StatusBadge status={order.status} />

        {order.missing_items.length > 0 && (
          <span className="flex items-center gap-1 text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">
            <AlertTriangle size={11} />
            Missing: {order.missing_items.join(', ')}
          </span>
        )}

        {order.items
          .filter(i => i.is_core_item && order.missing_items.includes(i.name))
          .map(i => (
            <span key={i.name} className="text-xs bg-red-600 text-white px-2 py-0.5 rounded-full font-bold animate-pulse">
              CORE MISSING
            </span>
          ))}
      </div>

      {/* Items summary */}
      <div className="w-40 flex-shrink-0 text-xs text-slate-500 truncate">
        {order.items.map(i => i.name).join(', ')}
      </div>

      {/* Action */}
      {nextStatus && (
        <button
          onClick={() => onUpdateStatus(order.id, nextStatus)}
          className="flex-shrink-0 flex items-center gap-1 px-2.5 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-medium rounded-md transition-colors"
        >
          <Truck size={12} />
          → {STATUS_LABEL[nextStatus]}
        </button>
      )}
      {order.status === 'delivered' && (
        <div className="flex-shrink-0 flex items-center gap-1 text-green-600 text-xs font-medium">
          <CheckCircle size={14} />
          Done
        </div>
      )}
    </div>
  )
}

function RiskDot({ level }: { level: RiskLevel }) {
  const colors = {
    green: 'bg-green-400',
    yellow: 'bg-amber-400 animate-pulse',
    red: 'bg-red-500 animate-pulse',
  }
  return <div className={`w-2 h-2 rounded-full flex-shrink-0 ${colors[level]}`} />
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    received: 'bg-slate-100 text-slate-600',
    picking: 'bg-blue-100 text-blue-700',
    picked: 'bg-purple-100 text-purple-700',
    dispatched: 'bg-amber-100 text-amber-700',
    delivered: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] ?? 'bg-slate-100 text-slate-600'}`}>
      {STATUS_LABEL[status] ?? status}
    </span>
  )
}
