import { CheckCircle2, CircleDashed, Clock, Info, XCircle } from 'lucide-react'
import type { SubmissionStatus, TestStatus } from '../../types/workspace'
import { cn } from '../../utils/format'
import { TONE_CHIP, type Tone } from '../ui/tones'
import { TEST_STATUSES, VERDICTS } from '../workspace/verdicts'

const ICONS: Partial<Record<SubmissionStatus | TestStatus, typeof Info>> = {
  ACCEPTED: CheckCircle2,
  PASSED: CheckCircle2,
  EXECUTED: CheckCircle2,
  WRONG_ANSWER: XCircle,
  FAILED: XCircle,
  RUNTIME_ERROR: XCircle,
  COMPILE_ERROR: XCircle,
  TIME_LIMIT_EXCEEDED: Clock,
  MEMORY_LIMIT_EXCEEDED: XCircle,
  OUTPUT_LIMIT_EXCEEDED: XCircle,
  PENDING: CircleDashed,
  RUNNING: CircleDashed,
}

function Chip({ label, tone, icon: Icon, className }: { label: string; tone: Tone; icon: typeof Info; className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-md px-2 py-0.5 font-mono text-[11px] font-bold tracking-wide whitespace-nowrap uppercase ring-1 ring-inset',
        TONE_CHIP[tone],
        className,
      )}
    >
      <Icon className="size-3.5 shrink-0" aria-hidden />
      {label}
    </span>
  )
}

/** A submission's verdict (icon + label, never color alone). */
export function VerdictBadge({ verdict, className }: { verdict: SubmissionStatus; className?: string }) {
  const { label, tone } = VERDICTS[verdict]
  return <Chip label={label} tone={tone} icon={ICONS[verdict] ?? Info} className={className} />
}

/** One test's status. */
export function TestStatusBadge({ status, className }: { status: TestStatus; className?: string }) {
  const { label, tone } = TEST_STATUSES[status]
  return <Chip label={label} tone={tone} icon={ICONS[status] ?? Info} className={className} />
}
