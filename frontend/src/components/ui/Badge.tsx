import type { ReactNode } from 'react'
import type { Role } from '../../types/auth'
import { cn, roleLabel } from '../../utils/format'
import { TONE_CHIP, TONE_DOT, type Tone } from './tones'

interface BadgeProps {
  tone?: Tone
  children: ReactNode
  className?: string
  /** Monospace uppercase style used for technical labels (e.g. role, phase). */
  mono?: boolean
}

export function Badge({ tone = 'neutral', children, className, mono }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold whitespace-nowrap ring-1 ring-inset',
        mono && 'rounded-md font-mono tracking-wider uppercase',
        TONE_CHIP[tone],
        className,
      )}
    >
      {children}
    </span>
  )
}

const ROLE_TONES: Record<Role, Tone> = { STUDENT: 'info', STAFF: 'accent', ADMIN: 'warning' }

export function RoleBadge({ role, mono }: { role: Role; mono?: boolean }) {
  return (
    <Badge tone={ROLE_TONES[role]} mono={mono}>
      {mono ? role : roleLabel(role)}
    </Badge>
  )
}

export function StatusBadge({ active }: { active: boolean }) {
  const tone: Tone = active ? 'brand' : 'danger'
  return (
    <Badge tone={tone}>
      <span className={cn('size-1.5 rounded-full', TONE_DOT[tone])} aria-hidden />
      {active ? 'Active' : 'Inactive'}
    </Badge>
  )
}
