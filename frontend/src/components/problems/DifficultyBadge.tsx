import type { Difficulty } from '../../types/problem'
import { cn } from '../../utils/format'

// Easy = green, Medium = yellow, Hard = red. Flat tints (no glow) keep it readable.
const STYLES: Record<Difficulty, string> = {
  EASY: 'bg-brand-500/10 text-brand-400 ring-brand-500/30',
  MEDIUM: 'bg-warning/10 text-warning ring-warning/30',
  HARD: 'bg-danger/10 text-danger ring-danger/30',
}

export function DifficultyBadge({ difficulty, className }: { difficulty: Difficulty; className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2 py-0.5 font-mono text-[11px] font-bold tracking-wider whitespace-nowrap uppercase ring-1 ring-inset',
        STYLES[difficulty],
        className,
      )}
    >
      {difficulty}
    </span>
  )
}
