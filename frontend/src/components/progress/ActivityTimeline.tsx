import { CheckCircle2, XCircle } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { LANGUAGE_CONFIG } from '../../config/languages'
import { useAppTimezone } from '../../hooks/useAppTimezone'
import type { ActivityItem } from '../../types/progress'
import { dayKey, dayLabel, formatTime, timeAgo } from '../../utils/dates'
import { VERDICTS } from '../workspace/verdicts'

function describe(item: ActivityItem): string {
  if (item.type === 'SOLVED') return `Solved ${item.problem.title}`
  if (item.type === 'ACCEPTED') return `Accepted again: ${item.problem.title}`
  return `${VERDICTS[item.verdict].label} on ${item.problem.title}`
}

interface ActivityTimelineProps {
  items: ActivityItem[]
  /** Link each entry to its submission (students only, their own submissions). */
  linkToSubmissions?: boolean
}

/** Real judged submissions, newest first, grouped by calendar day in the app timezone. */
export function ActivityTimeline({ items, linkToSubmissions = false }: ActivityTimelineProps) {
  const timezone = useAppTimezone()
  // Captured once per mount so rendering stays pure.
  const [now] = useState(() => Date.now())
  if (!timezone) return null
  const today = dayKey(new Date(now), timezone)
  const groups: { key: string; items: ActivityItem[] }[] = []
  for (const item of items) {
    const key = dayKey(item.occurred_at, timezone)
    const last = groups[groups.length - 1]
    if (last && last.key === key) last.items.push(item)
    else groups.push({ key, items: [item] })
  }

  return (
    <div className="space-y-4">
      {groups.map((group) => (
        <section key={group.key} aria-label={dayLabel(group.key, today)}>
          <h3 className="mb-2 font-mono text-[10px] tracking-[0.18em] text-ink-400 uppercase">{dayLabel(group.key, today)}</h3>
          <ol className="space-y-1.5">
            {group.items.map((item) => {
              const good = item.type !== 'ATTEMPTED'
              const body = (
                <>
                  {good ? (
                    <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-brand-500" aria-label="Accepted" />
                  ) : (
                    <XCircle className="mt-0.5 size-4 shrink-0 text-danger" aria-label="Not accepted" />
                  )}
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-ink-950">{describe(item)}</span>
                    <span className="block font-mono text-[11px] text-ink-400">
                      {LANGUAGE_CONFIG[item.language].label} · {formatTime(item.occurred_at, timezone)} ·{' '}
                      <time dateTime={item.occurred_at}>{timeAgo(item.occurred_at, now)}</time>
                    </span>
                  </span>
                </>
              )
              return (
                <li key={item.submission_id}>
                  {linkToSubmissions ? (
                    <Link to={`/student/submissions/${item.submission_id}`} className="flex items-start gap-2.5 rounded-lg px-2 py-1.5 transition hover:bg-ink-100/50">
                      {body}
                    </Link>
                  ) : (
                    <div className="flex items-start gap-2.5 px-2 py-1.5">{body}</div>
                  )}
                </li>
              )
            })}
          </ol>
        </section>
      ))}
    </div>
  )
}
