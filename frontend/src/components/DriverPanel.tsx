import { Bike, Car, PhoneOff, Package, CircleDot } from 'lucide-react'
import type { Driver, Stats } from '../types'

interface Props {
  drivers: Driver[]
  stats: Stats | null
}

export function DriverPanel({ drivers, stats }: Props) {
  const companyStats = stats?.drivers.by_company ?? {}

  // Build company list from drivers, preserving order
  const companies = Array.from(new Set(drivers.map(d => d.company).filter(Boolean)))

  const totalDrivers = drivers.length
  const presentDrivers = drivers.filter(d => d.status !== 'called_out').length
  const calledOut = drivers.filter(d => d.status === 'called_out').length

  return (
    <aside className="w-56 bg-white border-r border-slate-200 flex flex-col overflow-hidden">
      {/* Header with shift-level summary */}
      <div className="px-3 pt-4 pb-3 border-b border-slate-100 flex-shrink-0">
        <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
          Drivers
        </h2>
        <div className="bg-slate-50 rounded-lg px-3 py-2 text-xs space-y-0.5">
          <div className="flex justify-between">
            <span className="text-slate-500">Expected</span>
            <span className="font-semibold text-slate-700">{totalDrivers}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Present</span>
            <span className="font-semibold text-green-700">{presentDrivers}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Out</span>
            <span className={`font-semibold ${calledOut > 0 ? 'text-red-600' : 'text-slate-500'}`}>
              {calledOut}
            </span>
          </div>
        </div>
      </div>

      {/* Companies */}
      <div className="flex-1 overflow-auto py-2">
        {companies.map(company => {
          const compDrivers = drivers.filter(d => d.company === company)
          const cs = companyStats[company]
          const expected = cs?.expected ?? compDrivers.length
          const present = cs?.present ?? compDrivers.filter(d => d.status !== 'called_out').length
          const out = cs?.called_out ?? compDrivers.filter(d => d.status === 'called_out').length
          const hasGap = out > 0

          return (
            <div key={company} className="px-3 py-2">
              {/* Company header */}
              <div className={`rounded-md px-2 py-1.5 mb-2 ${hasGap ? 'bg-red-50' : 'bg-slate-50'}`}>
                <div className={`text-xs font-semibold truncate ${hasGap ? 'text-red-700' : 'text-slate-700'}`}>
                  {company}
                </div>
                <div className="flex items-center gap-2 mt-0.5 text-xs">
                  <span className="text-slate-500">
                    {present}/{expected} present
                  </span>
                  {out > 0 && (
                    <span className="text-red-600 font-medium">· {out} out</span>
                  )}
                </div>
              </div>

              {/* Driver rows */}
              <div className="space-y-1 pl-1">
                {compDrivers.map(d => (
                  <DriverRow key={d.id} driver={d} />
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Footer: biker vs driver split */}
      <div className="border-t border-slate-100 px-3 py-2 flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-1">
          <Bike size={11} />
          <span>{drivers.filter(d => d.type === 'biker').length} bikers</span>
        </div>
        <div className="flex items-center gap-1">
          <Car size={11} />
          <span>{drivers.filter(d => d.type === 'driver').length} drivers</span>
        </div>
      </div>
    </aside>
  )
}

function DriverRow({ driver }: { driver: Driver }) {
  const isCalledOut = driver.status === 'called_out'
  const isOnDelivery = driver.status === 'on_delivery'

  const Icon =
    isCalledOut ? PhoneOff :
    isOnDelivery ? Package :
    driver.type === 'biker' ? Bike : Car

  const nameColor = isCalledOut
    ? 'text-red-400 line-through'
    : isOnDelivery
    ? 'text-blue-600'
    : 'text-slate-700'

  const iconColor = isCalledOut
    ? 'text-red-400'
    : isOnDelivery
    ? 'text-blue-500'
    : 'text-green-500'

  return (
    <div className="flex items-center gap-1.5">
      <Icon size={11} className={iconColor} />
      <span className={`text-xs truncate flex-1 ${nameColor}`}>
        {driver.name.split(' ')[0]}
      </span>
      {!isCalledOut && !isOnDelivery && (
        <CircleDot size={8} className="text-green-400 flex-shrink-0" />
      )}
    </div>
  )
}
