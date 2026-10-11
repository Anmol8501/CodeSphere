import { ChevronDown } from 'lucide-react'
import { useId } from 'react'
import { cn } from '../../utils/format'

interface SelectProps<T extends string> {
  label: string
  value: T
  options: { value: T; label: string }[]
  onChange: (value: T) => void
  /** Visually hide the label (it stays available to screen readers). */
  hideLabel?: boolean
  className?: string
  disabled?: boolean
}

/** Styled native <select> (keeps full keyboard and screen-reader support). */
export function Select<T extends string>({
  label,
  value,
  options,
  onChange,
  hideLabel,
  className,
  disabled,
}: SelectProps<T>) {
  const id = useId()
  return (
    <div className={className}>
      <label htmlFor={id} className={cn('mb-1.5 block text-xs font-semibold text-ink-500', hideLabel && 'sr-only')}>
        {label}
      </label>
      <div className="relative">
        <select
          id={id}
          value={value}
          disabled={disabled}
          onChange={(event) => onChange(event.target.value as T)}
          className="h-10 w-full cursor-pointer appearance-none rounded-xl border border-ink-200 bg-night pr-9 pl-3 text-sm text-ink-950 hover:border-ink-300 focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
        >
          {options.map((option) => (
            <option key={option.value} value={option.value} className="bg-surface">
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-ink-400" aria-hidden />
      </div>
    </div>
  )
}
