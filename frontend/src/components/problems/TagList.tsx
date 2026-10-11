import type { Tag } from '../../types/problem'
import { cn } from '../../utils/format'

/** Small technical badge: dark fill, subtle green border, monospace uppercase. */
export function TagBadge({ name, className }: { name: string; className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md border border-brand-500/20 bg-night px-1.5 py-0.5 font-mono text-[10px] font-semibold tracking-wider whitespace-nowrap text-ink-500 uppercase',
        className,
      )}
    >
      {name}
    </span>
  )
}

interface TagListProps {
  tags: Tag[]
  /** Show at most this many tags, then "+N". */
  max?: number
  className?: string
}

export function TagList({ tags, max, className }: TagListProps) {
  if (tags.length === 0) return null
  const shown = max ? tags.slice(0, max) : tags
  const hidden = tags.length - shown.length
  return (
    <ul className={cn('flex flex-wrap gap-1.5', className)} aria-label="Tags">
      {shown.map((tag) => (
        <li key={tag.id}>
          <TagBadge name={tag.name} />
        </li>
      ))}
      {hidden > 0 && (
        <li>
          <TagBadge name={`+${hidden}`} className="text-ink-400" />
        </li>
      )}
    </ul>
  )
}
