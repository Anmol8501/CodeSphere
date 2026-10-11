import { ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { ProblemListItem } from '../../types/problem'
import { formatPercent } from '../workspace/verdicts'
import { DifficultyBadge } from './DifficultyBadge'
import { SolvedStatus } from './SolvedStatus'
import { TagList } from './TagList'

interface ProblemListProps {
  problems: ProblemListItem[]
  /** Where problem links point, e.g. "/student/problems". */
  basePath: string
  /** Hide the solved column (staff have no personal progress). */
  showStatus?: boolean
  /** Hide the topic column (e.g. on a topic page). */
  showTopic?: boolean
  caption: string
}

/** Desktop: table. Mobile: cards. */
export function ProblemList({ problems, basePath, showStatus = true, showTopic = true, caption }: ProblemListProps) {
  return (
    <>
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full text-left text-sm">
          <caption className="sr-only">{caption}</caption>
          <thead className="border-b border-ink-200 bg-night/60 font-mono text-[11px] tracking-[0.14em] text-ink-400 uppercase">
            <tr>
              {showStatus && (
                <th scope="col" className="w-16 px-4 py-3 font-semibold">
                  Status
                </th>
              )}
              <th scope="col" className="px-4 py-3 font-semibold">Title</th>
              <th scope="col" className="px-4 py-3 font-semibold">Difficulty</th>
              {showTopic && <th scope="col" className="px-4 py-3 font-semibold">Topic</th>}
              <th scope="col" className="px-4 py-3 font-semibold">Tags</th>
              <th scope="col" className="px-4 py-3 text-right font-semibold" title="Accepted / judged submissions, all students">
                Acceptance
              </th>
              <th scope="col" className="px-4 py-3 text-right font-semibold" title="Students with an accepted submission">
                Solved by
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-200">
            {problems.map((problem) => (
              <tr key={problem.id} className="group transition hover:bg-ink-100/50">
                {showStatus && (
                  <td className="px-4 py-3">
                    <SolvedStatus status={problem.user_status} />
                  </td>
                )}
                <td className="px-4 py-3">
                  <Link
                    to={`${basePath}/${problem.slug}`}
                    className="font-semibold text-ink-950 transition group-hover:text-brand-400 hover:underline"
                  >
                    {problem.title}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <DifficultyBadge difficulty={problem.difficulty} />
                </td>
                {showTopic && <td className="px-4 py-3 whitespace-nowrap text-ink-500">{problem.topic.name}</td>}
                <td className="px-4 py-3">
                  <TagList tags={problem.tags} max={3} />
                </td>
                <td className="px-4 py-3 text-right font-mono text-xs text-ink-500 tabular-nums">
                  {formatPercent(problem.stats.acceptance_rate)}
                </td>
                <td className="px-4 py-3 text-right font-mono text-xs text-ink-500 tabular-nums">
                  {problem.stats.solved_by.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ul className="divide-y divide-ink-200 md:hidden" aria-label={caption}>
        {problems.map((problem) => (
          <li key={problem.id}>
            <Link
              to={`${basePath}/${problem.slug}`}
              className="flex items-start gap-3 p-4 transition hover:bg-ink-100/50"
            >
              {showStatus && (
                <span className="pt-0.5">
                  <SolvedStatus status={problem.user_status} />
                </span>
              )}
              <span className="min-w-0 flex-1 space-y-2">
                <span className="block font-semibold text-ink-950">{problem.title}</span>
                <span className="flex flex-wrap items-center gap-2">
                  <DifficultyBadge difficulty={problem.difficulty} />
                  {showTopic && <span className="text-xs text-ink-500">{problem.topic.name}</span>}
                </span>
                <TagList tags={problem.tags} max={3} />
                <span className="block font-mono text-[11px] text-ink-400">
                  Solved by {problem.stats.solved_by.toLocaleString()} · Acceptance {formatPercent(problem.stats.acceptance_rate)}
                </span>
              </span>
              <ChevronRight className="mt-0.5 size-4 shrink-0 text-ink-400" aria-hidden />
            </Link>
          </li>
        ))}
      </ul>
    </>
  )
}
