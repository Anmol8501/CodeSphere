import { ArrowUpRight, type LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Badge } from '../ui/Badge'

export interface QuickAction {
  label: string
  description: string
  icon: LucideIcon
  to: string
  /** Shows a "Soon" badge when the destination feature isn't built yet. */
  comingSoon?: boolean
}

export function QuickActions({ actions }: { actions: QuickAction[] }) {
  return (
    <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {actions.map((action) => {
        const Icon = action.icon
        return (
          <li key={action.to}>
            <Link
              to={action.to}
              className="group flex h-full items-start gap-3 rounded-xl border border-ink-200 bg-night/50 p-4 transition hover:border-brand-500/40 hover:bg-brand-500/[0.04]"
            >
              <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand-500/10 text-brand-500 ring-1 ring-brand-500/20">
                <Icon className="size-[18px]" aria-hidden />
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-ink-950">{action.label}</span>
                  {action.comingSoon && (
                    <Badge tone="warning" mono>
                      Soon
                    </Badge>
                  )}
                </span>
                <span className="mt-0.5 block text-xs leading-relaxed text-ink-500">{action.description}</span>
              </span>
              <ArrowUpRight
                className="size-4 shrink-0 text-ink-400 transition group-hover:text-brand-500"
                aria-hidden
              />
            </Link>
          </li>
        )
      })}
    </ul>
  )
}
