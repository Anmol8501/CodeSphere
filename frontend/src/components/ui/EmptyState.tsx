import type { ReactNode } from 'react'
import { cn } from '../../utils/format'
import { Button, ButtonLink } from './Button'

interface EmptyStateProps {
  icon: ReactNode
  title: string
  description?: string
  /** Label for the built-in action button. Use with `actionTo` or `onAction`. */
  actionLabel?: string
  actionTo?: string
  onAction?: () => void
  /** Fully custom action element (overrides actionLabel). */
  action?: ReactNode
  className?: string
  /** Smaller padding for use inside dropdowns or small cards. */
  compact?: boolean
}

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  actionTo,
  onAction,
  action,
  className,
  compact,
}: EmptyStateProps) {
  let actionNode = action
  if (!actionNode && actionLabel) {
    actionNode = actionTo ? (
      <ButtonLink to={actionTo} size="sm">
        {actionLabel}
      </ButtonLink>
    ) : (
      <Button size="sm" onClick={onAction}>
        {actionLabel}
      </Button>
    )
  }

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-xl border border-dashed border-ink-300 bg-night/40 text-center',
        compact ? 'px-4 py-6' : 'px-6 py-9',
        className,
      )}
    >
      <span className="flex size-11 items-center justify-center rounded-xl bg-surface text-ink-400 ring-1 ring-ink-200 [&>svg]:size-5">
        {icon}
      </span>
      <p className="mt-3 text-sm font-semibold text-ink-900">{title}</p>
      {description && <p className="mt-1 max-w-sm text-[13px] leading-relaxed text-ink-500">{description}</p>}
      {actionNode && <div className="mt-4">{actionNode}</div>}
    </div>
  )
}
