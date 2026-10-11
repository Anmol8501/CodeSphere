import type { ReactNode } from 'react'
import { cn } from '../../utils/format'
import { Card } from './Card'
import { TONE_CHIP, type Tone } from './tones'

interface StatCardProps {
  label: string
  value: ReactNode
  icon: ReactNode
  tone?: Tone
  caption?: string
  /** Muted value styling for "empty" values like "Not Rated". */
  muted?: boolean
}

export function StatCard({ label, value, icon, tone = 'brand', caption, muted }: StatCardProps) {
  return (
    <Card className="group overflow-hidden p-5 transition hover:border-brand-500/30">
      <div
        className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-brand-500/40 to-transparent opacity-0 transition group-hover:opacity-100"
        aria-hidden
      />
      <div className="flex items-start justify-between gap-3">
        <p className="font-mono text-[11px] font-semibold tracking-[0.14em] text-ink-500 uppercase">{label}</p>
        <span
          className={cn(
            'flex size-8 shrink-0 items-center justify-center rounded-lg ring-1 ring-inset [&>svg]:size-4',
            TONE_CHIP[tone],
          )}
          aria-hidden
        >
          {icon}
        </span>
      </div>
      <p
        className={cn(
          'mt-3 text-[28px] leading-tight font-extrabold tracking-tight',
          muted ? 'text-ink-500' : 'text-ink-950',
        )}
      >
        {value}
      </p>
      {caption && <p className="mt-1 text-xs text-ink-400">{caption}</p>}
    </Card>
  )
}
