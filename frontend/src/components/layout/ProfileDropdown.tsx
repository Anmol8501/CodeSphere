import { ChevronDown, LogOut, Settings, UserRound } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { User } from '../../types/auth'
import { cn } from '../../utils/format'
import { ROLE_PROFILE } from '../../utils/routes'
import { Avatar } from '../ui/Avatar'
import { RoleBadge } from '../ui/Badge'
import { Dropdown } from '../ui/Dropdown'

interface ProfileDropdownProps {
  user: User
  onLogout: () => void
  loggingOut?: boolean
}

const itemClass =
  'flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-ink-700 transition hover:bg-ink-100 hover:text-ink-950'

export function ProfileDropdown({ user, onLogout, loggingOut }: ProfileDropdownProps) {
  return (
    <Dropdown
      label="Account menu"
      trigger={(props) => (
        <button
          type="button"
          {...props}
          aria-label={`Account menu for ${user.full_name}`}
          className="flex items-center gap-2.5 rounded-xl p-1 pr-1.5 transition hover:bg-ink-100 sm:pr-2"
        >
          <Avatar name={user.full_name} />
          <span className="hidden min-w-0 text-left md:block">
            <span className="block max-w-36 truncate text-sm font-semibold text-ink-950">{user.full_name}</span>
            <span className="mt-0.5 block">
              <RoleBadge role={user.role} mono />
            </span>
          </span>
          <ChevronDown
            className={cn('hidden size-4 text-ink-400 transition sm:block', props['aria-expanded'] && 'rotate-180')}
            aria-hidden
          />
        </button>
      )}
    >
      {(close) => (
        <>
          <div className="flex items-center gap-3 border-b border-ink-200 px-4 py-3.5">
            <Avatar name={user.full_name} size="lg" />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-ink-950">{user.full_name}</p>
              <p className="truncate text-xs text-ink-500">{user.email}</p>
              <div className="mt-1.5">
                <RoleBadge role={user.role} mono />
              </div>
            </div>
          </div>
          <div className="p-1.5">
            <Link role="menuitem" to={ROLE_PROFILE[user.role]} onClick={close} className={itemClass}>
              <UserRound className="size-4 text-ink-400" aria-hidden /> Profile
            </Link>
            <Link role="menuitem" to="/settings" onClick={close} className={itemClass}>
              <Settings className="size-4 text-ink-400" aria-hidden /> Settings
            </Link>
            <div className="my-1 h-px bg-ink-200" />
            <button
              role="menuitem"
              type="button"
              disabled={loggingOut}
              onClick={() => {
                close()
                onLogout()
              }}
              className={cn(itemClass, 'text-danger hover:bg-danger/10 hover:text-danger disabled:opacity-50')}
            >
              <LogOut className="size-4" aria-hidden /> {loggingOut ? 'Logging out...' : 'Logout'}
            </button>
          </div>
        </>
      )}
    </Dropdown>
  )
}
