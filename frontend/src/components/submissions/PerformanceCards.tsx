import { MemoryStick, Zap } from 'lucide-react'
import type { ReactNode } from 'react'
import type { SubmissionPerformance, SubmissionStatus } from '../../types/workspace'
import { cn } from '../../utils/format'
import { formatMemory, formatRuntime, formatTimeLimit } from '../workspace/verdicts'

interface PerformanceCardsProps {
  runtimeMs: number | null
  memoryKb: number | null
  timeLimitMs?: number | null
  memoryLimitKb?: number | null
  verdict?: SubmissionStatus
  performance?: SubmissionPerformance | null
  /** Extra cards after runtime and memory (tests passed, submitted time...). */
  extra?: { label: string; value: ReactNode; caption?: ReactNode }[]
  compact?: boolean
}

function Metric({
  icon,
  label,
  value,
  caption,
  warn,
  compact,
}: {
  icon?: ReactNode
  label: string
  value: ReactNode
  caption?: ReactNode
  warn?: boolean
  compact?: boolean
}) {
  return (
    <div
      className={cn(
        'min-w-0 rounded-xl border bg-night/50',
        compact ? 'px-3 py-2.5' : 'px-4 py-3.5',
        warn ? 'border-warning/40' : 'border-ink-200',
      )}
    >
      <dt className="flex items-center gap-1.5 font-mono text-[10px] tracking-[0.18em] text-ink-400 uppercase [&>svg]:size-3.5">
        {icon}
        {label}
      </dt>
      <dd className={cn('mt-1 font-semibold text-ink-950', compact ? 'text-base' : 'text-lg')}>{value}</dd>
      {caption && <dd className="mt-0.5 text-xs text-ink-500">{caption}</dd>}
    </div>
  )
}

/** Runtime and memory as clean cards, with the limit and (if real data allows) a percentile. */
export function PerformanceCards({
  runtimeMs,
  memoryKb,
  timeLimitMs,
  memoryLimitKb,
  verdict,
  performance,
  extra = [],
  compact,
}: PerformanceCardsProps) {
  const tle = verdict === 'TIME_LIMIT_EXCEEDED'
  const mle = verdict === 'MEMORY_LIMIT_EXCEEDED'
  const runtimeCaption = [
    timeLimitMs ? `${tle ? 'Exceeded the' : 'Limit'} ${formatTimeLimit(timeLimitMs)}${tle ? ' limit' : ''}` : null,
    performance?.runtime_percentile != null ? `Faster than ${performance.runtime_percentile}%` : null,
  ]
    .filter(Boolean)
    .join(' · ')
  const memoryCaption = [
    memoryLimitKb ? `${mle ? 'Exceeded the' : 'Limit'} ${formatMemory(memoryLimitKb)}${mle ? ' limit' : ''}` : null,
    performance?.memory_percentile != null ? `Less memory than ${performance.memory_percentile}%` : null,
  ]
    .filter(Boolean)
    .join(' · ')

  return (
    <dl className={cn('grid gap-3', extra.length >= 2 ? 'grid-cols-2 lg:grid-cols-4' : 'grid-cols-2')}>
      <Metric icon={<Zap aria-hidden />} label="Runtime" value={formatRuntime(runtimeMs)} caption={runtimeCaption || undefined} warn={tle} compact={compact} />
      <Metric icon={<MemoryStick aria-hidden />} label="Memory" value={formatMemory(memoryKb)} caption={memoryCaption || undefined} warn={mle} compact={compact} />
      {extra.map((item) => (
        <Metric key={item.label} label={item.label} value={item.value} caption={item.caption} compact={compact} />
      ))}
    </dl>
  )
}
