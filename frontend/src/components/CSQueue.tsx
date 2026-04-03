import { CheckCircle, Bell, Clock, Package, User } from 'lucide-react'
import type { CSNotification } from '../types'

interface Props {
  notifications: CSNotification[]
  onMarkHandled: (id: string) => void
}

function timeAgo(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  return `${Math.floor(diff / 3600)}h ago`
}

const ISSUE_COLOR: Record<string, string> = {
  missing_core_item: 'bg-red-100 text-red-700',
  missing_item: 'bg-amber-100 text-amber-700',
  late_delivery: 'bg-orange-100 text-orange-700',
  coverage_gap: 'bg-purple-100 text-purple-700',
  delivery_dispute: 'bg-blue-100 text-blue-700',
}

export function CSQueue({ notifications, onMarkHandled }: Props) {
  const pending = notifications.filter(n => n.status === 'pending')
  const handled = notifications.filter(n => n.status === 'handled')

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Bell size={20} className="text-blue-600" />
        <div>
          <h1 className="text-xl font-bold text-slate-900">CS Notification Queue</h1>
          <p className="text-sm text-slate-500">
            Agent-generated alerts that need customer communication
          </p>
        </div>
        <div className="ml-auto flex items-center gap-3 text-sm">
          <span className="bg-red-100 text-red-700 px-3 py-1 rounded-full font-semibold">
            {pending.length} pending
          </span>
          <span className="bg-slate-100 text-slate-600 px-3 py-1 rounded-full">
            {handled.length} handled
          </span>
        </div>
      </div>

      {pending.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-slate-400 bg-white rounded-xl border border-slate-200">
          <CheckCircle size={40} className="mb-3 opacity-30" />
          <p className="font-medium">All caught up!</p>
          <p className="text-sm mt-1">No pending CS notifications</p>
        </div>
      )}

      {pending.length > 0 && (
        <div className="space-y-3 mb-8">
          {pending.map(n => (
            <NotificationCard key={n.id} notif={n} onMarkHandled={onMarkHandled} />
          ))}
        </div>
      )}

      {handled.length > 0 && (
        <>
          <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">
            Handled ({handled.length})
          </h2>
          <div className="space-y-2 opacity-60">
            {handled.slice(0, 10).map(n => (
              <NotificationCard key={n.id} notif={n} onMarkHandled={onMarkHandled} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function NotificationCard({
  notif,
  onMarkHandled,
}: {
  notif: CSNotification
  onMarkHandled: (id: string) => void
}) {
  const isHandled = notif.status === 'handled'

  return (
    <div className={`bg-white rounded-xl border ${isHandled ? 'border-slate-100' : 'border-slate-200 shadow-sm'} p-4`}>
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            {notif.order_id && (
              <span className="font-mono text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                {notif.order_id}
              </span>
            )}
            <span
              className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${
                ISSUE_COLOR[notif.issue_type] ?? 'bg-slate-100 text-slate-600'
              }`}
            >
              {notif.issue_type.replace(/_/g, ' ')}
            </span>
            <span className="text-xs text-slate-400 flex items-center gap-1 ml-auto">
              <Clock size={11} />
              {timeAgo(notif.created_at)}
            </span>
          </div>

          {notif.customer_name && (
            <div className="flex items-center gap-1.5 text-sm font-medium text-slate-800 mb-1">
              <User size={13} className="text-slate-400" />
              {notif.customer_name}
            </div>
          )}

          {/* Internal details */}
          <p className="text-xs text-slate-500 mb-3">{notif.details}</p>

          {/* What CS should say */}
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
            <div className="text-xs font-semibold text-blue-600 mb-1 flex items-center gap-1">
              <Package size={11} />
              What to tell the customer:
            </div>
            <p className="text-sm text-blue-900 leading-relaxed">
              {notif.customer_message}
            </p>
          </div>
        </div>

        <div className="flex-shrink-0">
          {isHandled ? (
            <div className="flex items-center gap-1 text-green-600 text-xs font-medium">
              <CheckCircle size={15} />
              Handled
            </div>
          ) : (
            <button
              onClick={() => onMarkHandled(notif.id)}
              className="flex items-center gap-1.5 px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              <CheckCircle size={14} />
              Mark Handled
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
