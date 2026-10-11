import { useId } from 'react'
import { Link } from 'react-router-dom'
import { cn } from '../../utils/format'

/** The square </> brand mark. */
export function LogoMark({ className }: { className?: string }) {
  // Unique per instance: a shared id would point at the first logo in the DOM,
  // which may be inside a hidden element (e.g. the desktop sidebar on mobile).
  const gradientId = `ca-logo-${useId().replace(/:/g, '')}`
  return (
    <svg viewBox="0 0 64 64" fill="none" className={cn('size-9 shrink-0', className)} aria-hidden>
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
          <stop stopColor="#39ff14" />
          <stop offset="1" stopColor="#17b33a" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="16" fill={`url(#${gradientId})`} />
      <path
        d="M25 21 14 32l11 11M39 21l11 11-11 11"
        stroke="#050805"
        strokeWidth="5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M35 17 29 47" stroke="#050805" strokeOpacity=".6" strokeWidth="4" strokeLinecap="round" />
    </svg>
  )
}

interface LogoProps {
  to?: string
  /** "light" text for dark backgrounds. */
  tone?: 'dark' | 'light'
  className?: string
  subtitle?: string
}

export function Logo({ to = '/', tone = 'dark', className, subtitle }: LogoProps) {
  return (
    <Link to={to} className={cn('inline-flex items-center gap-2.5', className)} aria-label="CodeArena home">
      <LogoMark />
      <span className="flex flex-col leading-none">
        <span
          className={cn(
            'text-[17px] font-extrabold tracking-[0.12em]',
            'text-ink-950',
          )}
        >
          CODE<span className="text-brand-500">ARENA</span>
        </span>
        {subtitle && (
          <span
            className={cn(
              'mt-1 font-mono text-[10px] tracking-wider uppercase',
              tone === 'light' ? 'text-ink-500' : 'text-ink-400',
            )}
          >
            {subtitle}
          </span>
        )}
      </span>
    </Link>
  )
}
