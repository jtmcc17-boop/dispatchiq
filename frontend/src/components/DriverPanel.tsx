import { Bike, Car, PhoneOff, MapPin, Package } from 'lucide-react'
import type { Driver } from '../types'

interface Props {
  drivers: Driver[]
}

const ZONES = ['Uptown', 'Midtown', 'Chelsea', 'East Village', 'Downtown']

export function DriverPanel({ drivers }: Props) {
  const byZone = ZONES.map(zone => ({
    zone,
    drivers: drivers.filter(d => d.zones.includes(zone)),
  }))

  return (
    <aside className="w-52 bg-white border-r border-slate-200 flex flex-col overflow-auto">
      <div className="px-3 pt-4 pb-2 border-b border-slate-100">
        <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Drivers</h2>
        <div className="flex gap-3 mt-2 text-xs">
          <span className="text-green-600 font-medium">
            {drivers.filter(d => d.status === 'available').length} avail
          </span>
          <span className="text-blue-600 font-medium">
            {drivers.filter(d => d.status === 'on_delivery').length} out
          </span>
          <span className="text-red-600 font-medium">
            {drivers.filter(d => d.status === 'called_out').length} out sick
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-auto py-2">
        {byZone.map(({ zone, drivers: zoneDrvs }) => {
          const available = zoneDrvs.filter(d => d.status === 'available')
          const hasGap = zoneDrvs.length > 0 && available.length === 0
          return (
            <div key={zone} className="px-3 py-2">
              <div className="flex items-center gap-1 mb-1.5">
                <MapPin size={11} className={hasGap ? 'text-red-500' : 'text-slate-400'} />
                <span className={`text-xs font-semibold ${hasGap ? 'text-red-600' : 'text-slate-600'}`}>
                  {zone}
                </span>
                {hasGap && (
                  <span className="ml-auto text-xs text-red-500 font-medium">NO COVER</span>
                )}
              </div>
              {zoneDrvs.length === 0 ? (
                <p className="text-xs text-slate-400 pl-3">No drivers</p>
              ) : (
                <div className="space-y-1">
                  {zoneDrvs.map(d => (
                    <DriverRow key={d.id} driver={d} />
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Summary */}
      <div className="border-t border-slate-100 px-3 py-2 text-xs text-slate-500">
        <div className="flex items-center gap-1">
          <Bike size={11} /> {drivers.filter(d => d.type === 'biker').length} bikers
        </div>
        <div className="flex items-center gap-1 mt-0.5">
          <Car size={11} /> {drivers.filter(d => d.type === 'driver').length} drivers
        </div>
      </div>
    </aside>
  )
}

function DriverRow({ driver }: { driver: Driver }) {
  const statusColor = {
    available: 'text-green-600',
    on_delivery: 'text-blue-600',
    called_out: 'text-red-500 line-through',
  }[driver.status]

  const StatusIcon =
    driver.status === 'called_out'
      ? PhoneOff
      : driver.status === 'on_delivery'
      ? Package
      : driver.type === 'biker'
      ? Bike
      : Car

  return (
    <div className="flex items-center gap-1.5 pl-2">
      <StatusIcon size={11} className={statusColor} />
      <span className={`text-xs ${statusColor} truncate`}>{driver.name.split(' ')[0]}</span>
      <span className="ml-auto text-xs text-slate-400">{driver.type === 'biker' ? '🚲' : '🚗'}</span>
    </div>
  )
}
