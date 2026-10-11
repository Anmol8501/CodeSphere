import { ArrowRight, BookOpen, RotateCcw, Rocket } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Recommendation, RecommendationReason } from '../../types/progress'
import { DifficultyBadge } from '../problems/DifficultyBadge'

const REASON: Record<RecommendationReason, { label: string; Icon: typeof Rocket }> = {
  RESUME: { label: 'Pick up where you left off', Icon: RotateCcw },
  CONTINUE_TOPIC: { label: 'Continue topic', Icon: BookOpen },
  START_TOPIC: { label: 'Start a new topic', Icon: Rocket },
}

/** Rule-based next problems from the student's real progress (no AI, no randomness). */
export function RecommendationList({ items }: { items: Recommendation[] }) {
  return (
    <ul className="space-y-2.5">
      {items.map((item) => {
        const { label, Icon } = REASON[item.reason]
        return (
          <li key={item.problem.id}>
            <Link
              to={`/student/problems/${item.problem.slug}/solve`}
              className="group flex items-center gap-3 rounded-xl border border-ink-200 bg-night/40 p-3 transition hover:border-brand-500/40"
            >
              <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand-500/10 text-brand-400 ring-1 ring-brand-500/25">
                <Icon className="size-4" aria-hidden />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block font-mono text-[10px] tracking-[0.16em] text-ink-400 uppercase">
                  {label} · {item.problem.topic.name}
                </span>
                <span className="mt-0.5 flex flex-wrap items-center gap-2">
                  <span className="truncate text-sm font-semibold text-ink-950 group-hover:text-brand-400">{item.problem.title}</span>
                  <DifficultyBadge difficulty={item.problem.difficulty} />
                </span>
                <span className="mt-0.5 block text-xs text-ink-500">{item.message}</span>
              </span>
              <ArrowRight className="size-4 shrink-0 text-ink-400 transition group-hover:translate-x-0.5 group-hover:text-brand-400" aria-hidden />
            </Link>
          </li>
        )
      })}
    </ul>
  )
}
