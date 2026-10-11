import { Link } from 'react-router-dom'
import { LANGUAGE_CONFIG } from '../../config/languages'
import type { SubmissionSummary } from '../../types/workspace'
import { timeAgo } from '../../utils/dates'
import { VerdictBadge } from '../submissions/VerdictBadge'
import { formatRuntime } from '../workspace/verdicts'

/** The student's latest submissions: problem, verdict, language, runtime, time. */
export function RecentSubmissions({ items }: { items: SubmissionSummary[] }) {
  return (
    <ul className="divide-y divide-ink-200" aria-label="Recent submissions">
      {items.map((s) => (
        <li key={s.id}>
          <Link
            to={`/student/submissions/${s.id}`}
            className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-1 py-2.5 transition hover:bg-ink-100/40 sm:grid-cols-[minmax(0,1fr)_auto_4rem_4.5rem_5.5rem]"
          >
            <span className="truncate text-sm font-semibold text-ink-950">{s.problem.title}</span>
            <VerdictBadge verdict={s.status} />
            <span className="font-mono text-xs text-ink-500">{LANGUAGE_CONFIG[s.language].label}</span>
            <span className="font-mono text-xs text-ink-500 tabular-nums">{formatRuntime(s.runtime_ms)}</span>
            <time className="font-mono text-[11px] text-ink-400 sm:text-right" dateTime={s.submitted_at}>
              {timeAgo(s.submitted_at)}
            </time>
          </Link>
        </li>
      ))}
    </ul>
  )
}
