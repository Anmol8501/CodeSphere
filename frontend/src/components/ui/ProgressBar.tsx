import { cn } from '../../utils/format'

interface ProgressBarProps {
  /** 0–100 */
  value: number
  label?: string
  /** Use `label` only as the accessible name (not shown). */
  hideLabel?: boolean
  showValue?: boolean
  size?: 'sm' | 'md'
  className?: string
}

export function ProgressBar({ value, label, hideLabel, showValue = true, size = 'md', className }: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)))
  return (
    <div className={className}>
      {((label && !hideLabel) || showValue) && (
        <div className="mb-1.5 flex items-center justify-between gap-3 text-[13px]">
          {label && !hideLabel && <span className="truncate font-medium text-ink-800">{label}</span>}
          {showValue && <span className="font-mono text-xs text-ink-500 tabular-nums">{clamped}%</span>}
        </div>
      )}
      <div
        role="progressbar"
        aria-label={label ?? 'Progress'}
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        className={cn('overflow-hidden rounded-full bg-ink-100 ring-1 ring-ink-200 ring-inset', size === 'sm' ? 'h-1.5' : 'h-2')}
      >
        <div
          className="h-full rounded-full bg-gradient-to-r from-moss via-accent to-brand-500 shadow-glow-sm transition-[width] duration-500"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  )
}
