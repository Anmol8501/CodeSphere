import { History } from 'lucide-react'
import { Link } from 'react-router-dom'
import { LANGUAGE_CONFIG } from '../../../config/languages'
import type { SubmissionSummary } from '../../../types/workspace'
import { VerdictBadge } from '../../submissions/VerdictBadge'
import { formatMemory, formatRuntime } from '../verdicts'

interface ProblemSubmissionsProps {
  submissions: SubmissionSummary[] | null
  loading: boolean
  error: string | null
  problemSlug: string
}

const timeFormat = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })

/** This problem's recent submissions (the student's own only). */
export function ProblemSubmissions({ submissions, loading, error, problemSlug }: ProblemSubmissionsProps) {
  if (loading && !submissions) return <p className="font-mono text-xs text-ink-400">Loading submissions...</p>
  if (error) return <p className="text-sm text-danger">Unable to load submissions. {error}</p>
  if (!submissions || submissions.length === 0) {
    return (
      <div className="flex min-h-24 flex-col items-center justify-center gap-1.5 text-center">
        <History className="size-5 text-ink-400" aria-hidden />
        <p className="text-sm text-ink-500">No submissions for this problem yet.</p>
      </div>
    )
  }
  return (
    <div>
      <ul className="divide-y divide-ink-200 rounded-xl ring-1 ring-ink-200" aria-label="Your submissions for this problem">
        {submissions.map((s) => (
          <li key={s.id}>
            <Link
              to={`/student/submissions/${s.id}`}
              className="flex flex-wrap items-center gap-x-3 gap-y-1 px-3 py-2 text-xs transition hover:bg-ink-100/50"
            >
              <VerdictBadge verdict={s.status} />
              <span className="font-mono text-ink-500">{LANGUAGE_CONFIG[s.language].label}</span>
              <span className="font-mono text-ink-500">
                {s.passed_tests}/{s.total_tests}
              </span>
              <span className="font-mono text-ink-500">{formatRuntime(s.runtime_ms)}</span>
              <span className="font-mono text-ink-500">{formatMemory(s.memory_kb)}</span>
              <span className="ml-auto font-mono text-ink-400">{timeFormat.format(new Date(s.submitted_at))}</span>
            </Link>
          </li>
        ))}
      </ul>
      <Link to={`/student/submissions?problem=${problemSlug}`} className="mt-2 inline-block text-xs font-semibold text-brand-400 hover:underline">
        View all in submission history
      </Link>
    </div>
  )
}
