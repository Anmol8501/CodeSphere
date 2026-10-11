import { Bot, Cpu, Database, KeyRound, Server, type LucideIcon } from 'lucide-react'
import type { ServiceStatus } from '../../types/dashboard'
import { StatusIndicator } from '../ui/StatusIndicator'

const ICONS: Record<string, LucideIcon> = {
  api: Server,
  database: Database,
  auth: KeyRound,
  judge: Cpu,
  ai: Bot,
}

interface SystemStatusPanelProps {
  services: ServiceStatus[]
  showDetail?: boolean
}

/** Service list reported by the backend. Never marks unbuilt services online. */
export function SystemStatusPanel({ services, showDetail = true }: SystemStatusPanelProps) {
  return (
    <ul className="-my-3 divide-y divide-ink-200">
      {services.map((service) => {
        const Icon = ICONS[service.key] ?? Server
        return (
          <li key={service.key} className="flex items-center gap-3 py-3">
            <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-night text-ink-500 ring-1 ring-ink-200">
              <Icon className="size-4" aria-hidden />
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate font-mono text-xs font-semibold tracking-wider text-ink-900 uppercase">
                {service.name}
              </p>
              {showDetail && <p className="truncate text-xs text-ink-400">{service.detail}</p>}
            </div>
            <StatusIndicator state={service.status} />
          </li>
        )
      })}
    </ul>
  )
}
