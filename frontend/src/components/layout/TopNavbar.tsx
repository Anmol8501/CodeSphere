import { Menu } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import { PORTAL_LABEL, getPageTitle } from '../../config/navigation'
import type { User } from '../../types/auth'
import { ROLE_HOME } from '../../utils/routes'
import { Logo } from '../brand/Logo'
import { NotificationsMenu } from './NotificationsMenu'
import { ProfileDropdown } from './ProfileDropdown'

interface TopNavbarProps {
  user: User
  onOpenMenu: () => void
  onLogout: () => void
  loggingOut?: boolean
}

export function TopNavbar({ user, onOpenMenu, onLogout, loggingOut }: TopNavbarProps) {
  const { pathname } = useLocation()
  const title = getPageTitle(user.role, pathname)

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-3 border-b border-ink-200 bg-surface/85 px-4 backdrop-blur-md sm:px-6 lg:px-8">
      <div className="flex min-w-0 items-center gap-2">
        <button
          type="button"
          onClick={onOpenMenu}
          className="-ml-1 flex size-10 items-center justify-center rounded-xl text-ink-700 hover:bg-ink-100 lg:hidden"
          aria-label="Open navigation menu"
        >
          <Menu className="size-5" aria-hidden />
        </button>

        {/* Mobile: brand. Desktop: breadcrumb + page title. */}
        <div className="lg:hidden">
          <Logo to={ROLE_HOME[user.role]} />
        </div>
        <nav aria-label="Breadcrumb" className="hidden min-w-0 lg:block">
          <ol className="flex items-center gap-2 font-mono text-[11px] tracking-wider text-ink-400 uppercase">
            <li>{PORTAL_LABEL[user.role]}</li>
            <li aria-hidden className="text-ink-300">
              /
            </li>
            <li aria-current="page" className="truncate font-semibold text-ink-950">
              {title}
            </li>
          </ol>
        </nav>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <NotificationsMenu />
        <ProfileDropdown user={user} onLogout={onLogout} loggingOut={loggingOut} />
      </div>
    </header>
  )
}
