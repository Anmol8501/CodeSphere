import { LogOut } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { NAV_SECTIONS, PORTAL_LABEL, isNavItemActive } from '../../config/navigation'
import type { User } from '../../types/auth'
import { cn } from '../../utils/format'
import { ROLE_HOME } from '../../utils/routes'
import { Logo } from '../brand/Logo'

interface SidebarProps {
  user: User
  onLogout: () => void
  loggingOut?: boolean
  /** Called after a link is chosen (closes the mobile drawer). */
  onNavigate?: () => void
}

export function Sidebar({ user, onLogout, loggingOut, onNavigate }: SidebarProps) {
  const { pathname } = useLocation()

  return (
    <div className="flex h-full flex-col border-r border-ink-200 bg-surface">
      <div className="flex h-16 shrink-0 items-center border-b border-ink-200 px-5">
        <Logo to={ROLE_HOME[user.role]} tone="light" subtitle={PORTAL_LABEL[user.role]} />
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-5" aria-label="Main navigation">
        {NAV_SECTIONS[user.role].map((section) => (
          <div key={section.label} className="mb-6 last:mb-0">
            <p className="mb-2 px-3 font-mono text-[10px] font-semibold tracking-[0.2em] text-ink-400 uppercase">
              {section.label}
            </p>
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const Icon = item.icon
                const active = isNavItemActive(item, pathname)
                return (
                  <li key={item.to}>
                    <Link
                      to={item.to}
                      onClick={onNavigate}
                      aria-current={active ? 'page' : undefined}
                      className={cn(
                        'relative flex h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium transition',
                        active
                          ? 'bg-brand-500/[0.08] text-brand-500 shadow-[inset_0_0_0_1px_rgb(57_255_20/0.12)]'
                          : 'text-ink-500 hover:bg-ink-100 hover:text-ink-950',
                      )}
                    >
                      {active && (
                        <span
                          className="absolute top-1/2 left-0 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-brand-500 shadow-glow-sm"
                          aria-hidden
                        />
                      )}
                      <Icon className={cn('size-[18px] shrink-0', active ? 'text-brand-500' : 'text-ink-400')} aria-hidden />
                      <span className="truncate">{item.label}</span>
                    </Link>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-ink-200 p-3">
        <button
          type="button"
          onClick={onLogout}
          disabled={loggingOut}
          className="flex h-10 w-full items-center gap-3 rounded-lg px-3 text-sm font-medium text-ink-500 transition hover:bg-danger/10 hover:text-danger disabled:opacity-50"
        >
          <LogOut className="size-[18px]" aria-hidden />
          {loggingOut ? 'Logging out...' : 'Logout'}
        </button>
        <p className="mt-2 px-3 font-mono text-[10px] tracking-wider text-ink-400">CODEARENA · v0.2.0</p>
      </div>
    </div>
  )
}
