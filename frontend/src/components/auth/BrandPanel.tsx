import { CheckCircle2 } from 'lucide-react'
import { CodeWindow } from '../brand/CodeWindow'

const HIGHLIGHTS = [
  'Practice DSA problems with instant feedback',
  'Track your progress and keep your streak alive',
  'Compete in contests and classroom assignments',
]

/** Dark branding column shown next to auth forms on large screens. */
export function BrandPanel() {
  return (
    <div className="relative hidden overflow-hidden rounded-3xl border border-ink-200 bg-surface p-10 text-ink-950 lg:flex lg:flex-col lg:justify-between">
      <div className="bg-dot-grid absolute inset-0" aria-hidden />
      <div
        className="absolute -top-24 -right-24 size-80 rounded-full bg-brand-500/15 blur-3xl"
        aria-hidden
      />
      <div
        className="absolute -bottom-32 -left-20 size-80 rounded-full bg-accent/10 blur-3xl"
        aria-hidden
      />
      <span
        className="absolute top-8 right-10 font-mono text-6xl font-bold text-brand-500/[0.08] select-none"
        aria-hidden
      >
        {'{ }'}
      </span>

      <div className="relative">
        <p className="inline-flex items-center gap-2 rounded-full border border-brand-500/25 bg-brand-500/5 px-3 py-1 font-mono text-xs text-brand-400">
          <span className="size-1.5 animate-pulse rounded-full bg-brand-500" /> Learn • Code • Compete
        </p>
        <h2 className="mt-6 text-[34px] leading-[1.15] font-extrabold tracking-tight">
          Where college coders
          <br />
          <span className="bg-gradient-to-r from-brand-500 to-accent bg-clip-text text-transparent">
            sharpen their skills.
          </span>
        </h2>
        <ul className="mt-6 space-y-3">
          {HIGHLIGHTS.map((item) => (
            <li key={item} className="flex items-start gap-2.5 text-[15px] text-ink-700">
              <CheckCircle2 className="mt-0.5 size-[18px] shrink-0 text-brand-500" />
              {item}
            </li>
          ))}
        </ul>
      </div>

      <CodeWindow className="relative mt-10" />
    </div>
  )
}
