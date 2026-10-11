import { LANGUAGE_CONFIG } from '../../config/languages'
import type { LanguageStat, TopicProgressItem } from '../../types/progress'
import { ProgressBar } from '../ui/ProgressBar'
import { formatPercent } from '../workspace/verdicts'

/** Solved / total per topic (published problems). */
export function TopicProgressList({ topics, limit }: { topics: TopicProgressItem[]; limit?: number }) {
  const shown = topics.filter((t) => t.total_problems > 0).slice(0, limit)
  if (shown.length === 0) return <p className="text-sm text-ink-500">No topics with published problems yet.</p>
  return (
    <ul className="space-y-3.5">
      {shown.map((t) => (
        <li key={t.topic.id}>
          <div className="mb-1.5 flex items-center justify-between gap-3 text-[13px]">
            <span className="truncate font-medium text-ink-800">{t.topic.name}</span>
            <span className="shrink-0 font-mono text-xs text-ink-500 tabular-nums">
              {t.solved_problems} / {t.total_problems}
            </span>
          </div>
          <ProgressBar value={t.percentage} label={`${t.topic.name}: ${t.solved_problems} of ${t.total_problems} solved`} hideLabel showValue={false} size="sm" />
        </li>
      ))}
    </ul>
  )
}

/** Judged submissions and acceptance per language (one series: one color). */
export function LanguageStatsList({ languages }: { languages: LanguageStat[] }) {
  const max = Math.max(1, ...languages.map((l) => l.submissions))
  if (languages.every((l) => l.submissions === 0)) {
    return <p className="text-sm text-ink-500">No submissions yet. Language usage appears after your first submission.</p>
  }
  return (
    <table className="w-full text-left text-sm">
      <caption className="sr-only">Submissions by language</caption>
      <thead className="font-mono text-[10px] tracking-[0.16em] text-ink-400 uppercase">
        <tr>
          <th scope="col" className="pb-2 font-semibold">Language</th>
          <th scope="col" className="pb-2 font-semibold">Submissions</th>
          <th scope="col" className="pb-2 text-right font-semibold">Acceptance</th>
        </tr>
      </thead>
      <tbody>
        {languages.map((l) => (
          <tr key={l.language}>
            <th scope="row" className="py-1.5 pr-3 font-medium whitespace-nowrap text-ink-800">{LANGUAGE_CONFIG[l.language].label}</th>
            <td className="w-full py-1.5 pr-3">
              <div className="flex items-center gap-2">
                <div className="h-2 flex-1 rounded-full bg-ink-100" aria-hidden>
                  <div className="h-2 rounded-full bg-accent" style={{ width: `${(l.submissions / max) * 100}%` }} />
                </div>
                <span className="w-8 shrink-0 text-right font-mono text-xs text-ink-700 tabular-nums">{l.submissions}</span>
              </div>
            </td>
            <td className="py-1.5 text-right font-mono text-xs whitespace-nowrap text-ink-700 tabular-nums">{formatPercent(l.acceptance_rate)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
