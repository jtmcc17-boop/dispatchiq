import { useState } from 'react'
import {
  ClipboardList, Loader2, Bot, AlertTriangle, CheckCircle,
  TrendingUp, ChevronDown, ChevronUp, ArrowRight, Truck, Bell,
} from 'lucide-react'
import { api } from '../api/client'
import type { Stats, Exception, ShiftSummaryStructured } from '../types'

interface Props {
  stats: Stats | null
  exceptions: Exception[]
}

export function ShiftSummary({ stats, exceptions }: Props) {
  const [structured, setStructured] = useState<ShiftSummaryStructured | null>(null)
  const [loading, setLoading] = useState(false)
  const [generatedAt, setGeneratedAt] = useState<string | null>(null)
  const [notesOpen, setNotesOpen] = useState(false)

  const generate = async () => {
    setLoading(true)
    try {
      const result = await api.agent.shiftSummary()
      setStructured(result.structured)
      setGeneratedAt(result.generated_at)
    } catch {
      setStructured({
        handoff_status: 'issues',
        critical_issues: [],
        next_priorities: ['Review open exceptions', 'Clear pending CS notifications'],
        operational_notes: 'Error generating summary — check backend connection.',
      })
    } finally {
      setLoading(false)
    }
  }

  const openExc = exceptions.filter(e => e.status === 'open')
  const resolvedExc = exceptions.filter(e => e.status === 'resolved')
  const deliveredCount = stats?.status_breakdown['delivered'] ?? 0
  const totalOrders = stats?.total_orders ?? 0
  const completionRate = totalOrders > 0 ? Math.round((deliveredCount / totalOrders) * 100) : 0

  const handoffColor = {
    clean: 'bg-green-50 border-green-200 text-green-800',
    issues: 'bg-amber-50 border-amber-200 text-amber-800',
    critical: 'bg-red-50 border-red-300 text-red-800',
  }
  const handoffIcon = {
    clean: <CheckCircle size={16} className="text-green-600" />,
    issues: <AlertTriangle size={16} className="text-amber-600" />,
    critical: <AlertTriangle size={16} className="text-red-600" />,
  }
  const handoffLabel = {
    clean: 'Clean Handoff',
    issues: 'Handoff Has Issues',
    critical: 'Critical — Immediate Attention Required',
  }

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <ClipboardList size={20} className="text-blue-600" />
        <div>
          <h1 className="text-xl font-bold text-slate-900">Shift Summary</h1>
          <p className="text-sm text-slate-500">Scannable in 15 seconds</p>
        </div>
        <button
          onClick={generate}
          disabled={loading}
          className="ml-auto flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {loading ? <Loader2 size={15} className="animate-spin" /> : <Bot size={15} />}
          {loading ? 'Generating…' : structured ? 'Regenerate' : 'Generate Briefing'}
        </button>
      </div>

      {/* Handoff status banner (from AI) */}
      {structured && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-xl border font-semibold text-sm ${
          handoffColor[structured.handoff_status]
        }`}>
          {handoffIcon[structured.handoff_status]}
          {handoffLabel[structured.handoff_status]}
          {generatedAt && (
            <span className="ml-auto text-xs font-normal opacity-70">
              Generated {new Date(generatedAt).toLocaleTimeString()}
            </span>
          )}
        </div>
      )}

      {/* Stat cards — always visible, no AI needed */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard
            label="Total Orders"
            value={totalOrders}
            sub={`${completionRate}% delivered`}
            icon={<ClipboardList size={18} />}
            color="blue"
          />
          <StatCard
            label="Delivered"
            value={deliveredCount}
            sub={`${stats.status_breakdown['dispatched'] ?? 0} in transit`}
            icon={<CheckCircle size={18} />}
            color="green"
          />
          <StatCard
            label="Open Exceptions"
            value={stats.open_exceptions}
            sub={`${resolvedExc.length} resolved this shift`}
            icon={<AlertTriangle size={18} />}
            color={stats.open_exceptions > 0 ? 'red' : 'slate'}
          />
          <StatCard
            label="CS Pending"
            value={stats.pending_notifications}
            sub="need customer contact"
            icon={<Bell size={18} />}
            color={stats.pending_notifications > 0 ? 'amber' : 'slate'}
          />
        </div>
      )}

      {/* Window progress — always visible */}
      {stats && (
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">Delivery Windows</h2>
          <div className="space-y-2.5">
            {Object.entries(stats.window_stats).sort().map(([window, ws]) => {
              const done = ws.delivered + ws.dispatched
              const pct = ws.total > 0 ? Math.round((done / ws.total) * 100) : 0
              return (
                <div key={window} className="flex items-center gap-3">
                  <span className="text-xs font-mono text-slate-600 w-24 flex-shrink-0">{window}</span>
                  <div className="flex-1 bg-slate-100 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        ws.at_risk > 0 ? 'bg-amber-400' : pct === 100 ? 'bg-green-500' : 'bg-blue-400'
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className="text-xs text-slate-500 w-40 flex-shrink-0">
                    {done}/{ws.total} done
                    {ws.at_risk > 0 && (
                      <span className="text-red-600 font-medium ml-1">· {ws.at_risk} at risk</span>
                    )}
                    {ws.picking_orders > 0 && (
                      <span className="text-blue-500 ml-1">· {ws.picking_orders} picking</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="bg-white rounded-xl border border-slate-200 p-8 flex flex-col items-center gap-3 text-slate-500">
          <Loader2 size={28} className="animate-spin text-blue-500" />
          <p className="text-sm">Agent is writing your shift briefing…</p>
        </div>
      )}

      {/* Critical issues — from AI */}
      {structured && !loading && structured.critical_issues.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-1.5">
            <AlertTriangle size={14} className="text-red-500" />
            Critical Handoff Issues
          </h2>
          {structured.critical_issues.map((issue, i) => (
            <div key={i} className="bg-red-50 border border-red-200 rounded-xl p-4">
              <div className="font-semibold text-red-800 text-sm mb-1">{issue.title}</div>
              <p className="text-sm text-red-700 mb-2">{issue.detail}</p>
              <div className="flex items-start gap-1.5 text-xs text-red-800 bg-red-100 rounded-lg px-3 py-2">
                <ArrowRight size={12} className="flex-shrink-0 mt-0.5" />
                <span className="font-medium">{issue.action}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Next shift priorities — from AI */}
      {structured && !loading && structured.next_priorities.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-1.5">
            <Truck size={14} className="text-blue-500" />
            Next Shift Priorities
          </h2>
          <ol className="space-y-2">
            {structured.next_priorities.map((p, i) => (
              <li key={i} className="flex items-start gap-3 text-sm">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center mt-0.5">
                  {i + 1}
                </span>
                <span className="text-slate-700">{p}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Open exceptions quick list — always visible */}
      {openExc.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">
            Open Exceptions ({openExc.length})
          </h2>
          <div className="space-y-1.5">
            {openExc.map(e => (
              <div key={e.id} className="flex items-center gap-2 text-xs">
                <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                  e.severity === 'high' ? 'bg-red-500' :
                  e.severity === 'medium' ? 'bg-amber-400' : 'bg-slate-400'
                }`} />
                <span className="font-medium text-slate-600 capitalize">{e.type.replace(/_/g, ' ')}</span>
                <span className="text-slate-400 flex-1 truncate">{e.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Operational notes — collapsible */}
      {structured && !loading && structured.operational_notes && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <button
            onClick={() => setNotesOpen(o => !o)}
            className="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <span className="flex items-center gap-1.5">
              <TrendingUp size={14} />
              Operational Notes
            </span>
            {notesOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          {notesOpen && (
            <div className="px-4 pb-4 text-sm text-slate-600 leading-relaxed border-t border-slate-100 pt-3">
              {structured.operational_notes}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function StatCard({
  label, value, sub, icon, color,
}: {
  label: string
  value: number
  sub?: string
  icon: React.ReactNode
  color: string
}) {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-700 border-blue-100',
    green: 'bg-green-50 text-green-700 border-green-100',
    red: 'bg-red-50 text-red-700 border-red-100',
    amber: 'bg-amber-50 text-amber-700 border-amber-100',
    slate: 'bg-slate-50 text-slate-600 border-slate-200',
  }
  return (
    <div className={`rounded-xl border p-4 ${colorMap[color] ?? colorMap.slate}`}>
      <div className="flex items-center gap-2 mb-1 opacity-70">{icon}</div>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs font-medium opacity-70 mt-0.5">{label}</div>
      {sub && <div className="text-xs opacity-50 mt-0.5">{sub}</div>}
    </div>
  )
}
