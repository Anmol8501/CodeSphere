import { CheckCircle2, Circle, CircleDot } from 'lucide-react'
import type { UserProblemStatus } from '../../types/problem'
import { cn } from '../../utils/format'

const CONFIG: Record<UserProblemStatus, { label: string; className: string; Icon: typeof Circle }> = {
  SOLVED: { label: 'Solved', className: 'text-brand-500', Icon: CheckCircle2 },
  ATTEMPTED: { label: 'Attempted', className: 'text-warning', Icon: CircleDot },
  UNSOLVED: { label: 'Not Attempted', className: 'text-ink-400', Icon: Circle },
}

/** ✓ solved, ◉ attempted, ○ not attempted. Status comes from the server (judged submissions only). */
export function SolvedStatus({ status, showLabel }: { status: UserProblemStatus; showLabel?: boolean }) {
  const { label, className, Icon } = CONFIG[status]
  return (
    <span className={cn('inline-flex items-center gap-1.5 text-xs font-semibold', className)} title={label}>
      <Icon className="size-4 shrink-0" aria-hidden />
      {showLabel ? label : <span className="sr-only">{label}</span>}
    </span>
  )
}
