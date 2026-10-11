import type { ReactNode } from 'react'
import { cn } from '../../utils/format'

interface CardProps {
  children: ReactNode
  className?: string
  /** Adds subtle green corner brackets (HUD detail). Use sparingly. */
  hud?: boolean
  as?: 'div' | 'section' | 'article'
  'aria-labelledby'?: string
}

/** Decorative corner brackets for HUD-style cards. */
export function HudCorners() {
  const base = 'pointer-events-none absolute size-3 border-brand-500/50'
  return (
    <>
      <span className={cn(base, 'top-0 left-0 rounded-tl-2xl border-t border-l')} aria-hidden />
      <span className={cn(base, 'top-0 right-0 rounded-tr-2xl border-t border-r')} aria-hidden />
      <span className={cn(base, 'bottom-0 left-0 rounded-bl-2xl border-b border-l')} aria-hidden />
      <span className={cn(base, 'right-0 bottom-0 rounded-br-2xl border-r border-b')} aria-hidden />
    </>
  )
}

export function Card({ children, className, hud, as: Tag = 'div', ...rest }: CardProps) {
  return (
    <Tag
      className={cn('relative rounded-2xl border border-ink-200 bg-card shadow-card', className)}
      {...rest}
    >
      {hud && <HudCorners />}
      {children}
    </Tag>
  )
}

interface SectionCardProps {
  title: string
  description?: string
  icon?: ReactNode
  action?: ReactNode
  children: ReactNode
  className?: string
  bodyClassName?: string
  hud?: boolean
}

/** A titled card used for dashboard sections. */
export function SectionCard({
  title,
  description,
  icon,
  action,
  children,
  className,
  bodyClassName,
  hud,
}: SectionCardProps) {
  const id = `section-${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`
  return (
    <Card as="section" aria-labelledby={id} className={cn('flex min-w-0 flex-col', className)} hud={hud}>
      <div className="flex items-start justify-between gap-3 border-b border-ink-200 px-5 py-4">
        <div className="flex min-w-0 items-center gap-3">
          {icon && (
            <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-brand-500/10 text-brand-500 ring-1 ring-brand-500/20 [&>svg]:size-4">
              {icon}
            </span>
          )}
          <div className="min-w-0">
            <h2 id={id} className="truncate font-mono text-xs font-semibold tracking-[0.14em] text-ink-950 uppercase">
              {title}
            </h2>
            {description && <p className="mt-0.5 truncate text-[13px] text-ink-500">{description}</p>}
          </div>
        </div>
        {action}
      </div>
      <div className={cn('flex-1 p-5', bodyClassName)}>{children}</div>
    </Card>
  )
}
