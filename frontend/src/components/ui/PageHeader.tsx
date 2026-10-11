import type { ReactNode } from 'react'

interface PageHeaderProps {
  /** Small monospace technical label above the title, e.g. "MODULE · DSA". */
  eyebrow?: string
  title: ReactNode
  description?: ReactNode
  action?: ReactNode
}

export function PageHeader({ eyebrow, title, description, action }: PageHeaderProps) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        {eyebrow && (
          <p className="mb-2 flex items-center gap-2 font-mono text-[11px] tracking-[0.18em] text-brand-500 uppercase">
            <span className="h-px w-5 bg-brand-500/60" aria-hidden />
            {eyebrow}
          </p>
        )}
        <h1 className="text-2xl font-extrabold tracking-tight text-ink-950 sm:text-[28px]">{title}</h1>
        {description && <p className="mt-1 text-sm text-ink-500 sm:text-[15px]">{description}</p>}
      </div>
      {action && <div className="flex shrink-0 flex-wrap gap-2">{action}</div>}
    </div>
  )
}
