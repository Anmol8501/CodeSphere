import type { DifficultyProgress } from '../../types/progress'
import { ProgressBar } from '../ui/ProgressBar'

const ROWS = [
  { key: 'easy', label: 'Easy', dot: 'bg-accent' },
  { key: 'medium', label: 'Medium', dot: 'bg-warning' },
  { key: 'hard', label: 'Hard', dot: 'bg-danger' },
] as const

/** Solved / total per difficulty, from published problems. */
export function DifficultyProgressList({ difficulty }: { difficulty: DifficultyProgress }) {
  return (
    <ul className="space-y-4">
      {ROWS.map(({ key, label, dot }) => {
        const row = difficulty[key]
        return (
          <li key={key}>
            <div className="mb-1.5 flex items-center justify-between gap-3 text-[13px]">
              <span className="flex items-center gap-2 font-medium text-ink-800">
                <span className={`size-2 rounded-full ${dot}`} aria-hidden />
                {label}
              </span>
              <span className="font-mono text-xs text-ink-500 tabular-nums">
                <strong className="font-semibold text-ink-950">{row.solved}</strong> / {row.total}
              </span>
            </div>
            <ProgressBar value={row.percentage} label={`${label}: ${row.solved} of ${row.total} solved`} hideLabel showValue={false} size="sm" />
          </li>
        )
      })}
    </ul>
  )
}
