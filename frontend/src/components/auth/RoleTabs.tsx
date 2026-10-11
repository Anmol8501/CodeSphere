import { GraduationCap, Presentation } from 'lucide-react'
import type { ReactNode } from 'react'
import { cn } from '../../utils/format'

export type PublicLoginRole = 'STUDENT' | 'STAFF'

const OPTIONS: { value: PublicLoginRole; label: string; icon: ReactNode }[] = [
  { value: 'STUDENT', label: 'Student', icon: <GraduationCap className="size-4" /> },
  { value: 'STAFF', label: 'Staff', icon: <Presentation className="size-4" /> },
]

interface RoleTabsProps {
  value: PublicLoginRole
  onChange: (role: PublicLoginRole) => void
}

/** Segmented "Login as" control. Admin is intentionally not an option here. */
export function RoleTabs({ value, onChange }: RoleTabsProps) {
  return (
    <div>
      <p className="mb-2 text-xs font-semibold tracking-wider text-ink-500 uppercase">Login as</p>
      <div role="tablist" aria-label="Login as" className="grid grid-cols-2 gap-1 rounded-xl bg-night p-1 ring-1 ring-ink-200">
        {OPTIONS.map((option) => {
          const selected = option.value === value
          return (
            <button
              key={option.value}
              type="button"
              role="tab"
              aria-selected={selected}
              onClick={() => onChange(option.value)}
              className={cn(
                'flex h-10 items-center justify-center gap-2 rounded-lg text-sm font-bold tracking-wide transition',
                selected
                  ? 'bg-brand-500/10 text-brand-500 ring-1 ring-brand-500/40'
                  : 'text-ink-500 hover:text-ink-800',
              )}
            >
              {option.icon}
              {option.label.toUpperCase()}
            </button>
          )
        })}
      </div>
    </div>
  )
}
