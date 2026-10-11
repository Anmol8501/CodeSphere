import { useId } from 'react'
import { cn } from '../../utils/format'

interface SwitchProps {
  label: string
  description?: string
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
  className?: string
}

/** Accessible on/off toggle built on a native checkbox (role="switch"). */
export function Switch({ label, description, checked, onChange, disabled, className }: SwitchProps) {
  const id = useId()
  return (
    <div className={cn('flex items-start gap-3', className)}>
      <span className="relative mt-0.5 inline-flex shrink-0">
        <input
          id={id}
          type="checkbox"
          role="switch"
          checked={checked}
          disabled={disabled}
          aria-describedby={description ? `${id}-description` : undefined}
          onChange={(event) => onChange(event.target.checked)}
          className="peer absolute inset-0 z-10 cursor-pointer opacity-0 disabled:cursor-not-allowed"
        />
        <span
          aria-hidden
          className={cn(
            'flex h-5 w-9 items-center rounded-full p-0.5 ring-1 transition peer-focus-visible:ring-4 peer-focus-visible:ring-brand-500/25',
            checked ? 'bg-brand-500/90 ring-brand-500' : 'bg-ink-100 ring-ink-300',
            disabled && 'opacity-50',
          )}
        >
          <span className={cn('size-4 rounded-full transition', checked ? 'translate-x-4 bg-night' : 'bg-ink-400')} />
        </span>
      </span>
      <span className="min-w-0">
        <label htmlFor={id} className="cursor-pointer text-sm font-semibold text-ink-900">
          {label}
        </label>
        {description && (
          <span id={`${id}-description`} className="block text-[13px] text-ink-500">
            {description}
          </span>
        )}
      </span>
    </div>
  )
}
