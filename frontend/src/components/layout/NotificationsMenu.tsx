import { Bell, BellOff } from 'lucide-react'
import { Dropdown } from '../ui/Dropdown'
import { EmptyState } from '../ui/EmptyState'

/**
 * Notification bell. There is no notification system yet, so the panel shows
 * an honest empty state instead of sample notifications.
 */
export function NotificationsMenu() {
  return (
    <Dropdown
      role="dialog"
      label="Notifications"
      widthClass="w-80"
      trigger={(props) => (
        <button
          type="button"
          {...props}
          aria-label="Notifications"
          className="flex size-10 items-center justify-center rounded-xl text-ink-500 ring-1 ring-ink-200 transition hover:bg-ink-100 hover:text-ink-950"
        >
          <Bell className="size-[18px]" aria-hidden />
        </button>
      )}
    >
      {() => (
        <div>
          <div className="flex items-center justify-between border-b border-ink-200 px-4 py-3">
            <p className="font-mono text-xs font-semibold tracking-[0.14em] text-ink-950 uppercase">Notifications</p>
          </div>
          <div className="p-3">
            <EmptyState
              compact
              icon={<BellOff />}
              title="No notifications yet."
              description="Updates about contests, assignments and feedback will appear here."
            />
          </div>
        </div>
      )}
    </Dropdown>
  )
}
