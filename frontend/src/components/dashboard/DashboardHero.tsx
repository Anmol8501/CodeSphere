import type { ReactNode } from 'react'
import { HudCorners } from '../ui/Card'

export interface HeroMeta {
  label: string
  value: ReactNode
}

interface DashboardHeroProps {
  eyebrow: string
  title: ReactNode
  subtitle: ReactNode
  meta?: HeroMeta[]
  action?: ReactNode
}

/** Top-of-dashboard banner with HUD details. All `meta` values must be real. */
export function DashboardHero({ eyebrow, title, subtitle, meta, action }: DashboardHeroProps) {
  return (
    <section className="relative mb-6 overflow-hidden rounded-2xl border border-ink-200 bg-card px-6 py-7 sm:px-8">
      <HudCorners />
      <div className="bg-dot-grid absolute inset-0 opacity-60" aria-hidden />
      <div className="absolute -top-24 -right-16 size-72 rounded-full bg-brand-500/10 blur-3xl" aria-hidden />
      <span
        className="absolute right-8 bottom-1 hidden font-mono text-7xl font-bold text-brand-500/[0.06] select-none md:block"
        aria-hidden
      >
        {'</>'}
      </span>

      <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0">
          <p className="flex items-center gap-2 font-mono text-[11px] tracking-[0.18em] text-brand-500 uppercase">
            <span className="size-1.5 animate-pulse rounded-full bg-brand-500 shadow-glow-sm" aria-hidden />
            {eyebrow}
          </p>
          <h1 className="mt-3 text-2xl font-extrabold tracking-tight break-words text-ink-950 sm:text-3xl">{title}</h1>
          <p className="mt-1.5 text-sm text-ink-500 sm:text-[15px]">{subtitle}</p>
          {action && <div className="mt-5 flex flex-wrap gap-2">{action}</div>}
        </div>

        {meta && meta.length > 0 && (
          <dl className="flex flex-wrap gap-x-8 gap-y-3 border-t border-ink-200 pt-4 lg:border-t-0 lg:border-l lg:pt-0 lg:pl-8">
            {meta.map((item) => (
              <div key={item.label}>
                <dt className="font-mono text-[10px] tracking-[0.2em] text-ink-400 uppercase">{item.label}</dt>
                <dd className="mt-1 font-mono text-sm font-semibold text-ink-950">{item.value}</dd>
              </div>
            ))}
          </dl>
        )}
      </div>
    </section>
  )
}
