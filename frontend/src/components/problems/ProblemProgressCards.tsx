import { BarChart3, History, UserRound } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAppTimezone } from '../../hooks/useAppTimezone'
import type { ProblemStats, UserProblemProgress } from '../../types/problem'
import { formatDateTime } from '../../utils/dates'
import { Card } from '../ui/Card'
import { formatMemory, formatPercent, formatRuntime } from '../workspace/verdicts'
import { SolvedStatus } from './SolvedStatus'

function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between gap-3 py-1.5 text-sm">
      <dt className="text-ink-500">{label}</dt>
      <dd className="font-mono text-ink-950 tabular-nums">{value}</dd>
    </div>
  )
}

/** The signed-in student's own progress on this problem (from the server). */
export function YourProgressCard({ progress, slug }: { progress: UserProblemProgress; slug: string }) {
  const timezone = useAppTimezone()
  return (
    <Card className="p-5">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 font-mono text-xs font-semibold tracking-[0.14em] text-brand-500 uppercase">
          <UserRound className="size-3.5" aria-hidden /> Your progress
        </h2>
        <SolvedStatus status={progress.status} showLabel />
      </div>
      <dl className="divide-y divide-ink-200">
        <Row label="Attempts" value={progress.attempts} />
        <Row label="Accepted submissions" value={progress.accepted_submissions} />
        {progress.solved_at && timezone && <Row label="Solved" value={formatDateTime(progress.solved_at, timezone)} />}
        {progress.status === 'SOLVED' && <Row label="Best runtime" value={formatRuntime(progress.best_runtime_ms)} />}
        {progress.status === 'SOLVED' && <Row label="Best memory" value={formatMemory(progress.best_memory_kb)} />}
      </dl>
      {progress.attempts > 0 && (
        <Link to={`/student/submissions?problem=${slug}`} className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-brand-400 hover:underline">
          <History className="size-3.5" aria-hidden /> Your submissions for this problem
        </Link>
      )}
    </Card>
  )
}

/** Aggregates across all students: solved by, attempts, acceptance (submission-based). */
export function ProblemStatsCard({ stats }: { stats: ProblemStats }) {
  return (
    <Card className="p-5">
      <h2 className="mb-3 flex items-center gap-2 font-mono text-xs font-semibold tracking-[0.14em] text-brand-500 uppercase">
        <BarChart3 className="size-3.5" aria-hidden /> Problem statistics
      </h2>
      <dl className="divide-y divide-ink-200">
        <Row label="Solved by" value={`${stats.solved_by.toLocaleString()} student${stats.solved_by === 1 ? '' : 's'}`} />
        <Row label="Attempts" value={stats.attempts.toLocaleString()} />
        <Row label="Acceptance" value={formatPercent(stats.acceptance_rate)} />
      </dl>
      <p className="mt-2 text-[11px] text-ink-400">Acceptance = accepted / judged submissions. Judge failures are not counted.</p>
    </Card>
  )
}
